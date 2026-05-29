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

_TEST_DATA_FILE       = Path(__file__).parent / "test_data.json"
_FAILURE_ARTIFACTS_DIR = Path(__file__).parent / "failure_artifacts"


@pytest.fixture(scope="session")
def test_data() -> dict:
    if _TEST_DATA_FILE.exists():
        return json.loads(_TEST_DATA_FILE.read_text(encoding="utf-8"))
    return {"app": {}, "suites": {}}


@pytest.fixture(autouse=True)
def set_timeouts(page):
    page.set_default_navigation_timeout(60_000)
    page.set_default_timeout(60_000)


# ─── Failure artifact capture ─────────────────────────────────────────────────
# Saves a screenshot + DOM snapshot on any test failure so the triage agent
# can inspect the page state rather than guessing from the traceback alone.

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)


@pytest.fixture(autouse=True)
def capture_failure_artifacts(request, page):
    yield
    rep = getattr(request.node, "rep_call", None)
    if rep is None or not rep.failed:
        return
    _FAILURE_ARTIFACTS_DIR.mkdir(exist_ok=True)
    test_name = request.node.name
    try:
        page.screenshot(
            path=str(_FAILURE_ARTIFACTS_DIR / f"{test_name}.png"),
            full_page=True,
        )
    except Exception:
        pass
    try:
        (_FAILURE_ARTIFACTS_DIR / f"{test_name}.html").write_text(
            page.content()[:50_000], encoding="utf-8"
        )
    except Exception:
        pass
