# YouTube Comment Fetcher

Fetch comments from a specific YouTube channel across another channel's video history.

## Quick Start

1. Get a YouTube Data API v3 key from [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Open `main.py` and fill in the **USER CONFIGURATION** section at the top
3. Install dependency: `pip install requests`
4. Run: `python main.py`

## Output

- `comment_results_*.txt` — Human-readable report
- `comment_results_*.json` — Structured data

## Requirements

- Python 3.7+
- `requests` library
- YouTube Data API v3 access
