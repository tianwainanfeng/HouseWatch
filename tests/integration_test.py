# tests/integration_test.py
#!/usr/bin/env python3
"""
Quick test script to verify the pipeline works：
    Scraper -> Filter -> Storage (New Houses Only) -> Notification
"""

import os
import sys
from pathlib import Path

# Add src to path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir / "src"))

from housewatch.config import ProjectConfig
from housewatch.filters.composite_filter import filter_houses
from housewatch.scraper.mock_scraper import get_mock_houses
from housewatch.notifier.email_notifier import EmailNotifier
from housewatch.storage.json_storage import HouseStorage


def run_test():
    """Test that filters work correctly"""
    print("Testing HouseWatch pipeline...")

    try:
        # Load all configurations
        config = ProjectConfig()
        print("All configurations loaded!")

        # Show criteria
        criteria = config.get("criteria", {})
        property_criteria = criteria.get("property", {})
        school_criteria = criteria.get("schools", {})
        print(f"\nHere's the criteria:")
        print(f"    - Max price: ${property_criteria.get("max_price", 0):,}")
        print(f"    - Min Year: {property_criteria.get("min_year_built", 1980)}")
        for level, schools in school_criteria.items():
            print(f"    - {level.capitalize()} schools:")
            print(f"        - {', '.join(schools)}")

        # Initialize storage file
        test_seen_path = root_dir / "data" / "test_seen_houses.json"
        test_matched_path = root_dir / "data" / "test_matched_houses.json"

        for p in [test_seen_path, test_matched_path]:
            if p.exists():
                p.unlink()
                
        storage = HouseStorage(str(test_seen_path), str(test_matched_path))

        """Will scan twice to include storage test"""
        
        # Get mock houses -- First Scan
        print("\n---- First Round Scan -----")
        raw_houses = get_mock_houses()
        
        # Store new houses
        new_houses = [h for h in raw_houses if storage.is_new(h)]
        print(f"Total mock houses: {len(raw_houses)} (including {len(new_houses)} new houses)")

        # Apply filters
        filtered = filter_houses(new_houses, config)
        
        print(f"\nResults:")
        print(f"    - Matching houses:  {len(filtered)}")

        for i, house in enumerate(filtered, 1):
            print(f"\n Match #{i}:")
            print(f"    Address: {house.address}")
            print(f"    Price: {house.price:,}")
            print(f"    Year Built: {house.year_built}")
            print(f"    Schools:")
            for level, schools in house.schools.items():
                   print(f"     {level.capitalize()}: {', '.join(schools) if schools else 'N/A'}")
        
        # Send email notification
        notifier = EmailNotifier(config.email)

        if filtered:  
            # Print first two digits of password (for debug only)
            #pwd = config.email.get('sender_password', '')
            #print(f"DEBUG: Using password starting with: {pwd[:2]}...")
            storage.save_matched(filtered)
            notifier.send_notification(filtered)
            storage.make_multiple_as_seen(filtered)
            print(f"Test success: {len(filtered)} matched houses found, notified, and stored into {test_matched_path}")

            storage.make_multiple_as_seen(new_houses)
            print(f"Marked all {len(new_houses)} houses as seen")
        else:
            print("Test success: No houses matched criteria.")
        
        # Get mock houses - Second Scan
        print("\n---- Second Round Scan -----")
        raw_houses_2 = get_mock_houses()
        new_to_storage_2 = [h for h in raw_houses_2 if storage.is_new(h)]
        print(f"Second round scan , found new houses: {len(new_to_storage_2)}")
        
        if len(new_to_storage_2) == 0:
            print("No new houses in the second round scan!")
        else:
            print(f"Storage failed: missing {len(new_to_storage_2)} replicate houses.")
            return False
        
        print("\nAll test passed!!!")
        return True
    
    except Exception as e:
        print(f"\n❌ Test failed -- {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_test()
    sys.exit(0 if success else 1)