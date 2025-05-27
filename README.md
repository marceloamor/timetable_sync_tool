# CELCAT to Google Calendar Sync Tool

This tool automatically syncs your university timetable from CELCAT to Google Calendar.

## Features

- Automated login to CELCAT timetable system
- Extraction of timetable data using web scraping
- Support for fetching multiple weeks of events
- Direct sync to Google Calendar
- Configurable settings for personal use
- Secure credential management

## Setup

1. Create a virtual environment and activate it:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the root directory with the following content:
```env
# CELCAT Configuration
CELCAT_USERNAME=your_username
CELCAT_PASSWORD=your_password
STUDENT_ID=your_student_id

# Google Calendar Configuration
GOOGLE_CALENDAR_ID=your_calendar_id
GOOGLE_CREDENTIALS_PATH=path/to/credentials.json
```

Replace the placeholder values with your actual credentials:
- `CELCAT_USERNAME`: Your CELCAT username
- `CELCAT_PASSWORD`: Your CELCAT password
- `STUDENT_ID`: Your student ID (required for accessing your timetable)
- `GOOGLE_CALENDAR_ID`: Your Google Calendar ID (optional, defaults to 'primary')
- `GOOGLE_CREDENTIALS_PATH`: Path to your Google Calendar API credentials JSON file

## Usage

### Google Calendar Setup

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable the Google Calendar API
4. Create OAuth 2.0 credentials
5. Download the credentials JSON file
6. Add the path to this file in your `.env` file as `GOOGLE_CREDENTIALS_PATH`

### Running the Tool

The tool provides several commands:

1. **Fetch events only**:
```bash
python main.py fetch --weeks 4
```

2. **Sync events from a file to Google Calendar**:
```bash
python main.py sync --file data/events_20250527_114210.json
```

3. **Fetch and sync in one go**:
```bash
python main.py all --weeks 4
```

Additional options:
- `--headless`: Run in headless mode (no browser UI)
- `--calendar-id`: Override the Google Calendar ID from the .env file
- `--credentials`: Override the Google credentials path from the .env file
- `--output`: Specify a custom output file name (for the fetch command)

## Project Structure

```
.
├── src/
│   ├── celcat/            # CELCAT integration
│   │   ├── auth.py        # Authentication with CELCAT
│   │   └── scraper.py     # Timetable scraping
│   ├── google/            # Google API integration
│   │   └── calendar.py    # Google Calendar integration
│   └── config.py          # Configuration management
├── data/                  # Exported event data
├── debug/                 # Debug files (HTML, screenshots)
├── logs/                  # Log files
├── main.py                # Main script
├── test_scraper.py        # Test script for scraper
├── test_calendar.py       # Test script for calendar integration
├── .env                   # Environment variables (create this)
├── requirements.txt       # Python dependencies
└── README.md              # This file
```

## Testing

You can test individual components:

1. **Test the scraper only**:
```bash
python test_scraper.py --weeks 1
```

2. **Test Google Calendar integration**:
```bash
python test_calendar.py --file data/events_20250527_114210.json
```

## Troubleshooting

1. If you see "student_id not found" errors:
   - Make sure your `.env` file exists and contains the `STUDENT_ID` variable
   - Verify that the value is correct

2. If you see "Calendar element not found" errors:
   - Verify that you can access your timetable manually in the browser
   - Check that your student ID is correct
   - Check the debug files in the `debug/` directory for more information

3. If you have issues with Google Calendar:
   - Ensure your credentials file is valid and has the right permissions
   - Check that you've enabled the Google Calendar API in your Google Cloud project
   - Look at the logs in the `logs/` directory

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request
