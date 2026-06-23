import os

MASSIVE_API_KEY = os.environ.get("MASSIVE_API_KEY", "")
MASSIVE_BASE_URL = os.environ.get("MASSIVE_BASE_URL", "https://api.massive.com")
MASSIVE_POLL_INTERVAL_SECONDS = float(os.environ.get("MASSIVE_POLL_INTERVAL_SECONDS", "15"))
