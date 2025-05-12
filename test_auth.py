"""
Test script for CELCAT authentication.
"""

import logging
from src.celcat.auth import CelcatAuth
from src.config import validate_config

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    # Validate configuration
    try:
        validate_config()
    except ValueError as e:
        print(f"Configuration error: {e}")
        return

    # Initialize auth with visible browser for testing
    auth = CelcatAuth(headless=False)
    
    try:
        print("Attempting to log in to CELCAT...")
        success = auth.login()
        
        if success:
            print("Successfully logged in!")
            # Keep the browser open for inspection
            input("Press Enter to close the browser...")
        else:
            print("Failed to log in. Check the logs for details.")
            
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        auth.close()

if __name__ == "__main__":
    main() 