import re
from pages.base_page import BasePage
from playwright.sync_api import Page, expect

class UserLoginPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)
        self.username_input = self.page.get_by_role("textbox", name="Username")
        self.password_input = self.page.get_by_role("textbox", name="Password")
        self.login_button = self.page.get_by_role("button", name="Login")
        self.error_message = self.page.locator(".oxd-alert-content")

    def login(self):
        self.goto_app()

    def navigate(self):
        self.page.wait_for_load_state("networkidle")

    def provide_username(self, username: str):
        self.username_input.fill(username)

    def provide_password(self, password: str):
        self.password_input.fill(password)

    def attempt_login(self):
        self.login_button.click()
        self.page.wait_for_load_state("networkidle")

    def assert_error_message(self):
        expect(self.page.locator(".oxd-input-field-error-message").first).to_be_visible()

    def assert_on_dashboard(self):
        expect(self.page).to_have_url(re.compile(r".*/dashboard/index"))

    def assert_access_denied(self):
        expect(self.error_message).to_be_visible()

    def assert_session_expired(self):
        expect(self.error_message).to_be_visible()

    def assert_invalid_credentials(self):
        expect(self.error_message).to_be_visible()