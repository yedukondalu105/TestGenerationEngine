import pytest
from playwright.sync_api import Page
from pages.user_and_role_management_page import UserAndRoleManagementPage

def test_create_new_user_with_valid_details(page: Page, test_data: dict):
    td = test_data["suites"]["user_and_role_management"]
    obj = UserAndRoleManagementPage(page)
    obj.login()
    obj.navigate()
    obj.add_record(td["valid_username"], td["max_length_password"], td["max_length_password"], "John Doe", "Admin", "Enabled")
    obj.assert_success_toast()

def test_assign_role_during_user_creation(page: Page, test_data: dict):
    td = test_data["suites"]["user_and_role_management"]
    obj = UserAndRoleManagementPage(page)
    obj.login()
    obj.navigate()
    obj.add_record(td["valid_username"], td["max_length_password"], td["max_length_password"], "John Doe", "Admin", "Enabled")
    obj.assert_success_toast()

def test_search_existing_users_by_username(page: Page, test_data: dict):
    td = test_data["suites"]["user_and_role_management"]
    obj = UserAndRoleManagementPage(page)
    obj.login()
    obj.navigate()
    obj.search(username=td["valid_username"])
    obj.assert_success_toast()

def test_search_users_by_role(page: Page, test_data: dict):
    td = test_data["suites"]["user_and_role_management"]
    obj = UserAndRoleManagementPage(page)
    obj.login()
    obj.navigate()
    obj.search(role="Admin")
    obj.assert_success_toast()

def test_search_users_by_status(page: Page, test_data: dict):
    td = test_data["suites"]["user_and_role_management"]
    obj = UserAndRoleManagementPage(page)
    obj.login()
    obj.navigate()
    obj.search(status="Enabled")
    obj.assert_success_toast()

def test_disable_a_user(page: Page, test_data: dict):
    td = test_data["suites"]["user_and_role_management"]
    obj = UserAndRoleManagementPage(page)
    obj.login()
    obj.navigate()
    obj.edit_record(0, new_status="Disabled")
    obj.assert_success_toast()

def test_access_admin_module_after_authentication(page: Page, test_data: dict):
    td = test_data["suites"]["user_and_role_management"]
    obj = UserAndRoleManagementPage(page)
    obj.login()
    obj.navigate()
    obj.assert_on_dashboard()

def test_fail_user_creation_if_employee_does_not_exist(page: Page, test_data: dict):
    td = test_data["suites"]["user_and_role_management"]
    obj = UserAndRoleManagementPage(page)
    obj.login()
    obj.navigate()
    obj.add_record(td["valid_username"], td["max_length_password"], td["max_length_password"], td["non_existent_employee"], "Admin", "Enabled")
    obj.assert_error_message()

def test_fail_creation_for_duplicate_username(page: Page, test_data: dict):
    td = test_data["suites"]["user_and_role_management"]
    obj = UserAndRoleManagementPage(page)
    obj.login()
    obj.navigate()
    obj.add_record(td["existing_user"], td["max_length_password"], td["max_length_password"], "John Doe", "Admin", "Enabled")
    obj.assert_error_message()

def test_fail_creation_for_invalid_password(page: Page, test_data: dict):
    td = test_data["suites"]["user_and_role_management"]
    obj = UserAndRoleManagementPage(page)
    obj.login()
    obj.navigate()
    obj.add_record(td["valid_username"], td["invalid_format"], td["invalid_format"], "John Doe", "Admin", "Enabled")
    obj.assert_error_message()

@pytest.mark.skip(reason="Session expiry not available")
def test_reject_access_to_admin_module_without_authentication(page: Page, test_data: dict):
    pass

def test_fail_disabling_a_user_that_does_not_exist(page: Page, test_data: dict):
    td = test_data["suites"]["user_and_role_management"]
    obj = UserAndRoleManagementPage(page)
    obj.login()
    obj.navigate()
    obj.delete_record(999)  # Assuming 999 is a non-existent index
    obj.assert_error_message()

def test_fail_user_creation_for_missing_mandatory_fields(page: Page, test_data: dict):
    td = test_data["suites"]["user_and_role_management"]
    obj = UserAndRoleManagementPage(page)
    obj.login()
    obj.navigate()
    obj.add_record(td["empty_value"], td["empty_value"], td["empty_value"], td["empty_value"], "Admin", "Enabled")
    obj.assert_error_message()

def test_fail_enabling_a_user_that_is_already_disabled(page: Page, test_data: dict):
    td = test_data["suites"]["user_and_role_management"]
    obj = UserAndRoleManagementPage(page)
    obj.login()
    obj.navigate()
    obj.edit_record(0, new_status="Enabled")
    obj.assert_error_message()

def test_error_for_empty_employee_name(page: Page, test_data: dict):
    td = test_data["suites"]["user_and_role_management"]
    obj = UserAndRoleManagementPage(page)
    obj.login()
    obj.navigate()
    obj.add_record(td["valid_username"], td["max_length_password"], td["max_length_password"], td["empty_value"], "Admin", "Enabled")
    obj.assert_error_message()

def test_error_for_empty_username(page: Page, test_data: dict):
    td = test_data["suites"]["user_and_role_management"]
    obj = UserAndRoleManagementPage(page)
    obj.login()
    obj.navigate()
    obj.add_record(td["empty_value"], td["max_length_password"], td["max_length_password"], "John Doe", "Admin", "Enabled")
    obj.assert_error_message()

def test_error_for_password_not_meeting_security_policies(page: Page, test_data: dict):
    td = test_data["suites"]["user_and_role_management"]
    obj = UserAndRoleManagementPage(page)
    obj.login()
    obj.navigate()
    obj.add_record(td["valid_username"], td["short_password"], td["short_password"], "John Doe", "Admin", "Enabled")
    obj.assert_error_message()

def test_error_for_username_that_is_not_unique(page: Page, test_data: dict):
    td = test_data["suites"]["user_and_role_management"]
    obj = UserAndRoleManagementPage(page)
    obj.login()
    obj.navigate()
    obj.add_record(td["existing_user"], td["max_length_password"], td["max_length_password"], "John Doe", "Admin", "Enabled")
    obj.assert_error_message()

@pytest.mark.skip(reason="Non-admin user access not available")
def test_reject_access_to_admin_module_for_non_admin_user(page: Page, test_data: dict):
    pass

@pytest.mark.skip(reason="Session expiry not available")
def test_reject_access_to_admin_module_for_unauthenticated_user(page: Page, test_data: dict):
    pass

@pytest.mark.skip(reason="Session expiry not available")
def test_fail_user_creation_if_authentication_is_not_completed(page: Page, test_data: dict):
    pass

def test_fail_role_assignment_if_the_user_does_not_exist(page: Page, test_data: dict):
    td = test_data["suites"]["user_and_role_management"]
    obj = UserAndRoleManagementPage(page)
    obj.login()
    obj.navigate()
    obj.edit_record(999, new_role="Admin")  # Assuming 999 is a non-existent index
    obj.assert_error_message()

def test_transition_from_active_to_disabled_state_succeeds(page: Page, test_data: dict):
    td = test_data["suites"]["user_and_role_management"]
    obj = UserAndRoleManagementPage(page)
    obj.login()
    obj.navigate()
    obj.edit_record(0, new_status="Disabled")
    obj.assert_success_toast()

def test_transition_from_disabled_to_active_state_is_blocked(page: Page, test_data: dict):
    td = test_data["suites"]["user_and_role_management"]
    obj = UserAndRoleManagementPage(page)
    obj.login()
    obj.navigate()
    obj.edit_record(0, new_status="Enabled")
    obj.assert_error_message()

def test_user_creation_with_maximum_allowed_username_length(page: Page, test_data: dict):
    td = test_data["suites"]["user_and_role_management"]
    obj = UserAndRoleManagementPage(page)
    obj.login()
    obj.navigate()
    obj.add_record(td["max_length_username"], td["max_length_password"], td["max_length_password"], "John Doe", "Admin", "Enabled")
    obj.assert_success_toast()

def test_user_creation_with_minimum_allowed_password_length(page: Page, test_data: dict):
    td = test_data["suites"]["user_and_role_management"]
    obj = UserAndRoleManagementPage(page)
    obj.login()
    obj.navigate()
    obj.add_record(td["valid_username"], td["short_password"], td["short_password"], "John Doe", "Admin", "Enabled")
    obj.assert_success_toast()

def test_user_creation_with_maximum_allowed_password_length(page: Page, test_data: dict):
    td = test_data["suites"]["user_and_role_management"]
    obj = UserAndRoleManagementPage(page)
    obj.login()
    obj.navigate()
    obj.add_record(td["valid_username"], td["max_length_password"], td["max_length_password"], "John Doe", "Admin", "Enabled")
    obj.assert_success_toast()

def test_audit_log_entry_created_for_user_creation(page: Page, test_data: dict):
    td = test_data["suites"]["user_and_role_management"]
    obj = UserAndRoleManagementPage(page)
    obj.login()
    obj.navigate()
    obj.add_record(td["valid_username"], td["max_length_password"], td["max_length_password"], "John Doe", "Admin", "Enabled")
    obj.assert_success_toast()

def test_audit_log_entry_created_for_role_assignment(page: Page, test_data: dict):
    td = test_data["suites"]["user_and_role_management"]
    obj = UserAndRoleManagementPage(page)
    obj.login()
    obj.navigate()
    obj.edit_record(0, new_role="Admin")
    obj.assert_success_toast()

def test_handle_username_taken_error_for_duplicate_username(page: Page, test_data: dict):
    td = test_data["suites"]["user_and_role_management"]
    obj = UserAndRoleManagementPage(page)
    obj.login()
    obj.navigate()
    obj.add_record(td["existing_user"], td["max_length_password"], td["max_length_password"], "John Doe", "Admin", "Enabled")
    obj.assert_error_message()

def test_handle_invalid_password_error_for_weak_password(page: Page, test_data: dict):
    td = test_data["suites"]["user_and_role_management"]
    obj = UserAndRoleManagementPage(page)
    obj.login()
    obj.navigate()
    obj.add_record(td["valid_username"], td["short_password"], td["short_password"], "John Doe", "Admin", "Enabled")
    obj.assert_error_message()

@pytest.mark.skip(reason="Non-admin user access not available")
def test_handle_unauthorized_access_error_for_non_admin_access_attempt(page: Page, test_data: dict):
    pass

def test_verify_user_creation_operation_is_logged_in_audit(page: Page, test_data: dict):
    td = test_data["suites"]["user_and_role_management"]
    obj = UserAndRoleManagementPage(page)
    obj.login()
    obj.navigate()
    obj.add_record(td["valid_username"], td["max_length_password"], td["max_length_password"], "John Doe", "Admin", "Enabled")
    obj.assert_success_toast()

def test_verify_role_assignment_operation_is_logged_in_audit(page: Page, test_data: dict):
    td = test_data["suites"]["user_and_role_management"]
    obj = UserAndRoleManagementPage(page)
    obj.login()
    obj.navigate()
    obj.edit_record(0, new_role="Admin")
    obj.assert_success_toast()

def test_verify_audit_log_captures_all_changes_made_to_user_roles(page: Page, test_data: dict):
    td = test_data["suites"]["user_and_role_management"]
    obj = UserAndRoleManagementPage(page)
    obj.login()
    obj.navigate()
    obj.edit_record(0, new_role="Admin")
    obj.assert_success_toast()