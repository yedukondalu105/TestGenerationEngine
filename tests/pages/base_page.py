import os
from playwright.sync_api import Page, expect


class BasePage:
    APP_URL = os.getenv("PLAYWRIGHT_APP_URL", "")

    def __init__(self, page: Page):
        self.page = page

    def goto_app(self) -> None:
        """Navigate to the app login page without logging in."""
        self.page.goto(self.APP_URL)
        self.page.wait_for_load_state("networkidle")

    def login(self, username: str = "Admin", password: str = "admin123") -> None:
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
