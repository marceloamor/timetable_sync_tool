"""
Google Calendar integration module.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional

import google.auth.exceptions
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from src.config import GOOGLE_CALENDAR_ID, GOOGLE_CREDENTIALS_PATH

# Set up logging
logger = logging.getLogger(__name__)

# Define the scopes for the Google Calendar API
SCOPES = ['https://www.googleapis.com/auth/calendar']

class GoogleCalendar:
    """Handle integration with Google Calendar."""
    
    def __init__(self, calendar_id: str = None, credentials_path: str = None):
        """Initialize the Google Calendar integration.
        
        Args:
            calendar_id (str, optional): The ID of the Google Calendar to use.
            credentials_path (str, optional): Path to the credentials file.
        """
        self.calendar_id = calendar_id or GOOGLE_CALENDAR_ID
        self.credentials_path = credentials_path or GOOGLE_CREDENTIALS_PATH
        self.service = None
        
        if not self.calendar_id:
            logger.warning("No calendar ID provided. Using primary calendar.")
            self.calendar_id = 'primary'
            
        if not self.credentials_path:
            logger.warning("No credentials path provided.")
        
    def authenticate(self) -> bool:
        """Authenticate with Google Calendar API.
        
        Returns:
            bool: True if authentication was successful, False otherwise.
        """
        try:
            creds = None
            
            # Create a token file path
            token_path = Path('token.json')
            
            # Check if token.json exists and load credentials from it
            if token_path.exists():
                creds = Credentials.from_authorized_user_info(
                    json.loads(token_path.read_text()),
                    SCOPES
                )
            
            # If there are no (valid) credentials available, let the user log in
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    credentials_path = Path(self.credentials_path)
                    if not credentials_path.exists():
                        logger.error(f"Credentials file not found at {credentials_path}")
                        return False
                    
                    flow = InstalledAppFlow.from_client_secrets_file(
                        str(credentials_path),
                        SCOPES
                    )
                    creds = flow.run_local_server(port=0)
                
                # Save the credentials for the next run
                token_path.write_text(creds.to_json())
            
            # Build the service
            self.service = build('calendar', 'v3', credentials=creds)
            logger.info("Successfully authenticated with Google Calendar API")
            return True
            
        except Exception as e:
            logger.error(f"Error authenticating with Google Calendar API: {str(e)}")
            return False
    
    def create_event(self, event_data: Dict[str, Any]) -> Optional[str]:
        """Create an event in Google Calendar.
        
        Args:
            event_data (Dict[str, Any]): Event data from the CELCAT scraper.
            
        Returns:
            Optional[str]: The event ID if successful, None otherwise.
        """
        if not self.service:
            if not self.authenticate():
                return None
        
        try:
            # Extract date from event_data - first check for week_date (our new field)
            date_obj = None
            
            # Try to use the week_date field first (added in the optimized scraper)
            if 'week_date' in event_data and event_data['week_date']:
                try:
                    date_obj = datetime.strptime(event_data['week_date'], '%Y-%m-%d')
                    logger.info(f"Using week_date: {event_data['week_date']}")
                except ValueError:
                    logger.warning(f"Could not parse week_date: {event_data['week_date']}")
            
            # Fall back to calendar_date if week_date is not available
            if not date_obj:
                event_date = event_data.get('calendar_date', '')
                
                # If calendar_date is in format like "May 26 – Jun 1, 2025", extract the first date
                if '–' in event_date:
                    # Format: "May 26 – Jun 1, 2025"
                    date_parts = event_date.split('–')[0].strip().split(' ')
                    if len(date_parts) >= 2:
                        # Try to parse "May 26" format
                        month = date_parts[0]
                        day = date_parts[1]
                        year = event_date.split(',')[-1].strip()
                        date_str = f"{month} {day} {year}"
                        try:
                            date_obj = datetime.strptime(date_str, "%b %d %Y")
                        except ValueError:
                            logger.warning(f"Could not parse date: {date_str}")
            
            # If we still couldn't extract a date, use the current date
            if not date_obj:
                date_obj = datetime.now()
                logger.warning(f"Using current date as fallback for event: {event_data.get('title', 'Unknown')}")
                
            # Parse the start and end times
            start_time = event_data.get('start_time', '')
            end_time = event_data.get('end_time', '')
            
            # Convert to datetime objects
            start_datetime = None
            end_datetime = None
            
            if start_time:
                try:
                    # Try AM/PM format
                    if 'AM' in start_time or 'PM' in start_time:
                        start_datetime = datetime.strptime(start_time, "%I:%M %p")
                    else:
                        # Try 24-hour format
                        start_datetime = datetime.strptime(start_time, "%H:%M")
                    
                    # Set the date part of the datetime
                    start_datetime = start_datetime.replace(
                        year=date_obj.year,
                        month=date_obj.month,
                        day=date_obj.day
                    )
                except ValueError:
                    logger.warning(f"Could not parse start time: {start_time}")
            
            if end_time:
                try:
                    # Try AM/PM format
                    if 'AM' in end_time or 'PM' in end_time:
                        end_datetime = datetime.strptime(end_time, "%I:%M %p")
                    else:
                        # Try 24-hour format
                        end_datetime = datetime.strptime(end_time, "%H:%M")
                    
                    # Set the date part of the datetime
                    end_datetime = end_datetime.replace(
                        year=date_obj.year,
                        month=date_obj.month,
                        day=date_obj.day
                    )
                except ValueError:
                    logger.warning(f"Could not parse end time: {end_time}")
            
            # If we couldn't parse the times, use defaults
            if not start_datetime or not end_datetime:
                logger.warning("Using default event times (1 hour event)")
                start_datetime = date_obj
                end_datetime = start_datetime + timedelta(hours=1)
            
            # Create the event
            event = {
                'summary': event_data.get('course_details', 'CELCAT Event'),
                'location': event_data.get('location', ''),
                'description': (
                    f"Instructor: {event_data.get('instructor', 'N/A')}\n"
                    f"Time: {event_data.get('time', 'N/A')}\n"
                    f"Course: {event_data.get('title', 'N/A')}\n"
                    f"CELCAT ID: {event_data.get('event_id', 'N/A')}"
                ),
                'start': {
                    'dateTime': start_datetime.isoformat(),
                    'timeZone': 'Europe/London',
                },
                'end': {
                    'dateTime': end_datetime.isoformat(),
                    'timeZone': 'Europe/London',
                },
                'reminders': {
                    'useDefault': True,
                },
            }
            
            # Add the event to the calendar
            result = self.service.events().insert(calendarId=self.calendar_id, body=event).execute()
            logger.info(f"Event created: {result.get('htmlLink')}")
            return result.get('id')
            
        except HttpError as e:
            logger.error(f"An error occurred while creating the event: {str(e)}")
            return None
    
    def create_events_from_file(self, file_path: str) -> List[str]:
        """Create events from a JSON file.
        
        Args:
            file_path (str): Path to the JSON file with events.
            
        Returns:
            List[str]: List of created event IDs.
        """
        try:
            # Load events from file
            with open(file_path, 'r', encoding='utf-8') as f:
                events = json.load(f)
            
            logger.info(f"Loaded {len(events)} events from {file_path}")
            
            # Create events
            event_ids = []
            for i, event in enumerate(events, 1):
                logger.info(f"Creating event {i}/{len(events)}: {event.get('course_details', 'Unknown')}")
                event_id = self.create_event(event)
                if event_id:
                    event_ids.append(event_id)
                # Add a small delay to avoid rate limiting
                if i < len(events):
                    import time
                    time.sleep(0.5)
            
            logger.info(f"Created {len(event_ids)}/{len(events)} events")
            return event_ids
            
        except Exception as e:
            logger.error(f"Error creating events from file: {str(e)}")
            return [] 