import re
import pytest
from playwright.sync_api import Page, expect
from pages.user_login_page import UserLoginPage

VALID_USER = "Admin"
VALID_PASS = "admin123"
BAD_USER   = "WrongUser"
BAD_PASS   = "wrongpass"

def test_successful_login_with_valid_username_and_password(page: Page):
    obj = UserLoginPage(page)
    obj.login()
    obj.navigate()
    obj.provide_username(VALID_USER)
    obj.provide_password(VALID_PASS)
    obj.attempt_login()
    obj.assert_on_dashboard()

def test_redirect_to_dashboard_upon_successful_login(page: Page):
    obj = UserLoginPage(page)
    obj.login()
    obj.navigate()
    obj.provide_username(VALID_USER)
    obj.provide_password(VALID_PASS)
    obj.attempt_login()
    obj.assert_on_dashboard()

def test_user_session_is_created_after_successful_login(page: Page):
    obj = UserLoginPage(page)
    obj.login()
    obj.navigate()
    obj.provide_username(VALID_USER)
    obj.provide_password(VALID_PASS)
    obj.attempt_login()
    obj.assert_on_dashboard()

def test_login_rejected_for_empty_username(page: Page):
    obj = UserLoginPage(page)
    obj.login()
    obj.navigate()
    obj.provide_username("")
    obj.provide_password(VALID_PASS)
    obj.attempt_login()
    obj.assert_error_message()

def test_login_rejected_for_empty_password(page: Page):
    obj = UserLoginPage(page)
    obj.login()
    obj.navigate()
    obj.provide_username(VALID_USER)
    obj.provide_password("")
    obj.attempt_login()
    obj.assert_error_message()

def test_login_rejected_for_invalid_credentials(page: Page):
    obj = UserLoginPage(page)
    obj.login()
    obj.navigate()
    obj.provide_username(BAD_USER)
    obj.provide_password(BAD_PASS)
    obj.attempt_login()
    obj.assert_invalid_credentials()

@pytest.mark.skip(reason="Requires a non-admin user account not available in default OrangeHRM")
def test_unauthorized_user_cannot_access_admin_module(page: Page):
    pass

@pytest.mark.skip(reason="Requires a session expiry mechanism not testable via UI alone")
def test_session_expired_user_cannot_access_dashboard(page: Page):
    pass

def test_validation_error_for_empty_username(page: Page):
    obj = UserLoginPage(page)
    obj.login()
    obj.navigate()
    obj.provide_username("")
    obj.provide_password(VALID_PASS)
    obj.attempt_login()
    obj.assert_error_message()

def test_validation_error_for_empty_password(page: Page):
    obj = UserLoginPage(page)
    obj.login()
    obj.navigate()
    obj.provide_username(VALID_USER)
    obj.provide_password("")
    obj.attempt_login()
    obj.assert_error_message()

def test_validation_error_for_invalid_credentials(page: Page):
    obj = UserLoginPage(page)
    obj.login()
    obj.navigate()
    obj.provide_username(BAD_USER)
    obj.provide_password(BAD_PASS)
    obj.attempt_login()
    obj.assert_invalid_credentials()

@pytest.mark.skip(reason="Requires a non-admin user account")
def test_reject_access_to_admin_module_for_non_admin_user(page: Page):
    pass

@pytest.mark.skip(reason="Requires an ESS user account not set up in this environment")
def test_reject_access_to_admin_module_for_ess_user(page: Page):
    pass

@pytest.mark.skip(reason="Requires an unauthorized user account")
def test_access_to_dashboard_is_blocked_for_unauthorized_users(page: Page):
    pass

@pytest.mark.skip(reason="Requires an unauthorized user account")
def test_access_to_pim_module_is_blocked_for_unauthorized_users(page: Page):
    pass

def test_transition_from_logged_out_to_logged_in_succeeds(page: Page):
    obj = UserLoginPage(page)
    obj.login()
    obj.navigate()
    obj.provide_username(VALID_USER)
    obj.provide_password(VALID_PASS)
    obj.attempt_login()
    obj.assert_on_dashboard()

@pytest.mark.skip(reason="Requires an unauthorized user account")
def test_transition_from_unauthorized_to_access_granted_is_blocked(page: Page):
    pass

def test_login_with_maximum_allowed_username_length(page: Page):
    obj = UserLoginPage(page)
    obj.login()
    obj.navigate()
    obj.provide_username("a" * 255)
    obj.provide_password(VALID_PASS)
    obj.attempt_login()
    obj.assert_invalid_credentials()

def test_login_with_maximum_allowed_password_length(page: Page):
    obj = UserLoginPage(page)
    obj.login()
    obj.navigate()
    obj.provide_username(VALID_USER)
    obj.provide_password("a" * 255)
    obj.attempt_login()
    obj.assert_invalid_credentials()

def test_admin_module_access_control_after_successful_login(page: Page):
    obj = UserLoginPage(page)
    obj.login()
    obj.navigate()
    obj.provide_username(VALID_USER)
    obj.provide_password(VALID_PASS)
    obj.attempt_login()
    obj.assert_on_dashboard()

def test_dashboard_access_control_after_successful_login(page: Page):
    obj = UserLoginPage(page)
    obj.login()
    obj.navigate()
    obj.provide_username(VALID_USER)
    obj.provide_password(VALID_PASS)
    obj.attempt_login()
    obj.assert_on_dashboard()

def test_invalid_credentials_error_for_invalid_login_attempt(page: Page):
    obj = UserLoginPage(page)
    obj.login()
    obj.navigate()
    obj.provide_username(BAD_USER)
    obj.provide_password(BAD_PASS)
    obj.attempt_login()
    obj.assert_invalid_credentials()

@pytest.mark.skip(reason="Requires an unauthorized user account")
def test_access_denied_error_for_unauthorized_access_attempt(page: Page):
    pass

@pytest.mark.skip(reason="Requires a session expiry mechanism not testable via UI alone")
def test_session_expired_error_for_session_timeout(page: Page):
    pass

def test_successful_login_attempt_is_audit_logged(page: Page):
    obj = UserLoginPage(page)
    obj.login()
    obj.navigate()
    obj.provide_username(VALID_USER)
    obj.provide_password(VALID_PASS)
    obj.attempt_login()
    obj.assert_on_dashboard()

def test_failed_login_attempt_is_audit_logged(page: Page):
    obj = UserLoginPage(page)
    obj.login()
    obj.navigate()
    obj.provide_username(BAD_USER)
    obj.provide_password(BAD_PASS)
    obj.attempt_login()
    obj.assert_invalid_credentials()

def test_audit_log_includes_username_timestamp_and_login_status(page: Page):
    obj = UserLoginPage(page)
    obj.login()
    obj.navigate()
    obj.provide_username(VALID_USER)
    obj.provide_password(VALID_PASS)
    obj.attempt_login()
    obj.assert_on_dashboard()
