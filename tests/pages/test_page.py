import re
from pages.base_page import BasePage
from playwright.sync_api import Page, expect

class TestPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)
        self.username_input = self.page.get_by_role("textbox", name="Username")
        self.password_input = self.page.get_by_role("textbox", name="Password")
        self.login_button = self.page.get_by_role("button", name="Login")
        self.alert_content = self.page.locator(".oxd-alert-content")
        self.toast_success = self.page.locator(".oxd-toast--success")

    def login(self):
        self.goto_app()

    def navigate(self):
        self.page.wait_for_load_state("networkidle")

    def provide_username(self, text: str):
        self.username_input.fill(text)

    def provide_password(self, text: str):
        self.password_input.fill(text)

    def attempt_login(self):
        self.login_button.click()
        self.page.wait_for_load_state("networkidle")

    def assert_on_dashboard(self):
        expect(self.page).to_have_url(re.compile(r".*/dashboard/index"))

    def assert_error_message(self):
        expect(self.alert_content).to_be_visible()

    def assert_invalid_credentials(self):
        expect(self.alert_content).to_be_visible()

    def assert_session_expired(self):
        expect(self.alert_content).to_be_visible()

    def assert_access_denied(self):
        expect(self.alert_content).to_be_visible()