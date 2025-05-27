"""
CELCAT timetable scraper module.
"""

from bs4 import BeautifulSoup
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import os
import re
from pathlib import Path

from src.celcat.auth import CelcatAuth

logger = logging.getLogger(__name__)

class CelcatScraper:
    """Handle scraping of timetable data from CELCAT."""
    
    def __init__(self, auth: CelcatAuth):
        """Initialize the CELCAT scraper.
        
        Args:
            auth (CelcatAuth): Authenticated CELCAT session.
        """
        self.auth = auth
        
    def _save_page_content(self, prefix: str = "debug"):
        """Save the current page content for debugging.
        
        Args:
            prefix (str): Prefix for the debug file name.
        """
        try:
            # Create debug directory if it doesn't exist
            debug_dir = Path("debug")
            debug_dir.mkdir(exist_ok=True)
            
            # Save the page source
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = debug_dir / f"{prefix}_{timestamp}.html"
            
            with open(filename, "w", encoding="utf-8") as f:
                f.write(self.auth.driver.page_source)
                
            logger.info(f"Saved page content to {filename}")
            
            # Also save a screenshot
            screenshot_path = debug_dir / f"{prefix}_{timestamp}.png"
            self.auth.driver.save_screenshot(str(screenshot_path))
            logger.info(f"Saved screenshot to {screenshot_path}")
            
        except Exception as e:
            logger.error(f"Error saving debug content: {str(e)}")
        
    def get_timetable_url(self, start_date: datetime) -> str:
        """Generate the timetable URL for a given date.
        
        Args:
            start_date (datetime): The start date for the timetable view.
            
        Returns:
            str: The timetable URL.
        """
        date_str = start_date.strftime("%Y-%m-%d")
        return f"{self.auth.base_url}/cal?vt=agendaWeek&dt={date_str}&et=student&fid0={self.auth.student_id}"
        
    def _parse_event_time(self, time_text: str) -> tuple:
        """Parse event time string into start and end datetime objects.
        
        Args:
            time_text (str): Time text from the event element (e.g. "9:00 - 10:30")
            
        Returns:
            tuple: (start_time, end_time) as strings, or empty strings if parsing fails
        """
        try:
            if not time_text:
                return "", ""
                
            # Handle different time formats
            # Format like "09:00 - 10:30"
            time_match = re.search(r'(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})', time_text)
            if time_match:
                start_time = time_match.group(1)
                end_time = time_match.group(2)
                return start_time, end_time
                
            # Format with AM/PM like "9:00 AM - 10:30 AM"
            am_pm_match = re.search(r'(\d{1,2}:\d{2}\s*[AP]M)\s*-\s*(\d{1,2}:\d{2}\s*[AP]M)', time_text)
            if am_pm_match:
                start_time = am_pm_match.group(1)
                end_time = am_pm_match.group(2)
                return start_time, end_time
                
            logger.warning(f"Could not parse time text: {time_text}")
            return "", ""
            
        except Exception as e:
            logger.error(f"Error parsing event time: {str(e)}")
            return "", ""
        
    def get_events(self) -> List[Dict[str, Any]]:
        """Extract all events from the current timetable view.
        
        Returns:
            List[Dict[str, Any]]: List of events with their details.
        """
        try:
            # Wait for the calendar to be fully loaded
            WebDriverWait(self.auth.driver, 10).until(
                EC.presence_of_element_located((By.ID, "calendar"))
            )
            
            # Save the page content for debugging
            self._save_page_content("calendar_page")
            
            # Try different event selectors based on the actual HTML
            event_selectors = [
                "a.fc-time-grid-event",  # Primary selector from HTML inspection
                "a[class*='fc-event']",  # Any anchor with fc-event in class
                "div.fc-event",          # FullCalendar default
                "div.fc-time-grid-event", # Time grid events
                "div.fc-day-grid-event",  # Day grid events
                "div[class*='fc-event']", # Any div with fc-event in class
            ]
            
            events = []
            for selector in event_selectors:
                try:
                    # Try to find events using Selenium
                    event_elements = self.auth.driver.find_elements(By.CSS_SELECTOR, selector)
                    if event_elements:
                        logger.info(f"Found {len(event_elements)} events using selector: {selector}")
                        
                        for element in event_elements:
                            try:
                                # Get the event details
                                raw_html = element.get_attribute("outerHTML")
                                event_id = element.get_attribute("id") or ""
                                
                                # Extract the full content
                                content_element = element.find_element(By.CLASS_NAME, "fc-content")
                                content_text = content_element.text if content_element else element.text
                                
                                # Try to get time information
                                time_text = ""
                                try:
                                    time_element = element.find_element(By.CLASS_NAME, "fc-time")
                                    time_text = time_element.get_attribute("data-full") or time_element.text
                                except NoSuchElementException:
                                    # Try to extract time from content
                                    if content_text and " - " in content_text and ":" in content_text:
                                        # Look for time pattern in content
                                        time_match = re.search(r'(\d{1,2}:\d{2}(?: [AP]M)?) - (\d{1,2}:\d{2}(?: [AP]M)?)', content_text)
                                        if time_match:
                                            time_text = f"{time_match.group(1)} - {time_match.group(2)}"
                                
                                # Parse the time text into start and end times
                                start_time, end_time = self._parse_event_time(time_text)
                                
                                # Parse the content to extract course code, location, and instructor
                                lines = content_text.strip().split('\n')
                                title = lines[0] if lines else ""
                                
                                # Extract location if present
                                location = ""
                                for line in lines:
                                    if "[" in line and "]" in line:  # Room usually has capacity in brackets
                                        location = line.strip()
                                        break
                                
                                # Extract instructor if present (usually after location)
                                instructor = ""
                                found_location = False
                                for line in lines:
                                    if found_location and line.strip():
                                        instructor = line.strip()
                                        break
                                    if line.strip() == location:
                                        found_location = True
                                
                                # Extract course name/details (usually the last line)
                                course_details = lines[-1] if len(lines) > 1 else ""
                                
                                # Get the current date from the calendar
                                current_date = ""
                                try:
                                    # Attempt to get the date from the event's parent day column
                                    # This might need adjusting based on the actual HTML structure
                                    date_element = self.auth.driver.find_element(By.CSS_SELECTOR, ".fc-today")
                                    current_date = date_element.get_attribute("data-date")
                                except:
                                    # If we can't get the specific day, try to get the week range from the header
                                    try:
                                        header_element = self.auth.driver.find_element(By.CSS_SELECTOR, ".fc-center h2")
                                        current_date = header_element.text
                                    except:
                                        pass
                                
                                event = {
                                    'title': title,
                                    'time': time_text,
                                    'start_time': start_time,
                                    'end_time': end_time,
                                    'location': location,
                                    'instructor': instructor,
                                    'course_details': course_details,
                                    'content': content_text,
                                    'event_id': event_id,
                                    'calendar_date': current_date,
                                    'raw_html': raw_html
                                }
                                events.append(event)
                                
                            except Exception as e:
                                logger.error(f"Error extracting event details: {str(e)}")
                                continue
                        
                        # If we found events with this selector, no need to try others
                        break
                        
                except Exception as e:
                    logger.error(f"Error with selector {selector}: {str(e)}")
                    continue
            
            if not events:
                # If no events found with Selenium, try BeautifulSoup
                html_content = self.auth.driver.page_source
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Save the parsed HTML for debugging
                debug_dir = Path("debug")
                debug_dir.mkdir(exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                with open(debug_dir / f"parsed_html_{timestamp}.html", "w", encoding="utf-8") as f:
                    f.write(str(soup.prettify()))
                
                for selector in event_selectors:
                    event_elements = soup.select(selector)
                    if event_elements:
                        logger.info(f"Found {len(event_elements)} events using BeautifulSoup with selector: {selector}")
                        
                        for element in event_elements:
                            try:
                                # Get the full HTML
                                raw_html = str(element)
                                event_id = element.get('id', '')
                                
                                # Extract the content
                                content_element = element.select_one('.fc-content')
                                content_text = content_element.text.strip() if content_element else element.text.strip()
                                
                                # Try to get time information
                                time_element = element.select_one('.fc-time')
                                time_text = ""
                                if time_element:
                                    time_text = time_element.get('data-full', '') or time_element.text.strip()
                                
                                # Parse the time text into start and end times
                                start_time, end_time = self._parse_event_time(time_text)
                                
                                # Parse the content to extract course code, location, and instructor
                                lines = content_text.strip().split('\n')
                                title = lines[0] if lines else ""
                                
                                # Extract location if present
                                location = ""
                                for line in lines:
                                    if "[" in line and "]" in line:  # Room usually has capacity in brackets
                                        location = line.strip()
                                        break
                                
                                # Extract instructor if present (usually after location)
                                instructor = ""
                                found_location = False
                                for line in lines:
                                    if found_location and line.strip():
                                        instructor = line.strip()
                                        break
                                    if line.strip() == location:
                                        found_location = True
                                
                                # Extract course name/details (usually the last line)
                                course_details = lines[-1] if len(lines) > 1 else ""
                                
                                # Get the current date from the calendar
                                current_date = ""
                                try:
                                    header_element = soup.select_one(".fc-center h2")
                                    if header_element:
                                        current_date = header_element.text.strip()
                                except:
                                    pass
                                
                                event = {
                                    'title': title,
                                    'time': time_text,
                                    'start_time': start_time,
                                    'end_time': end_time,
                                    'location': location,
                                    'instructor': instructor,
                                    'course_details': course_details,
                                    'content': content_text,
                                    'event_id': event_id,
                                    'calendar_date': current_date,
                                    'raw_html': raw_html
                                }
                                events.append(event)
                            except Exception as e:
                                logger.error(f"Error extracting event with BeautifulSoup: {str(e)}")
                                continue
                        
                        break
            
            logger.info(f"Total events found: {len(events)}")
            return events
            
        except Exception as e:
            logger.error(f"Error getting events: {str(e)}")
            # Save the page content even if there's an error
            self._save_page_content("error_page")
            return []
            
    def get_events_for_week(self, start_date: datetime = None) -> List[Dict[str, Any]]:
        """Get all events for a specific week.
        
        Args:
            start_date (datetime, optional): The start date of the week. Defaults to current date.
            
        Returns:
            List[Dict[str, Any]]: List of events for the week.
        """
        if not start_date:
            start_date = datetime.now()
            
        # Navigate to the timetable for the given date
        if not self.auth.navigate_to_timetable(start_date):
            return []
            
        # Give the page time to fully load
        time.sleep(5)
        
        # Extract events
        return self.get_events()
        
    def get_timetable(self, start_date: datetime = None) -> List[Dict[str, Any]]:
        """Get the timetable for a given date range.
        
        Args:
            start_date (datetime, optional): The start date. Defaults to current date.
            
        Returns:
            List[Dict[str, Any]]: List of timetable events.
        """
        if not start_date:
            start_date = datetime.now()
            
        try:
            url = self.get_timetable_url(start_date)
            self.auth.driver.get(url)
            
            # Wait for the timetable to load
            time.sleep(5)
            
            return self.get_events()
            
        except Exception as e:
            logger.error(f"Error getting timetable: {str(e)}")
            return []
            
    def get_events_for_date_range(self, start_date: datetime = None, num_weeks: int = 16) -> List[Dict[str, Any]]:
        """Get all events for a specific date range.
        
        Args:
            start_date (datetime, optional): The start date of the range. Defaults to current date.
            num_weeks (int, optional): Number of weeks to fetch. Defaults to 16 (about 4 months).
            
        Returns:
            List[Dict[str, Any]]: List of events for the date range with no duplicates.
        """
        if not self.auth.driver:
            # Make sure we have a driver before starting
            if not self.auth.login():
                logger.error("Failed to log in")
                return []
        
        if not start_date:
            start_date = datetime.now()
            
        all_events = []
        unique_event_ids = set()  # To track unique events
        
        # Start from the given date and go forward for the specified number of weeks
        current_date = start_date
        
        logger.info(f"Fetching events for {num_weeks} weeks starting from {current_date.strftime('%Y-%m-%d')}")
        
        for week in range(num_weeks):
            logger.info(f"Fetching week {week+1}/{num_weeks}: {current_date.strftime('%Y-%m-%d')}")
            
            try:
                # For the first week, we need to navigate properly
                if week == 0:
                    # Navigate to the timetable for the given date
                    if not self.auth.navigate_to_timetable(current_date):
                        logger.error(f"Failed to navigate to week {week+1}")
                        continue
                else:
                    # For subsequent weeks, directly navigate to the URL
                    url = self.get_timetable_url(current_date)
                    logger.info(f"Directly navigating to URL: {url}")
                    self.auth.driver.get(url)
                    time.sleep(5)  # Give page time to load
                    
                    # Wait for the calendar to be present
                    try:
                        WebDriverWait(self.auth.driver, 10).until(
                            EC.presence_of_element_located((By.ID, "calendar"))
                        )
                    except TimeoutException:
                        logger.error(f"Calendar not found for week {week+1}")
                        continue
                
                # Give the page time to fully load
                time.sleep(3)
                
                # Extract events
                events = self.get_events()
                
                # Add only unique events to the result list
                for event in events:
                    # Create a unique identifier based on available data
                    event_identifier = (
                        f"{event.get('title', '')}-{event.get('time', '')}-"
                        f"{event.get('location', '')}-{event.get('course_details', '')}"
                    )
                    
                    if event_identifier not in unique_event_ids:
                        unique_event_ids.add(event_identifier)
                        # Set the actual date for this event based on the current week
                        event['week_date'] = current_date.strftime('%Y-%m-%d')
                        all_events.append(event)
                
                logger.info(f"Week {week+1}: Found {len(events)} events, {len(all_events)} total unique events so far")
                
                # Can also try using the "next" button if available
                try:
                    next_button = self.auth.driver.find_element(By.CLASS_NAME, "fc-next-button")
                    if next_button and week < num_weeks - 1:
                        logger.info("Using next button to navigate to next week")
                        next_button.click()
                        time.sleep(5)
                        # Update current_date based on what's now displayed
                        try:
                            header_element = self.auth.driver.find_element(By.CSS_SELECTOR, ".fc-center h2")
                            if header_element:
                                logger.info(f"Calendar header shows: {header_element.text}")
                        except:
                            pass
                        # Still increment current_date manually as backup
                        current_date += timedelta(days=7)
                        continue  # Skip the current_date increment at the end of the loop
                except:
                    logger.info("Next button not found or not clickable, using URL navigation")
                
            except Exception as e:
                logger.error(f"Error fetching week {week+1}: {str(e)}")
                # Continue with the next week
            
            # Move to the next week
            current_date += timedelta(days=7)
            
            # Add a short pause between requests to avoid overloading the server
            time.sleep(1)
        
        logger.info(f"Completed fetching {len(all_events)} unique events across {num_weeks} weeks")
        return all_events
    
    def save_events_to_file(self, events: List[Dict[str, Any]], filename: str = None):
        """Save events to a JSON file.
        
        Args:
            events (List[Dict[str, Any]]): List of events to save.
            filename (str, optional): Filename to save to. Defaults to auto-generated name.
        """
        import json
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"events_{timestamp}.json"
        
        # Create data directory if it doesn't exist
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)
        
        file_path = data_dir / filename
        
        try:
            # Process events to make them JSON serializable
            processed_events = []
            for event in events:
                # Create a copy without the raw HTML to make the file smaller
                event_copy = {k: v for k, v in event.items() if k != 'raw_html'}
                processed_events.append(event_copy)
                
            # Save to file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(processed_events, f, indent=2, ensure_ascii=False)
                
            logger.info(f"Saved {len(processed_events)} events to {file_path}")
            return str(file_path)
            
        except Exception as e:
            logger.error(f"Error saving events to file: {str(e)}")
            return None 