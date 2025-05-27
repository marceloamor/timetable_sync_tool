"""
Test script for CELCAT timetable scraper.
"""

import logging
import time
import argparse
from datetime import datetime
from src.celcat.auth import CelcatAuth
from src.celcat.scraper import CelcatScraper
from src.config import validate_config, STUDENT_ID

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Test CELCAT Timetable Scraper')
    parser.add_argument('--weeks', type=int, default=1, help='Number of weeks to fetch (default: 1)')
    parser.add_argument('--save', action='store_true', help='Save events to a JSON file')
    parser.add_argument('--headless', action='store_true', help='Run in headless mode (no browser UI)')
    args = parser.parse_args()
    
    # Validate configuration
    try:
        validate_config()
    except ValueError as e:
        print(f"Configuration error: {e}")
        return

    # Initialize auth with visible browser for testing (unless headless mode is requested)
    auth = CelcatAuth(headless=args.headless, student_id=STUDENT_ID)
    scraper = CelcatScraper(auth)
    
    try:
        print("Opening browser and navigating to CELCAT...")
        success = auth.login()
        
        if success:
            print("Successfully logged in!")
            
            if args.weeks <= 1:
                # For a single week, use the existing method
                print("Getting events for current week...")
                events = scraper.get_events_for_week(datetime.now())
            else:
                # For multiple weeks, use the new date range method
                print(f"Getting events for {args.weeks} weeks...")
                events = scraper.get_events_for_date_range(datetime.now(), args.weeks)
            
            if events:
                print(f"\nFound {len(events)} events:")
                
                # Save events to file if requested
                if args.save:
                    filename = scraper.save_events_to_file(events)
                    if filename:
                        print(f"Saved events to {filename}")
                
                # Print the first 5 events (or all if less than 5)
                for i, event in enumerate(events[:5], 1):
                    print(f"\nEvent {i}/{len(events)}:")
                    print(f"Title: {event.get('title', 'N/A')}")
                    print(f"Time: {event.get('time', 'N/A')}")
                    print(f"Start: {event.get('start_time', 'N/A')}")
                    print(f"End: {event.get('end_time', 'N/A')}")
                    print(f"Location: {event.get('location', 'N/A')}")
                    print(f"Instructor: {event.get('instructor', 'N/A')}")
                    print(f"Course Details: {event.get('course_details', 'N/A')}")
                    print(f"Calendar Date: {event.get('calendar_date', 'N/A')}")
                
                # If there are more than 5 events, just show a summary
                if len(events) > 5:
                    print(f"\n... and {len(events) - 5} more events")
            else:
                print("No events found.")
                print("Saving page source for debugging...")
                scraper._save_page_content("no_events_found")
            
            print("\nBrowser will stay open for 10 seconds for inspection...")
            time.sleep(10)
        else:
            print("Login failed. Browser will stay open for 30 seconds for inspection...")
            time.sleep(30)
            
    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()
        print("Browser will stay open for 30 seconds for inspection...")
        time.sleep(30)
    finally:
        auth.close()

if __name__ == "__main__":
    main() 