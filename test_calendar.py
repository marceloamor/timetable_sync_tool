"""
Test script for Google Calendar integration.
"""

import argparse
import logging
import sys
from pathlib import Path
from src.google.calendar import GoogleCalendar
from src.config import validate_config

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Google Calendar Integration Test')
    parser.add_argument('--file', type=str, help='Path to the JSON file with events to import')
    parser.add_argument('--calendar-id', type=str, help='Google Calendar ID (if not set in .env file)')
    parser.add_argument('--credentials', type=str, help='Path to the Google API credentials file (if not set in .env file)')
    args = parser.parse_args()
    
    # Validate configuration
    try:
        validate_config()
    except ValueError as e:
        print(f"Configuration error: {e}")
        return
    
    # Initialize Google Calendar
    calendar = GoogleCalendar(
        calendar_id=args.calendar_id,
        credentials_path=args.credentials
    )
    
    # Authenticate
    print("Authenticating with Google Calendar...")
    if not calendar.authenticate():
        print("Failed to authenticate with Google Calendar.")
        return
    
    # If a file was provided, import events from it
    if args.file:
        file_path = Path(args.file)
        if not file_path.exists():
            print(f"File not found: {file_path}")
            return
        
        print(f"Importing events from {file_path}...")
        event_ids = calendar.create_events_from_file(str(file_path))
        
        if event_ids:
            print(f"Successfully imported {len(event_ids)} events to Google Calendar.")
        else:
            print("No events were imported.")
    else:
        # Otherwise, just confirm that authentication works
        print("Successfully authenticated with Google Calendar.")
        print("Use --file argument to import events from a JSON file.")

if __name__ == "__main__":
    main() 