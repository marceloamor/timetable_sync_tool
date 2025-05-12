"""
Test script for CELCAT timetable scraper.
"""

import logging
import time
from datetime import datetime
from src.celcat.auth import CelcatAuth
from src.celcat.scraper import CelcatScraper
from src.config import validate_config

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    # Validate configuration
    try:
        validate_config()
    except ValueError as e:
        print(f"Configuration error: {e}")
        return

    # Initialize auth with visible browser for testing
    auth = CelcatAuth(headless=False)
    scraper = CelcatScraper(auth)
    
    try:
        print("Opening browser and navigating to CELCAT...")
        success = auth.login()
        
        if success:
            print("Successfully logged in!")
            
            # Try to get events for the current week
            print("Getting events for current week...")
            events = scraper.get_events_for_week(datetime.now())
            
            if events:
                print(f"\nFound {len(events)} events:")
                for i, event in enumerate(events, 1):
                    print(f"\nEvent {i}:")
                    print(f"Title: {event['title']}")
                    print(f"Start: {event['start_time']}")
                    print(f"End: {event['end_time']}")
                    print(f"Location: {event['location']}")
                    print("Raw HTML:", event['raw_html'][:200] + "..." if len(event['raw_html']) > 200 else event['raw_html'])
            else:
                print("No events found.")
            
            print("\nBrowser will stay open for 30 seconds for inspection...")
            time.sleep(30)
        else:
            print("Login failed. Browser will stay open for 30 seconds for inspection...")
            time.sleep(30)
            
    except Exception as e:
        print(f"An error occurred: {e}")
        print("Browser will stay open for 30 seconds for inspection...")
        time.sleep(30)
    finally:
        auth.close()

if __name__ == "__main__":
    main() 