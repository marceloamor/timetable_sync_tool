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

from ..config import CELCAT_USERNAME, CELCAT_PASSWORD, CELCAT_BASE_URL, STUDENT_ID

logger = logging.getLogger(__name__)

class CelcatAuth:
    """Handle authentication with CELCAT timetable system."""
    
    def __init__(self, headless=True):
        """Initialize the CELCAT authentication handler.
        
        Args:
            headless (bool): Whether to run the browser in headless mode.
        """
        self.headless = headless
        self.driver = None
        
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
            self.driver.get(f"{CELCAT_BASE_URL}/login")
            time.sleep(2)  # Give the page time to load
            
            # Print the current URL for debugging
            logger.info(f"Current URL: {self.driver.current_url}")
            
            # Wait for and fill in the login form
            try:
                # Try different possible selectors for the username field
                username_selectors = [
                    (By.NAME, "username"),
                    (By.ID, "username"),
                    (By.CSS_SELECTOR, "input[type='text']"),
                    (By.CSS_SELECTOR, "input[type='email']")
                ]
                
                username_field = None
                for by, selector in username_selectors:
                    try:
                        username_field = WebDriverWait(self.driver, 5).until(
                            EC.presence_of_element_located((by, selector))
                        )
                        if username_field:
                            break
                    except TimeoutException:
                        continue
                
                if not username_field:
                    logger.error("Could not find username field")
                    return False
                
                # Clear and fill username
                username_field.clear()
                username_field.send_keys(CELCAT_USERNAME)
                time.sleep(1)  # Small delay between fields
                
                # Find and fill password field
                password_field = self.driver.find_element(By.NAME, "password")
                password_field.clear()
                password_field.send_keys(CELCAT_PASSWORD)
                time.sleep(1)  # Small delay before submit
                
                # Try to find and click the submit button
                submit_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
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
            timetable_url = f"{CELCAT_BASE_URL}/cal?vt=agendaWeek&dt={date_str}&et=student&fid0={STUDENT_ID}"
            
            logger.info(f"Navigating to timetable URL: {timetable_url}")
            self.driver.get(timetable_url)
            time.sleep(5)  # Give the page time to load
            
            # Check if we're on the timetable page
            if "cal" not in self.driver.current_url:
                logger.error("Failed to navigate to timetable page")
                return False
                
            logger.info("Successfully navigated to timetable page")
            return True
            
        except Exception as e:
            logger.error(f"Error navigating to timetable: {str(e)}")
            return False
            
    def close(self):
        """Close the browser session."""
        if self.driver:
            self.driver.quit()
            self.driver = None 