import sys
import os
import json
import pytest
from pathlib import Path
from dotenv import load_dotenv

# "from pages.xxx import" works with tests/ on the path
sys.path.insert(0, str(Path(__file__).parent))
# "from base_page import BasePage" works with tests/pages/ on the path
sys.path.insert(0, str(Path(__file__).parent / "pages"))

# Load project .env so APP_URL is available to page objects
load_dotenv(str(Path(__file__).parent.parent / ".env"), override=True)

_TEST_DATA_FILE = Path(__file__).parent / "test_data.json"


@pytest.fixture(scope="session")
def test_data() -> dict:
    if _TEST_DATA_FILE.exists():
        return json.loads(_TEST_DATA_FILE.read_text(encoding="utf-8"))
    return {"app": {}, "suites": {}}


@pytest.fixture(autouse=True)
def set_timeouts(page):
    page.set_default_navigation_timeout(60_000)
    page.set_default_timeout(60_000)
