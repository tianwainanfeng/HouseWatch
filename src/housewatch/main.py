# src/housewatch/main.py

import os
import sys
from pathlib import Path
import logging
from datetime import datetime


# 1. Get the directory where main.py lives: root_dir/src/housewatch/
# 2. Get the 'src' directory: root_dir/src/
# This is the directory Python needs to 'see' the 'housewatch' package
# 3. Add 'src' to sys.path
current_dir = Path(__file__).resolve().parent
src_dir = current_dir.parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))
root_dir = src_dir.parent

from housewatch.config import ProjectConfig
from housewatch.scraper.redfin_scraper import RedfinScraper
from housewatch.filters.composite_filter import filter_houses
from housewatch.storage.json_storage import HouseStorage
from housewatch.notifier.email_notifier import EmailNotifier

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main pipeline: scrape -> filter -> storage -> notify"""
    logger.info("Starting HouseWatch Service...")

    try:
        # Load configuration
        config = ProjectConfig()
        logger.info("✓ Configuration loaded")
        #print("config:\n", vars(config))

        # Initialize components
        seen_path = root_dir / "data" / "seen_houses.json"
        matched_path = root_dir / "data" / "matched_houses.json"
        #logger.info(f"\n\tSeen path: {seen_path}")
        #logger.info(f"\n\tMatched path: {matched_path}")

        scraper = RedfinScraper(config)
        storage = HouseStorage(str(seen_path), str(matched_path))
        notifier = EmailNotifier(config.email)
            
        # Fech from Redfin
        all_houses = scraper.fetch()

        # Filter out houses that have been seen (Deduplication)
        new_listings = [h for h in all_houses if storage.is_new(h)]        
        logger.info(f"Processing {len(new_listings)} brank new listings (skipping {len(all_houses)-len(new_listings)} already seen)")

        if not new_listings:
            logger.info("No new houses since last check.")
            return

        """
        # This part is not needed as the filtration is applied in redfin_scraper (fast!).
        # Apply criteria
        matched_houses = filter_houses(new_listings, config)
        logger.info(f"✓ {len(matched_houses)} houses match all criteria")

        if matched_houses:
            logger.info(f"Found {len(matched_houses)} NEW matches!")
            storage.save_matched(matched_houses)

            # Send notification
            if notifier.send_notification(matched_houses):
                logger.info("Email notification sent")
            else:
                logger.info("Failed to send email notification")
        else:
            logger.info("No matches found among new listings")
        """
        
        logger.info(f"Found {len(new_listings)} NEW matches!")
        storage.save_matched(new_listings)

        # Send notification
        if notifier.send_notification(new_listings):
            logger.info("Email notification sent")
        else:
            logger.info("Failed to send email notification")

        # Mark all processed listings as 'seen'
        storage.make_multiple_as_seen(new_listings)
        logger.info(f"Marked {len(new_listings)} houses as seen in history.")
        
    except Exception as e:
        logger.error(f"Main pipeline crashed: {e}", exc_info=True)
    
    print(f"HouseWatch run completed at {datetime.now().strftime('%Y-%m-%d %H: %M: %S')}")


if __name__ == "__main__":
    main()
