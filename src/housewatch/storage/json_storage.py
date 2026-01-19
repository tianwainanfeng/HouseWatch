# src/housewatch/storage/json_storage.py

import json
from pathlib import Path
from typing import List
from datetime import datetime
from housewatch.models.house import House


class HouseStorage:
    """Simple JSON-based storage for tracking seen houses"""

    def __init__(self, seen_path: str = "data/seen_houses.json",
                 matched_path: str = "data/matched_houses.json"):
        self.seen_path = Path(seen_path)
        self.matched_path = Path(matched_path)
        self.seen_path.parent.mkdir(parents=True, exist_ok=True)
        self.seen_houses: dict[str, str] = {} # listing_id -> address
        self.load_seen()
    

    def load_seen(self) -> None:
        """Load previously seen house IDs from file"""
        if self.seen_path.exists():
            try:
                with open(self.seen_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.seen_houses = data.get("seen_houses", {})
            except (json.JSONDecodeError, IOError):
                self.seen_houses = {}
    

    def save_seen(self) -> None:
        """Save seen houses to file"""
        data = {
            "seen_houses": self.seen_houses,
            "last_updated": datetime.now().isoformat()
        }
        with open(self.seen_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    

    def is_new(self, house: House) -> bool:
        """Check if house hasn't seen before"""
        return house.listing_id not in self.seen_houses
    

    def mark_as_seen(self, house: House) -> None:
        """Mark a house as seen and save"""
        self.seen_houses[house.listing_id] = f"{house.address}, {house.city}, {house.state} {house.zip_code}"
        self.save_seen()
    

    def make_multiple_as_seen(self, houses: List[House]) -> None:
        """Mark multiple houses as seen at once"""
        for house in houses:
            self.seen_houses[house.listing_id] = f"{house.address}, {house.city}, {house.state} {house.zip_code}"
        self.save_seen()
    

    def save_matched(self, houses: List[House]) -> None:
        if not houses:
            return
        
        existing_matches = []
        if self.matched_path.exists():
            try:
                with open(self.matched_path, 'r', encoding='utf-8') as f:
                    existing_matches = json.load(f)
            except (json.JSONDecodeError, IOError):
                existing_matches = []
        
        new_entries = []
        for house in houses:
            house_dict = {
                "listing_id": house.listing_id,
                "address": f"{house.address}, {house.city}, {house.state} {house.zip_code}",
                "price": house.price,
                "year_built": house.year_built,
                "schools": house.schools,
                "url": house.url,
                "detected_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            new_entries.append(house_dict)
        
        existing_matches.extend(new_entries)

        with open(self.matched_path, 'w', encoding='utf-8') as f:
            json.dump(existing_matches, f, indent=2, ensure_ascii=False)
        print(f"Write {len(new_entries)} new houses into {self.matched_path}" )
