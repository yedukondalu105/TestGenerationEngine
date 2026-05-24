import sys
import os
import pytest
from pathlib import Path
from dotenv import load_dotenv

# "from pages.xxx import" works with tests/ on the path
sys.path.insert(0, str(Path(__file__).parent))
# "from base_page import BasePage" works with tests/pages/ on the path
sys.path.insert(0, str(Path(__file__).parent / "pages"))

# Load project .env so APP_URL is available to page objects
load_dotenv(str(Path(__file__).parent.parent / ".env"), override=True)


@pytest.fixture(autouse=True)
def set_timeouts(page):
    page.set_default_navigation_timeout(60_000)
    page.set_default_timeout(60_000)
