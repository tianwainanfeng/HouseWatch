# src/housewatch/filters/property_filter.py

from ..models.house import House


def filter_by_property_criteria(house: House, config: dict) -> bool:
    """
    Apply property-related filters.
    """
    criteria = config.get("criteria", {})

    # Property type
    required_type = criteria.get("property_type", "Single-Family")
    if house.property_type.lower() != required_type.lower():
        return False
    
    # Year built
    min_year = criteria.get("min_year_built", 1980)
    if house.year_built and house.year_built < min_year:
        return False
    
    # HOA fee
    max_hoa = criteria.get("hoa_fee", 0)
    if house.hoa_fee and house.hoa_fee > max_hoa:
        return False
    
    # Price
    max_price = criteria.get("max_price", 800000)
    if house.price >= max_price:
        return False
    
    return True