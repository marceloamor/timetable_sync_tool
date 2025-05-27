"""
Main script for the CELCAT to Google Calendar sync tool.
"""

import argparse
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

from src.celcat.auth import CelcatAuth
from src.celcat.scraper import CelcatScraper
from src.google.calendar import GoogleCalendar
from src.config import validate_config, STUDENT_ID

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/sync.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='CELCAT to Google Calendar Sync Tool')
    
    # General arguments
    parser.add_argument('--headless', action='store_true', help='Run in headless mode (no browser UI)')
    
    # Subparsers for different commands
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Fetch command
    fetch_parser = subparsers.add_parser('fetch', help='Fetch events from CELCAT')
    fetch_parser.add_argument('--weeks', type=int, default=4, help='Number of weeks to fetch (default: 4)')
    fetch_parser.add_argument('--output', type=str, help='Output file path (default: auto-generated)')
    
    # Sync command
    sync_parser = subparsers.add_parser('sync', help='Sync events to Google Calendar')
    sync_parser.add_argument('--file', type=str, help='Path to the JSON file with events to import')
    sync_parser.add_argument('--calendar-id', type=str, help='Google Calendar ID (if not set in .env file)')
    sync_parser.add_argument('--credentials', type=str, help='Path to the Google API credentials file (if not set in .env file)')
    
    # All-in-one command
    all_parser = subparsers.add_parser('all', help='Fetch events and sync them to Google Calendar')
    all_parser.add_argument('--weeks', type=int, default=4, help='Number of weeks to fetch (default: 4)')
    all_parser.add_argument('--calendar-id', type=str, help='Google Calendar ID (if not set in .env file)')
    all_parser.add_argument('--credentials', type=str, help='Path to the Google API credentials file (if not set in .env file)')
    
    return parser.parse_args()

def fetch_events(args):
    """Fetch events from CELCAT."""
    try:
        # Initialize auth with headless mode if requested
        auth = CelcatAuth(headless=args.headless, student_id=STUDENT_ID)
        scraper = CelcatScraper(auth)
        
        logger.info("Opening browser and navigating to CELCAT...")
        success = auth.login()
        
        if success:
            logger.info("Successfully logged in!")
            
            # Fetch events for the specified number of weeks
            logger.info(f"Getting events for {args.weeks} weeks...")
            events = scraper.get_events_for_date_range(datetime.now(), args.weeks)
            
            if events:
                logger.info(f"Found {len(events)} events")
                
                # Save events to file
                output_file = args.output if args.command == 'fetch' and args.output else None
                filename = scraper.save_events_to_file(events, output_file)
                
                if filename:
                    logger.info(f"Saved events to {filename}")
                    return filename, events
                else:
                    logger.error("Failed to save events to file")
                    return None, events
            else:
                logger.warning("No events found")
                return None, []
        else:
            logger.error("Login failed")
            return None, []
            
    except Exception as e:
        logger.error(f"An error occurred during event fetching: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None, []
    finally:
        if 'auth' in locals() and auth:
            auth.close()

def sync_events(args, events_file=None):
    """Sync events to Google Calendar."""
    try:
        # Use provided file or the one from fetch_events
        file_path = args.file if args.command == 'sync' else events_file
        
        if not file_path:
            logger.error("No events file specified")
            return False
            
        # Check if the file exists
        if not Path(file_path).exists():
            logger.error(f"File not found: {file_path}")
            return False
        
        # Initialize Google Calendar
        calendar = GoogleCalendar(
            calendar_id=args.calendar_id,
            credentials_path=args.credentials
        )
        
        # Authenticate
        logger.info("Authenticating with Google Calendar...")
        if not calendar.authenticate():
            logger.error("Failed to authenticate with Google Calendar")
            return False
        
        # Import events
        logger.info(f"Importing events from {file_path}...")
        event_ids = calendar.create_events_from_file(str(file_path))
        
        if event_ids:
            logger.info(f"Successfully imported {len(event_ids)} events to Google Calendar")
            return True
        else:
            logger.warning("No events were imported")
            return False
            
    except Exception as e:
        logger.error(f"An error occurred during event syncing: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def main():
    """Main entry point."""
    # Create logs directory
    Path("logs").mkdir(exist_ok=True)
    
    # Parse arguments
    args = parse_args()
    
    # Validate configuration
    try:
        validate_config()
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        return 1
    
    # Execute the appropriate command
    if args.command == 'fetch':
        file_path, _ = fetch_events(args)
        if file_path:
            return 0
        return 1
    elif args.command == 'sync':
        success = sync_events(args)
        return 0 if success else 1
    elif args.command == 'all':
        # Fetch events
        file_path, events = fetch_events(args)
        if not file_path or not events:
            return 1
            
        # Sync events
        success = sync_events(args, file_path)
        return 0 if success else 1
    else:
        logger.error("No command specified. Use one of: fetch, sync, all")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 