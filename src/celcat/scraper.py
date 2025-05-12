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

from .auth import CelcatAuth

logger = logging.getLogger(__name__)

class CelcatScraper:
    """Handle scraping of timetable data from CELCAT."""
    
    def __init__(self, auth: CelcatAuth):
        """Initialize the CELCAT scraper.
        
        Args:
            auth (CelcatAuth): Authenticated CELCAT session.
        """
        self.auth = auth
        
    def get_timetable_url(self, start_date: datetime) -> str:
        """Generate the timetable URL for a given date.
        
        Args:
            start_date (datetime): The start date for the timetable view.
            
        Returns:
            str: The timetable URL.
        """
        date_str = start_date.strftime("%Y-%m-%d")
        return f"{self.auth.base_url}/cal?vt=agendaWeek&dt={date_str}&et=student&fid0={self.auth.student_id}"
        
    def get_events(self) -> List[Dict[str, Any]]:
        """Extract all events from the current timetable view.
        
        Returns:
            List[Dict[str, Any]]: List of events with their details.
        """
        try:
            # Wait for the calendar to be fully loaded
            WebDriverWait(self.auth.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "calendar"))
            )
            
            # Try different event selectors
            event_selectors = [
                "div.fc-event",  # FullCalendar default
                "div.fc-time-grid-event",  # Time grid events
                "div.fc-day-grid-event",   # Day grid events
                "div[class*='fc-event']",  # Any class containing fc-event
            ]
            
            events = []
            for selector in event_selectors:
                try:
                    # Try to find events using Selenium first
                    event_elements = self.auth.driver.find_elements(By.CSS_SELECTOR, selector)
                    if event_elements:
                        logger.info(f"Found {len(event_elements)} events using selector: {selector}")
                        
                        for element in event_elements:
                            try:
                                # Get the event details
                                title = element.get_attribute("title") or element.text
                                
                                # Try to get time information
                                time_element = element.find_element(By.CLASS_NAME, "fc-time")
                                time_text = time_element.text if time_element else ""
                                
                                # Try to get location
                                location = ""
                                try:
                                    location_element = element.find_element(By.CLASS_NAME, "fc-location")
                                    location = location_element.text
                                except NoSuchElementException:
                                    pass
                                
                                # Get the raw HTML for debugging
                                raw_html = element.get_attribute("outerHTML")
                                
                                event = {
                                    'title': title,
                                    'time': time_text,
                                    'location': location,
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
                
                for selector in event_selectors:
                    event_elements = soup.select(selector)
                    if event_elements:
                        logger.info(f"Found {len(event_elements)} events using BeautifulSoup with selector: {selector}")
                        
                        for element in event_elements:
                            try:
                                event = {
                                    'title': element.get('title', ''),
                                    'time': element.find(class_='fc-time').text if element.find(class_='fc-time') else '',
                                    'location': element.find(class_='fc-location').text if element.find(class_='fc-location') else '',
                                    'raw_html': str(element)
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
            # TODO: Add appropriate wait condition based on actual page structure
            
            html_content = self.auth.driver.page_source
            return self.get_events()
            
        except Exception as e:
            logger.error(f"Error getting timetable: {str(e)}")
            return [] 