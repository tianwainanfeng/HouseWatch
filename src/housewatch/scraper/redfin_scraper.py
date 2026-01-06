# src/housewatch/scraper/redfin_scraper.py

import requests
import json
import logging
import time
from typing import List
from bs4 import BeautifulSoup

from housewatch.models.house import House

logger = logging.getLogger(__name__)


class RedfinScraper:

    BASE_URL = "https://www.redfin.com/stingray/api/gis"

    def __init__(self, config):
        # API Core Parameters
        self.market = config.get("market", "chicago")
        self.region_id = int(config.get("region_id", "29501"))
        self.region_type =int(config.get("region_type", 6))
        self.state = config.get("state", "IL")
        self.latitude = config.get("latitude", 41.7508)
        self.longitude = config.get("longitude", -88.1535)
        self.lat_delta = config.get("lat_delta", 0.15)
        self.long_delta = config.get("long_delta", 0.18)

        self.min_price = config.get("min_price", 200000)
        self.max_price = config.get("max_price", 800000)
        self.min_beds = config.get("min_beds", 3)
        self.min_baths = int(config.get("min_baths", 2))
        self.timeout = config.get("timeout", 15)

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

        full_houses = []
        count = 0
        for house in basic_houses:
            count += 1
            if house.state != self.state:
                continue

            # Visit the detail page to get Schools and HOA
            logger.info(f"Fetching deep details for ({count}/{len(basic_houses)}): {house.address}")
            details = self._fetch_details(house.url)

            if details.get("state") and details["state"] != self.state:
                continue

            house.schools = details.get("schools", [])
            house.hoa_fee = details.get("hoa_fee", 0)
            house.year_built = details.get("year_built", house.year_built)

            full_houses.append(house)
            time.sleep(1) # Avoid gettinb blocked

        return full_houses

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _request_search(self) -> dict:
        """
        Perform HTTP request to Redfin API.
        """
        params = {
            "al": 1,
            "v": 8,
            "num_homes": 350,
            "status": 1,
            "uipt": "1", # Single-Family only 
        }
        
        if self.region_id:
            params["region_id"] = self.region_id
            params["region_type"] = self.region_type
        elif hasattr(self, 'latitude') and self.latitude:
            params.update({
                "minLat": self.latitude - self.lat_delta,
                "maxLat": self.latitude + self.lat_delta,
                "minLng": self.longitude - self.long_delta,
                "maxLng": self.longitude + self.long_delta,
        })
        elif self.market:
            params["market"] = self.market

        """
        params = {
            "al": 1,                     # all listings
            "v": 8, # API version
            "num_homes": 350, # max results per request
            "ord": "redfin-recommended-asc",
            
            #"market": self.market,
            "region_id": self.region_id,
            "region_type": self.region_type,
            "status": 1,                 # for sale + coming soon, 3 for active sale
            
            "uipt": "1",       # property types: 1 for Single-Family

            #"minLat": self.latitude - self.lat_delta,
            #"maxLat": self.latitude + self.lat_delta,
            #"minLng": self.longitude - self.long_delta,
            #"maxLng": self.longitude + self.long_delta,
        }
        """
      
        # Optional filters (API-level, not business filtering)
        if self.min_price:
            params["min_price"] = self.min_price
        if self.max_price:
            params["max_price"] = self.max_price
        if self.min_beds:
            params["min_num_beds"] = self.min_beds
        if self.min_baths:
            params["min_mun_baths"] = self.min_baths

   

        try:
            resp = requests.get(
                self.BASE_URL,
                headers=self.headers,
                params=params,
                timeout=self.timeout
            )
            content = resp.text.replace("{}&&", "", 1) if resp.text.startswith("{}&&") else resp.text
            return json.loads(content)

        except requests.RequestException as e:
            logger.exception("Redfin request failed")
            raise RuntimeError("Failed to fetch data from Redfin") from e

    
    def _parse_search(self, data: dict) -> List[House]:
        """
        Convert Redfin JSON payload into House models.
        """
        payload = data.get("payload", {})
        homes = payload.get("homes", [])
        
        logger.info(f"Redfin returned {len(homes)} homes")

        results: List[House] = []

        for h in homes:
            if h.get('propertyType') and h.get('propertyType') != 6: # 6 for API House
                 continue
            if "/unit-" in h.get('url', ""):
                continue

            try:
                house = House(
                    listing_id=h.get("listingId"),
                    price=h.get("price"),
                    beds=h.get("beds"),
                    baths=h.get("baths"),
                    sqft=h.get("sqFt"),
                    address=h.get("streetLine"),
                    city=h.get("city"),
                    state=h.get("state"),
                    zip_code=h.get("zip"),
                    url=f"https://www.redfin.com{h.get('url')}"
                )
                results.append(house)

            except Exception:
                logger.exception(
                    "Failed to parse house entry: %s",
                    h.get("propertyId"),
                )

        return results


    def _fetch_details(self, url: str) -> dict:
        """Visit property page to find Schools and HOA fee"""
        try:
            res = requests.get(url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(res.text, "lxml")

            state = None
            canonical = soup.find('link', rel='canonical')
            if canonical and '/IL/' in canonical.get("href", ""):
                state = "IL"

            # Extract Schools
            schools = []
            school_section = soup.find_all("div", class_="school-name")
            for s in school_section:
                schools.append(s.get_text(strip=True))
            

            # Extract HOA fee
            hoa_fee = 0.0
            stats = soup.find_all("span", class_="header")
            for stat in stats:
                if "HOA" in stat.get_text():
                    val = stat.find_next_sibling("span").get_text()
                    hoa_fee = float(''.join(filter(str.isdigit, val)) or 0.0)
            
            return {
                "schools": schools,
                "hoa_fee": hoa_fee,
                "state": state
            }
        except Exception as e:
            logger.warning(f"Could not fetch details for {url}: {e}")
            return {"schools": [], "hoa_fee": 0.0}
