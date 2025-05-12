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
import logging
import time
from datetime import datetime

from config import CELCAT_USERNAME, CELCAT_PASSWORD, CELCAT_BASE_URL

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
        if not student_id:
            raise ValueError("student_id is required")
            
        self.headless = headless
        self.driver = None
        self.base_url = base_url or CELCAT_BASE_URL
        self.username = username or CELCAT_USERNAME
        self.password = password or CELCAT_PASSWORD
        self.student_id = student_id
        
    def setup_driver(self):
        """Set up the Selenium WebDriver with appropriate options."""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless=new")
        
        # WSL-specific options
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        
        # Additional options for stability
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-software-rasterizer")
        chrome_options.add_argument("--disable-features=VizDisplayCompositor")
        
        # Set binary location explicitly for WSL
        chrome_options.binary_location = "/usr/bin/google-chrome-stable"
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.implicitly_wait(10)  # Add implicit wait
        
    def login(self):
        """Log in to the CELCAT timetable system.
        
        Returns:
            bool: True if login was successful, False otherwise.
        """
        try:
            if not self.driver:
                self.setup_driver()
                
            # Navigate to the login page
            self.driver.get(f"{self.base_url}/login")
            time.sleep(2)  # Give the page time to load
            
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
                
                # Find and click the submit button
                submit_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit'], input[type='submit']")
                submit_button.click()
                
                # Wait for successful login
                time.sleep(5)  # Give the page time to process login
                
                # Check if we're still on the login page
                if "login" in self.driver.current_url.lower():
                    logger.error("Still on login page after submission")
                    return False
                
                logger.info("Successfully logged in to CELCAT")
                return True
                
            except (TimeoutException, NoSuchElementException) as e:
                logger.error(f"Error during login process: {str(e)}")
                return False
            
        except Exception as e:
            logger.error(f"Failed to log in to CELCAT: {str(e)}")
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
            
            # Wait for the calendar to be present
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "calendar"))
                )
                
                # Check if we can see any events
                events = self.driver.find_elements(By.CLASS_NAME, "fc-event")
                if not events:
                    logger.warning("No events found in calendar view")
                    # Try to refresh the page
                    self.driver.refresh()
                    time.sleep(5)
                    events = self.driver.find_elements(By.CLASS_NAME, "fc-event")
                    if not events:
                        logger.error("Still no events found after refresh")
                        return False
                
                logger.info("Successfully navigated to timetable page")
                return True
                
            except TimeoutException:
                logger.error("Calendar element not found")
                return False
            
        except Exception as e:
            logger.error(f"Error navigating to timetable: {str(e)}")
            return False
            
    def close(self):
        """Close the browser session."""
        if self.driver:
            self.driver.quit()
            self.driver = None 