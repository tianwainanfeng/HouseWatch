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
        #  If you wanted to start with new storage files
        #  for p in [seen_path, matched_path]:
        #     if p.exists():
        #         p.unlink()
        #logger.info(f"\n\tSeen path: {seen_path}")
        #logger.info(f"\n\tMatched path: {matched_path}")

        # ==== This part has been modified to move filtration and storage in redfin_scraper ====

        storage = HouseStorage(str(seen_path), str(matched_path))
        scraper = RedfinScraper(config, storage)
        notifier = EmailNotifier(config.email)
            
        # Fetch new matched from Redfin
        new_listings = scraper.fetch()
        logger.info(f"Found {len(new_listings)} NEW matches!")    
        
        if not new_listings:
            logger.info("No new houses since last check.")
            return
               
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
