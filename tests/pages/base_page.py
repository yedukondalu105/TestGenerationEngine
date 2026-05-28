import os
import json
from pathlib import Path
from playwright.sync_api import Page, expect

_TD_FILE = Path(__file__).parent.parent / "test_data.json"
_TD = json.loads(_TD_FILE.read_text(encoding="utf-8")) if _TD_FILE.exists() else {}
_ADMIN = _TD.get("app", {}).get("admin", {})
_DEFAULT_USERNAME = _ADMIN.get("username", "Admin")
_DEFAULT_PASSWORD = _ADMIN.get("password", "admin123")


class BasePage:
    APP_URL = os.getenv("PLAYWRIGHT_APP_URL", "")

    def __init__(self, page: Page):
        self.page = page

    def goto_app(self) -> None:
        self.page.goto(self.APP_URL)
        self.page.wait_for_load_state("networkidle")

    def login(self, username: str = _DEFAULT_USERNAME, password: str = _DEFAULT_PASSWORD) -> None:
        """Full login: navigate → fill credentials → submit → wait for dashboard.
        Override in subclasses that test the login page itself."""
        self.goto_app()
        self.page.get_by_placeholder("Username").fill(username)
        self.page.get_by_placeholder("Password").fill(password)
        self.page.get_by_role("button", name="Login").click()
        self.page.wait_for_url("**/dashboard/index")

    def navigate_to(self, menu_item: str) -> None:
        self.page.get_by_role("link", name=menu_item).first.click()
        self.page.wait_for_load_state("networkidle")
