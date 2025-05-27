"""
Configuration module for the CELCAT to Google Calendar sync tool.
"""

import os
from pathlib import Path
from dotenv import load_dotenv, find_dotenv
import logging

logger = logging.getLogger(__name__)

class Config:
    """Configuration class for the application."""
    
    def __init__(self):
        """Initialize configuration from environment variables."""
        # Load environment variables from .env file
        env_path = find_dotenv()
        if not env_path:
            logger.warning("No .env file found in any parent directory")
            env_path = Path(__file__).parent.parent / '.env'
            if not env_path.exists():
                logger.warning(f".env file not found at {env_path}")
            else:
                logger.info(f"Found .env file at {env_path}")
        else:
            logger.info(f"Found .env file at {env_path}")
            
        # Load the environment variables
        load_dotenv(env_path, override=True)
        
        # CELCAT Configuration
        self.CELCAT_USERNAME = os.getenv("CELCAT_USERNAME")
        self.CELCAT_PASSWORD = os.getenv("CELCAT_PASSWORD")
        self.STUDENT_ID = os.getenv("STUDENT_ID")
        self.CELCAT_BASE_URL = "https://timetable.nulondon.ac.uk"
        
        # Google Calendar Configuration
        self.GOOGLE_CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID")
        self.GOOGLE_CREDENTIALS_PATH = os.getenv("GOOGLE_CREDENTIALS_PATH")
        
        # Log configuration status (without sensitive data)
        self._log_config_status()
        
        # Validate configuration
        self.validate()
        
    def _log_config_status(self):
        """Log the status of configuration loading."""
        logger.info("Configuration status:")
        logger.info(f"  CELCAT_USERNAME: {'Set' if self.CELCAT_USERNAME else 'Not set'}")
        logger.info(f"  CELCAT_PASSWORD: {'Set' if self.CELCAT_PASSWORD else 'Not set'}")
        logger.info(f"  STUDENT_ID: {'Set' if self.STUDENT_ID else 'Not set'}")
        if self.STUDENT_ID:
            logger.info(f"  STUDENT_ID value: {self.STUDENT_ID}")
        logger.info(f"  GOOGLE_CALENDAR_ID: {'Set' if self.GOOGLE_CALENDAR_ID else 'Not set'}")
        logger.info(f"  GOOGLE_CREDENTIALS_PATH: {'Set' if self.GOOGLE_CREDENTIALS_PATH else 'Not set'}")
        
    def validate(self):
        """Validate that all required environment variables are set."""
        required_vars = {
            "CELCAT_USERNAME": self.CELCAT_USERNAME,
            "CELCAT_PASSWORD": self.CELCAT_PASSWORD,
            "STUDENT_ID": self.STUDENT_ID,
        }
        
        missing_vars = [var for var, value in required_vars.items() if not value]
        
        if missing_vars:
            error_msg = f"Missing required environment variables: {', '.join(missing_vars)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
            
    def setup_directories(self):
        """Create necessary directories for the application."""
        Path("logs").mkdir(exist_ok=True)
        Path("data").mkdir(exist_ok=True)
        Path("debug").mkdir(exist_ok=True)

# Load environment variables at module level
env_path = find_dotenv()
if env_path:
    load_dotenv(env_path, override=True)
else:
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path, override=True)
    else:
        logger.warning("No .env file found")

# For backward compatibility
CELCAT_USERNAME = os.getenv("CELCAT_USERNAME")
CELCAT_PASSWORD = os.getenv("CELCAT_PASSWORD")
STUDENT_ID = os.getenv("STUDENT_ID")
CELCAT_BASE_URL = "https://timetable.nulondon.ac.uk"
GOOGLE_CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID")
GOOGLE_CREDENTIALS_PATH = os.getenv("GOOGLE_CREDENTIALS_PATH")

def validate_config():
    """Validate that all required environment variables are set."""
    required_vars = {
        "CELCAT_USERNAME": CELCAT_USERNAME,
        "CELCAT_PASSWORD": CELCAT_PASSWORD,
        "STUDENT_ID": STUDENT_ID,
    }
    
    missing_vars = [var for var, value in required_vars.items() if not value]
    
    if missing_vars:
        error_msg = f"Missing required environment variables: {', '.join(missing_vars)}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    # Create debug directory
    Path("debug").mkdir(exist_ok=True)
    
    return True 