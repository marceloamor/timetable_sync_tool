"""
Main script for CELCAT to Google Calendar sync.
"""

import logging
from datetime import datetime, timedelta
from celcat.auth import CelcatAuth
from celcat.scraper import CelcatScraper
from config import Config

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main entry point for the application."""
    try:
        # Load configuration
        config = Config()
        
        # Validate that we have all required configuration
        if not config.STUDENT_ID:
            logger.error("STUDENT_ID is not set in environment variables")
            return
            
        logger.info(f"Using student ID: {config.STUDENT_ID}")
        
        # Initialize CELCAT authentication
        auth = CelcatAuth(
            base_url=config.CELCAT_BASE_URL,
            username=config.CELCAT_USERNAME,
            password=config.CELCAT_PASSWORD,
            student_id=config.STUDENT_ID
        )
        
        # Login to CELCAT
        if not auth.login():
            logger.error("Failed to login to CELCAT")
            return
            
        # Initialize scraper
        scraper = CelcatScraper(auth)
        
        # Get events for current week
        start_date = datetime.now()
        events = scraper.get_events_for_week(start_date)
        
        # Print found events
        logger.info(f"Found {len(events)} events")
        for event in events:
            logger.info(f"Event: {event['title']}")
            logger.info(f"Time: {event['time']}")
            logger.info(f"Location: {event['location']}")
            logger.info("---")
            
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
    finally:
        # Clean up
        if 'auth' in locals():
            auth.close()

if __name__ == "__main__":
    main() 