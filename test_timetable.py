"""
Test script for inspecting CELCAT timetable structure.
"""

import logging
import time
from datetime import datetime
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
        print("Opening browser and navigating to CELCAT...")
        success = auth.login()
        
        if success:
            print("Successfully logged in!")
            
            # Try to navigate to the timetable
            print("Navigating to timetable view...")
            timetable_success = auth.navigate_to_timetable(datetime.now())
            
            if timetable_success:
                print("Successfully loaded timetable!")
                print("\nPlease inspect the timetable page in your browser.")
                print("Look for:")
                print("1. The HTML structure of timetable events")
                print("2. Class names or IDs used for events")
                print("3. How event details (time, location, etc.) are structured")
                print("\nThe browser will stay open for 60 seconds for inspection...")
                time.sleep(60)  # Keep browser open longer for inspection
            else:
                print("Failed to load timetable.")
                print("Browser will stay open for 30 seconds for inspection...")
                time.sleep(30)
        else:
            print("Login failed. Browser will stay open for 30 seconds for inspection...")
            time.sleep(30)
            
    except Exception as e:
        print(f"An error occurred: {e}")
        print("Browser will stay open for 30 seconds for inspection...")
        time.sleep(30)
    finally:
        auth.close()

if __name__ == "__main__":
    main() 