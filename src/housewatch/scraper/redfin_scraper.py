# src/housewatch/scraper/redfin_scraper.py

import requests
import re
import json
import logging
import time
from typing import List
from bs4 import BeautifulSoup

from housewatch.models.house import House
from housewatch.storage.json_storage import HouseStorage

logger = logging.getLogger(__name__)


SYSTEM_PARAMS = {
    "al": 1, # Acess/Anonymouse level -- default (no change needed)
    "v": 8, # Redfin current API stable version (may be upgraded to 9, 10, ...)
}

# Map: { "YAML_KEY": "REDFIN_API_KEY" }
PROPERTY_MAP = {
    "status": "status",
    "uipt": "uipt",
    "min_price": "min_price",
    "max_price": "max_price",
    "min_year_built": "min_year_built",
    "min_beds": "min_num_beds",
    "min_baths": "min_num_baths",
}

def _build_property_params(property_cfg: dict) -> dict:
    params = {}
    
    for key, value in property_cfg.items():
        if key not in PROPERTY_MAP:
            continue

        if value is None:
            continue

        redfin_key = PROPERTY_MAP[key]
        params[redfin_key] = value
    
    return params

def _build_bbox(loc):
    """Helper to calculate the bounding box"""
    d_lat = loc.get("lat_delta", 0.01)
    d_lon = loc.get("long_delta", 0.01)
    return {
        "minLat": loc["latitude"] - d_lat,
        "maxLat": loc["latitude"] + d_lat,
        "minLng": loc["longitude"] - d_lon,
        "maxLng": loc["longitude"] + d_lon,
    }

def build_params(app_cfg, criteria_cfg, region_id_override=None):
    params = {
        **SYSTEM_PARAMS,
        "num_homes": app_cfg["redfin"]["num_homes"], # maximum/limit number of results returned in a single request
    }
    
    active_modules = criteria_cfg.get("active_modules", [])

    # Property Logic
    if "property" in active_modules and "property" in criteria_cfg:
        params.update(_build_property_params(criteria_cfg["property"]))
    
    # Location Logic
    if "location" in active_modules and "location" in criteria_cfg:
        loc = criteria_cfg["location"]
        # Handle region search
        region_id_to_use = region_id_override or loc.get("region_id")
        if region_id_to_use:
            params["region_id"] = region_id_to_use
            params["region_type"] = loc["region_type"]
        elif loc.get("region_ids"):
            params["region_id"] = loc["region_ids"][0]
            params["region_type"] = loc["region_type"]
        # Handle coordinate search
        elif loc.get("latitude"):
            params.update(_build_bbox)
    
    # Schools Logic (Internal API specific)
    if "schools" in active_modules and "schools" in criteria_cfg:
        # Note: Redfin often handles school ratings as a separate
        #params["has_excellent_schools"] = True
        pass

    # Clean up None values
    return {k: v for k, v in params.items() if v is not None}



class RedfinScraper:

    BASE_URL = "https://www.redfin.com/stingray/api/gis"

    def __init__(self, config, storage: HouseStorage):
        # API Core Parameters
        self.config = config
        self.storage = storage
        self.timeout = config.app.get("timeout", 10)

        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json",
            #"Referer": "https://www.redfin.com/"
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def fetch(self) -> List[House]:
        """
        Fetch listings and then fetch details for each to get schools/HOA.
        """
        logger.info("Fetching search results from Redfin API")

        raw_data = self._request_search()
        basic_houses = self._parse_search(raw_data)

        logger.info(f"Redfin fetch houses: {len(basic_houses)}")
        
        new_houses = [h for h in basic_houses if self.storage.is_new(h)]

        full_houses = []
        count = 0
        for house in new_houses:
            count += 1
            # Visit the detail page to get Schools and HOA
            logger.info(f"Fetching deep details for ({count}/{len(new_houses)}): "
                        f"{house.address}, {house.city}, {house.state} {house.zip_code}")

            # Here only for schools
            schools = self._fetch_details(house.url)
            
            # Apply schools filtration
            if not self._schools_match_criteria(schools):
                continue

            house.schools = schools

            full_houses.append(house)
            time.sleep(1) # Avoid gettinb blocked

        # Mark all new_houses as "seen"

        self.storage.make_multiple_as_seen(new_houses)
        self.storage.save_seen()


        return full_houses
    

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _request_search(self) -> dict:
        """
        Perform HTTP request to Redfin API.
        """
        loc = self.config.criteria.get("location", {})
        region_ids = loc.get("region_ids", [])

        if not region_ids:
            single_region_id = loc.get("region_id")
            if single_region_id:
                region_ids = [single_region_id]
            elif not loc.get("latitude"):
                raise ValueError("No region_ids, region_id, or coordinates provided in criteria")
        
        all_homes = []
        
        for region_id in region_ids:
            params = build_params(self.config.app, self.config.criteria, region_id_override=region_id)
            try:
                resp = requests.get(
                    self.BASE_URL,
                    headers=self.headers,
                    params=params,
                    timeout=self.timeout
                )
                #print("request url:\n", resp.url)
                content = resp.text.replace("{}&&", "", 1) if resp.text.startswith("{}&&") else resp.text
                data = json.loads(content)
                homes = data.get("payload", {}).get("homes", [])
                all_homes.extend(homes)
            except requests.RequestException as e:
                logger.exception(f"Redfin request failed for region_id={region_id}")
                continue  # move to next region_id
        
        # Remove duplications
        seen = {}
        for h in all_homes:
            key = h.get("propertyId") or h.get("listingId")
            if key:
                seen[key] = h
        
        return {"payload": {"homes": list(seen.values())}}

    
    def _parse_search(self, data: dict) -> List[House]:
        """
        Convert Redfin JSON payload into House models.
        """
        payload = data.get("payload", {})
        homes = payload.get("homes", [])
        logger.info(f"Redfin returned {len(homes)} homes (before applying filtration)")

        results: List[House] = []


        for h in homes:
            #print("Sample Home Data:") #Check details
            #print(json.dumps(h, indent=4, ensure_ascii=False))
            #break
            """Homes from request does not apply any filtration. The following will do."""

            state = h.get("state", "")
            if state !=  self.config.criteria["location"].get("state", "IL"):
                continue

            if h.get('propertyType') and h.get('propertyType') != 6: # 6 for API House
                 continue
            
            property_type = self.config.criteria["property"].get("type", "Single Family")

            if "/unit-" in h.get('url', ""):
                continue
            
            price = h.get("price", {}).get("value", 0)
            if (price < self.config.criteria["property"].get("min_price", 0) or
                price > self.config.criteria["property"].get("max_price", 1500000)):
                continue
            
            year_built = h.get("yearBuilt", {}).get("value", 0)
            if year_built < self.config.criteria["property"].get("min_year_built", 1980):
                continue

            hoa = h.get("hoa", {}).get("value", 0.)
            if (hoa > self.config.criteria["property"].get("hoa_fee", 0.)):
                continue
            

            sqft = h.get("sqFt", {}).get("value", 0)
            lot_size = h.get("lotSize", {}).get("value", 0)


            #print("\nhouse full info:\n", h)
            
            # No school information is available at this stage            
            try:
                house = House(
                    listing_id=str(h.get("listingId", "")),
                    property_type=property_type,
                    price=price,
                    year_built=year_built,
                    hoa_fee=hoa,
                    beds=h.get("beds"),
                    baths=h.get("baths"),
                    sqft=sqft,
                    lot_size=lot_size,
                    address=h.get("streetLine", {}).get("value", "Address Undisclosed"),
                    city=h.get("city"),
                    state=state,
                    zip_code=h.get("zip"),
                    url=f"https://www.redfin.com{h.get('url')}"
                )
                # Check if house is new
                if self.storage.is_new(house):
                    results.append(house)
                else:
                    continue
                
            except Exception:
                logger.exception(
                    "Failed to parse house entry: %s",
                    h.get("propertyId"),
                )

        return results


    def _fetch_details(self, url: str) -> dict:
        """Visit property page to find more details, here only for schools"""
        # Extract Schools
        schools = {
            "elementary": [],
            "middle": [],
            "high": []
        }

        try:
            res = requests.get(url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(res.text, "lxml")

            for item in soup.select(".schools-table .ListItem"):
                name = item.select_one(".ListItem__heading")
                #rating = item.select_one(".rating-num")
                desc = item.select_one(".ListItem__description")

                if not name or not desc:
                    continue

                name = name.get_text(strip=True) 
                desc = desc.get_text(strip=True)

                # Extract grade range: K-5, 6-8, 9-12
                m = re.search(r"(K|\d+)\s*-\s*(\d+)", desc)
                if not m:
                    continue

                start, end = m.group(1), int(m.group(2))

                # Elementary
                if start == "K" and end <= 5:
                    schools["elementary"].append(name)

                # Middle
                elif start.isdigit() and 6 <= int(start) <= 8:
                    schools["middle"].append(name)

                # High
                elif end >= 9:
                    schools["high"].append(name)

        except Exception as e:
            logger.warning(f"Could not fetch details for {url}: {e}")
            
        return schools


    def _schools_match_criteria(self, schools: dict[str, List[str]]) -> bool:
        """Check if house schools match criteria"""

        for level in ("elementary", "middle", "high"):
            house_schools_set = set(schools.get(level, []))
            criteria_schools_set = set(self.config.criteria["schools"].get(level, []))

            if not house_schools_set & criteria_schools_set:
                return False
        return True
