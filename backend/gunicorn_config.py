import os
from dotenv import load_dotenv

load_dotenv()

port = os.getenv("BACKEND_PORT", "5001")  # Default to 5001 if not set
bind = f"0.0.0.0:{port}"
workers = 4  # Number of worker processes
timeout = 120  # Request timeout in seconds
loglevel = "info"  # Logging level
