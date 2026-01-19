# src/housewatch/filters/school_filter.py

from typing import List, Dict, Any
from ..models.house import House
import re


def filter_by_schools(house: House, school_config: Dict[str, Any]) -> bool:
    """
    Check if house is in the required school district
    Returns True if ALL required schools are in house.schools
    """

    if not house.schools:
        return False
    
    house_school_lower = {
        level: [s.lower().strip() for s in schools]
        for level, schools in house.schools.items()
    }
    
    # Track matches for each tier
    elementary_matched = False
    middle_matched = False
    high_matched = False

    # Extract school lists from config
    elementary_schools = school_config.get("elementary", [])
    middle_schools = school_config.get("middle", [])
    hihg_schools = school_config.get("high", [])

    # Check elemenatry schools
    if not elementary_schools:
        elementary_matched = True
    else:
        elementary_matched = any(
            re.search(_create_flexible_pattern(elem), school, re.IGNORECASE)
            for elem in elementary_schools
            for school in house_school_lower["elementary"]
        )
    
    # Check middle schools
    if not middle_schools:
        middle_matched = True
    else:
        middle_matched = any(
            re.search(_create_flexible_pattern(mid), school, re.IGNORECASE)
            for mid in middle_schools
            for school in house_school_lower["middle"]
        )
    
    # Check high schools
    if not hihg_schools:
        high_matched = True
    else:
        high_matched = any(
            re.search(_create_flexible_pattern(high), school, re.IGNORECASE)
            for high in hihg_schools
            for school in house_school_lower["high"]
        )
    
    return elementary_matched and middle_matched and high_matched


def _create_flexible_pattern(school_name: str) -> str:
    """
    Create a flexible regex pattern from school name.
    Handles abbreviations, word order variations, etc.
    """
    name = school_name.lower()

    words = re.findall(r'\b\w+\b', name)

    pattern_parts = []
    for word in words:
        if word not in ["school", "high", "elementary", "middle", "junior", "senior"]:
            pattern_parts.append(f"(?=.*\\b{word}\\b)")
    
    if pattern_parts:
        # Join with lookaheads to allow any order
        pattern = f"{''.join(pattern_parts)}.*"
    else:
        pattern = re.escape(name)
    
    return pattern
        
            
def filter_by_schools_strict(house: House, school_config: Dict[str, Any]) -> bool:
    """
    Strict matching: requires exact school names (case-insensitive)
    Check if house schools contain the full required school name
    """
    if not house.schools:
        return False
    
    house_schools_lower = [s.lower().strip() for s in house.schools]

    elementary_ok = False
    middle_ok = False
    high_ok = False

    # Check elementary
    required_elementary_schools = [s.lower() for s in school_config.get("elementary", [])]
    elementary_ok = any(
        any(required_elementary in school for school in house_schools_lower)
        for required_elementary in required_elementary_schools
    )

    # Check middle (only one required)
    required_middle_schools = [s.lower() for s in school_config.get("middle", [])]
    middle_ok = any(
        any(required_middle in school for school in house_schools_lower)
        for required_middle in required_middle_schools
    )

    # Check high (multiple options, need at least one)
    required_high_schools = [s.lower() for s in school_config.get("high", [])]
    high_ok = any(
        any(required_high in school for school in house_schools_lower)
        for required_high in required_high_schools 
    )

    return elementary_ok and middle_ok and high_ok


def filter_by_schools_exact(house: House, school_config: Dict[str, Any]) -> bool:
    """
    Exact matching: house schools must exactly match config schools.
    """
    if not house.schools:
        return False
    
    house_school_lower = [s.lower().strip() for s in house.schools]

    all_required = []
    for tier in ["elementary", "middle", "high"]:
        all_required.append([s.lwoer().strip() for s in school_config.get(tier, [])])
    
    for required in all_required:
        if required not in house_school_lower:
            return False
    
    return True


def get_school_tiers(house: House, school_config: Dict[str, Any]) -> Dict[str, List[str]]:
    """
    Identify which schools belong to which tier.
    """
    result = {
        "elementary": [],
        "middle": [],
        "high": [],
        "other": []
    }

    if not house.schools:
        return result
    
    for school in house.schools:
        school_lower = school.lower()
        matched = False

        # Check elementary
        for elem_pattern in school_config.get("elementary", []):
            if _create_flexible_pattern(elem_pattern) in school_lower:
                result["elementary"].append(school)
                matched = True
                break
        
        if matched:
            continue

        # Check middle
        for middle_pattern in school_config.get("middle", []):
            if _create_flexible_pattern(middle_pattern) in school_lower:
                result["middle"].append(school)
                matched = True
                break
        
        if matched:
            continue
        
        # Check high
        for high_pattern in school_config.get("high", []):
            if _create_flexible_pattern(high_pattern) in school_lower:
                result["high"].append(school)
                matched = True
                break
        
        if not matched:
            result["other"].append(school)
        
    return result