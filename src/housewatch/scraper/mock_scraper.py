# src/housewatch/scraper/mock_scraper.py

from typing import List
from datetime import datetime
from housewatch.models.house import House


def get_mock_houses() -> List[House]:
    """Generate mock house date for testing"""

    mock_houses = [
        House(
            listing_id="mock_001",
            address="123 Main Str",
            city="Naperville",
            state="IL",
            zip_code="60540",
            price=750000,
            year_built=1995,
            property_type="Single-Family",
            hoa_fee=0.0,
            beds=4,
            baths=2.5,
            sqft=2200,
            url="https://www.redfin.com/mock-001",
            schools=[
                "Highlands Elementary School",
                "Kennedy Junior High School",
                "Naperville North High School"
            ],
            listed_date=datetime.now()
        ),
        House(
            listing_id="mock_002",
            address="456 Oak Ave",
            city="Naperville",
            state="IL",
            zip_code="60540",
            price=720000,
            year_built=1985,
            property_type="Single-Family",
            hoa_fee=0.0,
            schools=[
                "Different Elementary School",
                "Kennedy Junior High School",
                "Naperville North High School"
            ],
            listed_date=datetime.now()
        ),
        House(
            listing_id="mock_003",
            address="789 Pine Rd",
            city="Naperville",
            state="IL",
            zip_code="60540",
            price=650000,
            year_built=1999,
            property_type="Townhouse",
            hoa_fee=150.0,
            schools=[
                "Different Elementary School",
                "Kennedy Junior High School",
                "Naperville North High School"
            ],
            listed_date=datetime.now()
        )
    ]

    return mock_houses