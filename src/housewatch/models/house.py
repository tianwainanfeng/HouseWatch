# src/housewatch/modesl/house.py

from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime


@dataclass
class House:
    """Represents a house listing with all relevant details"""
    listing_id: str
    address: str
    city: str
    state: str
    zip_code: str
    price: int
    year_built: Optional[int] = None
    property_type: str = ""
    hoa_fee: float = 0.0
    beds: Optional[int] = None
    baths: Optional[float] = None
    sqft: Optional[int] = None
    lot_size: Optional[float] = None
    url: str = ""
    schools: List[str] = None
    listed_date: Optional[datetime] = None
    last_update: Optional[datetime] = None


    def __post_init__(self):
        """
        a special function used to perform logic after the object has been 
        initialized. When using the @dataclass decorator, Python generates a 
        standard __init__, and after that it automatically looks for and calls
        __post_init__.
        """
        if self.schools is None:
            self.schools = []
    

    @property
    def formatted_price(self) -> str:
        """Return price as formatted string: $XXX,XXX"""
        return f"${self.price:,}"
    

    @property
    def full_address(self) -> str:
        """Return complete address"""
        return f"{self.address}, {self.city}, {self.state} {self.zip_code}"
    

    def to_dict(self) -> dict:
        """Convert to dictionary for storage"""
        return {
            "listing_id": self.listing_id,
            "address": self.address,
            "price": self.price,
            "hoa": self.hoa_fee,
            "year_built": self.year_built,
        }
