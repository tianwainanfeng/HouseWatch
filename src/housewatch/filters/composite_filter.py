# src/housewatch/filters/composite_filter.py

from typing import List
from ..models.house import House
from .school_filter import filter_by_schools
from .property_filter import filter_by_property_criteria


def filter_houses(houses: List[House], config: dict) -> List[House]:
    """
    Apply all filters and return only matching houses.
    Now uses the list-based schools config.
    """
    filtered = []

    criteria = config.get("criteria", {})
    required_schools = criteria.get("schools", [])

    for house in houses:
        if not filter_by_property_criteria(house, config):
            continue
        
        if not filter_by_schools(house, required_schools):
            continue
        
        filtered.append(house)
    
    return filtered