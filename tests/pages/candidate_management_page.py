import re
from pages.base_page import BasePage
from playwright.sync_api import Page, expect

class CandidateManagementPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)
        self.add_candidate_button = self.page.get_by_role("button", name="Add")
        self.first_name_input = self.page.locator("input.oxd-input").nth(0)
        self.last_name_input = self.page.locator("input.oxd-input").nth(1)
        self.email_input = self.page.locator("input.oxd-input").nth(2)
        self.resume_upload_input = self.page.locator("input[type='file']")
        self.save_button = self.page.get_by_role("button", name="Save")
        self.success_toast = self.page.locator(".oxd-toast--success")
        self.error_message = self.page.locator(".oxd-alert-content")
        self.required_field_error = self.page.locator(".oxd-input-field-error-message").first

    def navigate(self):
        self.navigate_to("Recruitment")
        self.page.get_by_role("link", name="Candidates").first.click()
        self.page.wait_for_load_state("networkidle")

    def add_candidate(self, first_name: str, last_name: str, email: str, resume_path: str):
        self.add_candidate_button.click()
        self.first_name_input.fill(first_name)
        self.last_name_input.fill(last_name)
        self.email_input.fill(email)
        self.resume_upload_input.set_input_files(resume_path)
        self.save_button.click()
        self.page.wait_for_load_state("networkidle")

    def upload_resume(self, resume_path: str):
        self.resume_upload_input.set_input_files(resume_path)
        self.save_button.click()
        self.page.wait_for_load_state("networkidle")

    def assert_success_toast(self):
        expect(self.success_toast).to_be_visible()

    def assert_error_message(self):
        expect(self.error_message).to_be_visible()

    def assert_invalid_credentials(self):
        expect(self.error_message).to_be_visible()

    def assert_required_field_error(self):
        expect(self.required_field_error).to_be_visible()

    def assert_on_dashboard(self):
        expect(self.page).to_have_url(re.compile(r".*/dashboard/index"))