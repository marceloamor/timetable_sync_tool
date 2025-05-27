"""
CELCAT authentication module.
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType
import logging
import time
from datetime import datetime
import os
import sys
from pathlib import Path

from src.config import CELCAT_USERNAME, CELCAT_PASSWORD, CELCAT_BASE_URL, STUDENT_ID

logger = logging.getLogger(__name__)

class CelcatAuth:
    """Handle authentication with CELCAT timetable system."""
    
    def __init__(self, base_url: str = None, username: str = None, password: str = None, student_id: str = None, headless: bool = True):
        """Initialize the CELCAT authentication handler.
        
        Args:
            base_url (str, optional): The base URL for CELCAT. Defaults to None.
            username (str, optional): The username for login. Defaults to None.
            password (str, optional): The password for login. Defaults to None.
            student_id (str): The student ID for timetable access. Required.
            headless (bool, optional): Whether to run the browser in headless mode. Defaults to True.
        """
        self.headless = headless
        self.driver = None
        self.base_url = base_url or CELCAT_BASE_URL
        self.username = username or CELCAT_USERNAME
        self.password = password or CELCAT_PASSWORD
        self.student_id = student_id or STUDENT_ID
        
        if not self.student_id:
            raise ValueError("student_id is required")
            
        logger.info(f"Initializing CelcatAuth with student_id: {self.student_id}")
        
    def setup_driver(self):
        """Set up the Selenium WebDriver with appropriate options."""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless=new")
        
        # WSL-specific options
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-software-rasterizer")
        chrome_options.add_argument("--disable-features=VizDisplayCompositor")
        
        # Additional options for stability
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-infobars")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--disable-popup-blocking")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        
        # Fix for DevToolsActivePort issue
        chrome_options.add_argument("--remote-debugging-port=9222")
        chrome_options.add_argument("--no-first-run")
        chrome_options.add_argument("--no-default-browser-check")
        
        # Set binary location explicitly for WSL
        chrome_options.binary_location = "/usr/bin/google-chrome-stable"
        
        # Create a temporary directory for Chrome with proper permissions
        chrome_data_dir = "/tmp/chrome_data"
        os.makedirs(chrome_data_dir, exist_ok=True)
        os.chmod(chrome_data_dir, 0o777)  # Ensure directory is writable
        chrome_options.add_argument(f"--user-data-dir={chrome_data_dir}")
        
        try:
            logger.info("Attempting to set up Chrome driver")
            
            # Get Chrome version
            chrome_version = ""
            try:
                chrome_version = os.popen('google-chrome-stable --version').read().strip()
                chrome_version = chrome_version.replace('Google Chrome ', '')
                logger.info(f"Detected Chrome version: {chrome_version}")
            except Exception as e:
                logger.warning(f"Could not determine Chrome version: {str(e)}")
            
            # Install ChromeDriver with proper cache directory
            logger.info("Installing ChromeDriver")
            driver_cache_dir = Path.home() / ".wdm" / "drivers"
            driver_cache_dir.mkdir(parents=True, exist_ok=True)
            
            # Install ChromeDriver using WebDriverManager
            try:
                driver_path = ChromeDriverManager().install()
                logger.info(f"ChromeDriver installed at: {driver_path}")
                service = Service(driver_path)
            except Exception as e:
                logger.error(f"Error installing ChromeDriver via manager: {str(e)}")
                raise
            
            # Create driver with explicit error handling
            logger.info("Creating Chrome WebDriver")
            self.driver = webdriver.Chrome(
                service=service,
                options=chrome_options
            )
            
            # Set timeouts
            self.driver.set_page_load_timeout(30)
            self.driver.implicitly_wait(10)
            
            logger.info("Chrome driver setup successful")
            
        except Exception as e:
            logger.error(f"Error setting up Chrome driver: {str(e)}")
            # Additional error information
            try:
                chrome_version = os.popen('google-chrome-stable --version').read().strip()
                logger.error(f"Chrome version: {chrome_version}")
            except:
                logger.error("Could not determine Chrome version")
                
            try:
                chromedriver_version = os.popen('chromedriver --version').read().strip()
                logger.error(f"ChromeDriver version: {chromedriver_version}")
            except:
                logger.error("Could not determine ChromeDriver version")
                
            raise

    def _save_debug_screenshot(self, prefix="error"):
        """Save a screenshot for debugging purposes."""
        try:
            if not self.driver:
                return
                
            # Create debug directory if it doesn't exist
            debug_dir = Path("debug")
            debug_dir.mkdir(exist_ok=True)
            
            # Save screenshot
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = debug_dir / f"{prefix}_{timestamp}.png"
            self.driver.save_screenshot(str(screenshot_path))
            logger.info(f"Saved debug screenshot to {screenshot_path}")
            
            # Save HTML
            html_path = debug_dir / f"{prefix}_{timestamp}.html"
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)
            logger.info(f"Saved debug HTML to {html_path}")
            
        except Exception as e:
            logger.error(f"Error saving debug screenshot: {str(e)}")

    def login(self):
        """Log in to the CELCAT timetable system.
        
        Returns:
            bool: True if login was successful, False otherwise.
        """
        try:
            if not self.driver:
                self.setup_driver()
                
            # Navigate to the login page
            logger.info(f"Navigating to login page: {self.base_url}/login")
            self.driver.get(f"{self.base_url}/login")
            time.sleep(2)  # Give the page time to load
            
            # Save screenshot before login attempt
            self._save_debug_screenshot("before_login")
            
            # Print the current URL for debugging
            logger.info(f"Current URL: {self.driver.current_url}")
            
            try:
                # Wait for the login form to be present
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "form"))
                )
                
                # Find the username field (usually the first input field)
                username_field = self.driver.find_element(By.CSS_SELECTOR, "input[type='text'], input[type='email']")
                username_field.clear()
                username_field.send_keys(self.username)
                time.sleep(1)
                
                # Find the password field (usually the second input field)
                password_field = self.driver.find_element(By.CSS_SELECTOR, "input[type='password']")
                password_field.clear()
                password_field.send_keys(self.password)
                time.sleep(1)
                
                # Save screenshot before clicking submit
                self._save_debug_screenshot("before_submit")
                
                # Find and click the submit button
                submit_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit'], input[type='submit']")
                submit_button.click()
                
                # Wait for successful login
                time.sleep(5)  # Give the page time to process login
                
                # Save screenshot after login attempt
                self._save_debug_screenshot("after_login")
                
                # Check if we're still on the login page
                if "login" in self.driver.current_url.lower():
                    logger.error("Still on login page after submission")
                    return False
                
                logger.info(f"Successfully logged in to CELCAT. Current URL: {self.driver.current_url}")
                return True
                
            except (TimeoutException, NoSuchElementException) as e:
                logger.error(f"Error during login process: {str(e)}")
                self._save_debug_screenshot("login_error")
                return False
            
        except Exception as e:
            logger.error(f"Failed to log in to CELCAT: {str(e)}")
            if self.driver:
                self._save_debug_screenshot("login_exception")
            return False

    def navigate_to_timetable(self, start_date: datetime = None):
        """Navigate to the timetable view for a specific date.
        
        Args:
            start_date (datetime, optional): The date to view. Defaults to current date.
            
        Returns:
            bool: True if navigation was successful, False otherwise.
        """
        try:
            if not start_date:
                start_date = datetime.now()
                
            # Format the date for the URL
            date_str = start_date.strftime("%Y-%m-%d")
            
            # First, try to access the main timetable page
            main_url = f"{self.base_url}/cal"
            logger.info(f"Navigating to main timetable URL: {main_url}")
            self.driver.get(main_url)
            time.sleep(5)  # Give the page time to load
            
            self._save_debug_screenshot("main_timetable")
            
            # Check for any permission warnings
            try:
                warning = self.driver.find_element(By.CLASS_NAME, "alert-warning")
                if warning:
                    logger.warning(f"Permission warning found: {warning.text}")
                    # Try to find and click any "Accept" or "Continue" buttons
                    try:
                        accept_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Accept') or contains(text(), 'Continue')]")
                        accept_button.click()
                        time.sleep(2)
                    except NoSuchElementException:
                        logger.error("Could not find accept button")
                        return False
            except NoSuchElementException:
                # No warning found, continue
                pass
            
            # Now navigate to the specific week view
            timetable_url = f"{self.base_url}/cal?vt=agendaWeek&dt={date_str}&et=student&fid0={self.student_id}"
            logger.info(f"Navigating to specific timetable URL: {timetable_url}")
            self.driver.get(timetable_url)
            time.sleep(5)  # Give the page time to load
            
            self._save_debug_screenshot("specific_timetable")
            
            # Wait for the calendar to be present - using the correct id "calendar"
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.ID, "calendar"))
                )
                
                # Check if we can see any events
                # First check for fc-time-grid-event which is what we see in the HTML
                events = self.driver.find_elements(By.CLASS_NAME, "fc-time-grid-event")
                
                if not events:
                    logger.warning("No fc-time-grid-event elements found, trying alternative selectors")
                    
                    # Try alternative selectors
                    alternative_selectors = [
                        "fc-event",
                        "fc-day-grid-event",
                        "div[class*='fc-event']",
                        "a[class*='fc-event']",
                        "a.fc-time-grid-event"
                    ]
                    
                    for selector in alternative_selectors:
                        events = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        if events:
                            logger.info(f"Found {len(events)} events with selector '{selector}'")
                            break
                            
                    if not events:
                        logger.warning("No events found with initial selectors. Looking at the whole calendar structure")
                        
                        # Get the calendar element
                        calendar = self.driver.find_element(By.ID, "calendar")
                        
                        # Log what we find in the calendar
                        logger.info(f"Calendar found with structure: {calendar.get_attribute('outerHTML')[:200]}...")
                        
                        # Look for any elements that could be events inside the calendar
                        potential_events = calendar.find_elements(By.CSS_SELECTOR, "div.fc-content, a.fc-time-grid-event, a[class*='fc-event'], div[class*='fc-event']")
                        
                        if potential_events:
                            logger.info(f"Found {len(potential_events)} potential event elements inside calendar")
                            return True
                        else:
                            logger.warning("No potential event elements found inside calendar")
                            # The calendar structure is there but no events found - could be empty calendar
                            return True
                
                logger.info(f"Successfully navigated to timetable page, found {len(events)} events")
                return True
                
            except TimeoutException:
                logger.error("Calendar element not found")
                self._save_debug_screenshot("calendar_not_found")
                return False
            
        except Exception as e:
            logger.error(f"Error navigating to timetable: {str(e)}")
            if self.driver:
                self._save_debug_screenshot("navigation_exception")
            return False
            
    def close(self):
        """Close the browser session."""
        if self.driver:
            self.driver.quit()
            self.driver = None 