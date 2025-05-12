"""
Configuration module for the CELCAT to Google Calendar sync tool.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Configuration class for the application."""
    
    def __init__(self):
        """Initialize configuration from environment variables."""
        # CELCAT Configuration
        self.CELCAT_USERNAME = os.getenv("CELCAT_USERNAME")
        self.CELCAT_PASSWORD = os.getenv("CELCAT_PASSWORD")
        self.STUDENT_ID = os.getenv("STUDENT_ID")
        self.CELCAT_BASE_URL = "https://timetable.nulondon.ac.uk"
        
        # Google Calendar Configuration
        self.GOOGLE_CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID")
        self.GOOGLE_CREDENTIALS_PATH = os.getenv("GOOGLE_CREDENTIALS_PATH")
        
        # Validate configuration
        self.validate()
        
    def validate(self):
        """Validate that all required environment variables are set."""
        required_vars = {
            "CELCAT_USERNAME": self.CELCAT_USERNAME,
            "CELCAT_PASSWORD": self.CELCAT_PASSWORD,
            "STUDENT_ID": self.STUDENT_ID,
        }
        
        missing_vars = [var for var, value in required_vars.items() if not value]
        
        if missing_vars:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing_vars)}"
            )
            
    def setup_directories(self):
        """Create necessary directories for the application."""
        Path("logs").mkdir(exist_ok=True)
        Path("data").mkdir(exist_ok=True)

# For backward compatibility
CELCAT_USERNAME = os.getenv("CELCAT_USERNAME")
CELCAT_PASSWORD = os.getenv("CELCAT_PASSWORD")
STUDENT_ID = os.getenv("STUDENT_ID")
CELCAT_BASE_URL = "https://timetable.nulondon.ac.uk"
GOOGLE_CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID")
GOOGLE_CREDENTIALS_PATH = os.getenv("GOOGLE_CREDENTIALS_PATH") 