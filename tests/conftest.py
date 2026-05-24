import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Make "from pages.xxx import" and "from base_page import" work
sys.path.insert(0, str(Path(__file__).parent))

# Load project .env so APP_URL is available to page objects
load_dotenv(str(Path(__file__).parent.parent / ".env"), override=True)
