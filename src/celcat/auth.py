"""
CELCAT authentication module.
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import logging

from ..config import CELCAT_USERNAME, CELCAT_PASSWORD, CELCAT_BASE_URL

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
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        
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
            
            # Wait for and fill in the login form
            username_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "username"))
            )
            password_field = self.driver.find_element(By.NAME, "password")
            
            username_field.send_keys(CELCAT_USERNAME)
            password_field.send_keys(CELCAT_PASSWORD)
            
            # Submit the form
            password_field.submit()
            
            # Wait for successful login
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "logged-in"))
            )
            
            logger.info("Successfully logged in to CELCAT")
            return True
            
        except Exception as e:
            logger.error(f"Failed to log in to CELCAT: {str(e)}")
            return False
            
    def close(self):
        """Close the browser session."""
        if self.driver:
            self.driver.quit()
            self.driver = None 