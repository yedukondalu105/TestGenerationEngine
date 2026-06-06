import re
from pages.base_page import BasePage
from playwright.sync_api import Page, expect

class UserAndRoleManagementPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)
        self.nav_link_admin = self.page.get_by_role("link", name="Admin").first
        self.add_user_button = self.page.get_by_role("button", name="Add")
        self.username_input = self.page.locator("input.oxd-input").nth(0)
        self.password_input = self.page.locator("input.oxd-input").nth(1)
        self.confirm_password_input = self.page.locator("input.oxd-input").nth(2)
        self.employee_name_autocomplete = self.page.locator(".oxd-autocomplete-text-input input").nth(0)
        self.role_dropdown = self.page.locator(".oxd-select-text").nth(0)
        self.status_dropdown = self.page.locator(".oxd-select-text").nth(1)
        self.search_button = self.page.get_by_role("button", name="Search")
        self.save_button = self.page.get_by_role("button", name="Save")
        self.toast_success = self.page.locator(".oxd-toast--success")
        self.alert_content = self.page.locator(".oxd-alert-content")
        self.input_field_error_message = self.page.locator(".oxd-input-field-error-message").first

    def navigate(self):
        self.navigate_to("Admin")
        self.page.wait_for_load_state("networkidle")

    def add_record(self, username, password, confirm_password, employee_name, role, status):
        self.add_user_button.click()
        self.username_input.fill(username)
        self.password_input.fill(password)
        self.confirm_password_input.fill(confirm_password)
        self.employee_name_autocomplete.fill(employee_name)
        self.page.locator(".oxd-autocomplete-option", has_text=employee_name).first.click()
        self.role_dropdown.click()
        self.page.get_by_role("option", name=role).click()
        self.status_dropdown.click()
        self.page.get_by_role("option", name=status).click()
        self.save_button.click()
        self.page.wait_for_load_state("networkidle")

    def search(self, username=None, role=None, status=None):
        if username:
            self.username_input.fill(username)
        if role:
            self.role_dropdown.click()
            self.page.get_by_role("option", name=role).click()
        if status:
            self.status_dropdown.click()
            self.page.get_by_role("option", name=status).click()
        self.search_button.click()
        self.page.wait_for_load_state("networkidle")

    def edit_record(self, row_index, new_username=None, new_role=None, new_status=None):
        self.page.locator(".oxd-table-cell-actions .oxd-icon-button").nth(row_index).click()
        if new_username:
            self.username_input.fill(new_username)
        if new_role:
            self.role_dropdown.click()
            self.page.get_by_role("option", name=new_role).click()
        if new_status:
            self.status_dropdown.click()
            self.page.get_by_role("option", name=new_status).click()
        self.save_button.click()
        self.page.wait_for_load_state("networkidle")

    def delete_record(self, row_index):
        self.page.locator(".oxd-table-cell-actions").nth(row_index).click()
        self.page.get_by_role("button", name="Yes, Delete").click()
        self.page.wait_for_load_state("networkidle")

    def assert_success_toast(self):
        expect(self.toast_success).to_be_visible()

    def assert_error_message(self):
        expect(self.input_field_error_message).to_be_visible()

    def assert_invalid_credentials(self):
        expect(self.alert_content).to_be_visible()

    def assert_on_dashboard(self):
        expect(self.page).to_have_url(re.compile(r".*/dashboard/index"))