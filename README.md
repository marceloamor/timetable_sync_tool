# CELCAT to Google Calendar Sync

A Python tool to automatically sync your university timetable from CELCAT (New College of the Humanities/Northeastern London) to Google Calendar.

## Features

- Automated login to CELCAT timetable system
- Extraction of timetable data using web scraping
- Export to .ics format or direct sync to Google Calendar
- Configurable settings for personal use
- Secure credential management

## Setup

1. Clone this repository
2. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Create a `.env` file with your credentials:
   ```
   CELCAT_USERNAME=your_username
   CELCAT_PASSWORD=your_password
   STUDENT_ID=your_student_id
   ```

## Usage

[Usage instructions will be added as the project develops]

## Project Structure

```
timetable_sync_tool/
├── src/
│   ├── __init__.py
│   ├── celcat/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   └── scraper.py
│   ├── calendar/
│   │   ├── __init__.py
│   │   ├── google_calendar.py
│   │   └── ics_exporter.py
│   └── config.py
├── tests/
│   └── __init__.py
├── .env.example
├── .gitignore
├── README.md
└── requirements.txt
```

## Development Status

🚧 This project is currently under development. 🚧

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

[License information to be added] 