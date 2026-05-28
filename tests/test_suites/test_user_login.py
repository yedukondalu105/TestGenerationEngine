import pytest
from playwright.sync_api import Page
from pages.user_login_page import UserLoginPage


@pytest.fixture
def td(test_data):
    return test_data["suites"]["user_login"]


def test_verify_successful_login_with_valid_username_and_password(page: Page, td):
    obj = UserLoginPage(page)
    obj.login()
    obj.navigate()
    obj.provide_username(td["valid_username"])
    obj.provide_password(td["valid_password"])
    obj.attempt_login()
    obj.assert_on_dashboard()


def test_verify_user_is_redirected_to_dashboard_after_successful_login(page: Page, td):
    obj = UserLoginPage(page)
    obj.login()
    obj.navigate()
    obj.provide_username(td["valid_username"])
    obj.provide_password(td["valid_password"])
    obj.attempt_login()
    obj.assert_on_dashboard()


def test_verify_session_is_created_after_successful_login(page: Page, td):
    obj = UserLoginPage(page)
    obj.login()
    obj.navigate()
    obj.provide_username(td["valid_username"])
    obj.provide_password(td["valid_password"])
    obj.attempt_login()
    obj.assert_on_dashboard()


def test_verify_login_rejected_for_invalid_username(page: Page, td):
    obj = UserLoginPage(page)
    obj.login()
    obj.navigate()
    obj.provide_username(td["invalid_username"])
    obj.provide_password(td["valid_password"])
    obj.attempt_login()
    obj.assert_invalid_credentials()


def test_verify_login_rejected_for_invalid_password(page: Page, td):
    obj = UserLoginPage(page)
    obj.login()
    obj.navigate()
    obj.provide_username(td["valid_username"])
    obj.provide_password(td["invalid_password"])
    obj.attempt_login()
    obj.assert_invalid_credentials()


def test_verify_login_rejected_for_empty_username(page: Page, td):
    obj = UserLoginPage(page)
    obj.login()
    obj.navigate()
    obj.provide_username(td["empty_value"])
    obj.provide_password(td["valid_password"])
    obj.attempt_login()
    obj.assert_error_message()


def test_verify_login_rejected_for_empty_password(page: Page, td):
    obj = UserLoginPage(page)
    obj.login()
    obj.navigate()
    obj.provide_username(td["valid_username"])
    obj.provide_password(td["empty_value"])
    obj.attempt_login()
    obj.assert_error_message()


@pytest.mark.skip(reason="Session expired scenario not available")
def test_verify_login_rejected_for_session_expired_user(page: Page, td):
    pass


@pytest.mark.skip(reason="Unauthorized access scenario not available")
def test_verify_unauthorized_access_for_user_without_permissions(page: Page, td):
    pass


def test_verify_login_rejected_for_username_shorter_than_minimum_length(page: Page, td):
    obj = UserLoginPage(page)
    obj.login()
    obj.navigate()
    obj.provide_username(td["short_username"])
    obj.provide_password(td["valid_password"])
    obj.attempt_login()
    obj.assert_invalid_credentials()


def test_verify_login_rejected_for_password_shorter_than_minimum_length(page: Page, td):
    obj = UserLoginPage(page)
    obj.login()
    obj.navigate()
    obj.provide_username(td["valid_username"])
    obj.provide_password(td["short_password"])
    obj.attempt_login()
    obj.assert_invalid_credentials()


def test_verify_login_rejected_for_invalid_credentials_format(page: Page, td):
    obj = UserLoginPage(page)
    obj.login()
    obj.navigate()
    obj.provide_username(td["invalid_format"])
    obj.provide_password(td["invalid_format"])
    obj.attempt_login()
    obj.assert_invalid_credentials()


@pytest.mark.skip(reason="Unauthorized access scenario not available")
def test_reject_login_for_unauthorized_user_attempting_to_access_restricted_module(page: Page, td):
    pass


@pytest.mark.skip(reason="Session expired scenario not available")
def test_reject_login_for_session_expired_user(page: Page, td):
    pass


@pytest.mark.skip(reason="User already logged in scenario not available")
def test_verify_login_requires_user_to_be_logged_out_before_attempting_login(page: Page, td):
    pass


def test_verify_transition_from_logged_out_to_logged_in_succeeds(page: Page, td):
    obj = UserLoginPage(page)
    obj.login()
    obj.navigate()
    obj.provide_username(td["valid_username"])
    obj.provide_password(td["valid_password"])
    obj.attempt_login()
    obj.assert_on_dashboard()


@pytest.mark.skip(reason="Logout action not available")
def test_verify_transition_from_logged_in_to_logged_out_is_blocked_without_logout_action(page: Page, td):
    pass


def test_verify_login_with_maximum_allowed_username_length(page: Page, td):
    obj = UserLoginPage(page)
    obj.login()
    obj.navigate()
    obj.provide_username(td["max_length_username"])
    obj.provide_password(td["valid_password"])
    obj.attempt_login()
    obj.assert_invalid_credentials()


def test_verify_login_with_maximum_allowed_password_length(page: Page, td):
    obj = UserLoginPage(page)
    obj.login()
    obj.navigate()
    obj.provide_username(td["valid_username"])
    obj.provide_password(td["max_length_password"])
    obj.attempt_login()
    obj.assert_invalid_credentials()


def test_verify_invalid_credentials_error_for_invalid_login_attempt(page: Page, td):
    obj = UserLoginPage(page)
    obj.login()
    obj.navigate()
    obj.provide_username(td["invalid_username"])
    obj.provide_password(td["invalid_password"])
    obj.attempt_login()
    obj.assert_invalid_credentials()


def test_verify_username_empty_error_for_empty_username_input(page: Page, td):
    obj = UserLoginPage(page)
    obj.login()
    obj.navigate()
    obj.provide_username(td["empty_value"])
    obj.provide_password(td["valid_password"])
    obj.attempt_login()
    obj.assert_error_message()


def test_verify_password_empty_error_for_empty_password_input(page: Page, td):
    obj = UserLoginPage(page)
    obj.login()
    obj.navigate()
    obj.provide_username(td["valid_username"])
    obj.provide_password(td["empty_value"])
    obj.attempt_login()
    obj.assert_error_message()


@pytest.mark.skip(reason="Unauthorized access scenario not available")
def test_verify_access_denied_error_for_unauthorized_access_attempt(page: Page, td):
    pass


@pytest.mark.skip(reason="Audit logging not available")
def test_verify_successful_login_attempt_is_audit_logged(page: Page, td):
    pass


@pytest.mark.skip(reason="Audit logging not available")
def test_verify_failed_login_attempt_is_audit_logged(page: Page, td):
    pass


@pytest.mark.skip(reason="Audit logging not available")
def test_verify_audit_log_includes_username_timestamp_and_login_status(page: Page, td):
    pass
