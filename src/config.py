"""
Configuration module for the CELCAT to Google Calendar sync tool.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# CELCAT Configuration
CELCAT_USERNAME = os.getenv("CELCAT_USERNAME")
CELCAT_PASSWORD = os.getenv("CELCAT_PASSWORD")
STUDENT_ID = os.getenv("STUDENT_ID")
CELCAT_BASE_URL = "https://timetable.nulondon.ac.uk"

# Google Calendar Configuration
GOOGLE_CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID")
GOOGLE_CREDENTIALS_PATH = os.getenv("GOOGLE_CREDENTIALS_PATH")

# Validate required environment variables
def validate_config():
    """Validate that all required environment variables are set."""
    required_vars = {
        "CELCAT_USERNAME": CELCAT_USERNAME,
        "CELCAT_PASSWORD": CELCAT_PASSWORD,
        "STUDENT_ID": STUDENT_ID,
    }
    
    missing_vars = [var for var, value in required_vars.items() if not value]
    
    if missing_vars:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing_vars)}"
        )

# Create necessary directories
def setup_directories():
    """Create necessary directories for the application."""
    Path("logs").mkdir(exist_ok=True)
    Path("data").mkdir(exist_ok=True) 