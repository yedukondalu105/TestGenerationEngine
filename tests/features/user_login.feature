Feature: User Login

Background:
  Given I am logged in as Admin

@Positive
Scenario: Verify successful login with valid username and password
  Given the user is not authenticated
  When the user attempts to log in with valid credentials
  Then the user should be logged in successfully
  And the session should be created

@Positive
Scenario: Verify user is redirected to dashboard after successful login
  Given the user is authenticated
  When the user logs in successfully
  Then the user should be redirected to the dashboard

@Positive
Scenario: Verify session is created after successful login
  Given the user is authenticated
  When the user logs in successfully
  Then the session should be created

@Negative
Scenario: Verify login rejected for invalid username
  Given the user is not authenticated
  When the user attempts to log in with an invalid username
  Then the login request should be rejected
  And the system should display INVALID_CREDENTIALS error

@Negative
Scenario: Verify login rejected for invalid password
  Given the user is not authenticated
  When the user attempts to log in with an invalid password
  Then the login request should be rejected
  And the system should display INVALID_CREDENTIALS error

@Negative
Scenario: Verify login rejected for empty username
  Given the user is not authenticated
  When the user attempts to log in with an empty username
  Then the login request should be rejected
  And the system should display USERNAME_EMPTY error

@Negative
Scenario: Verify login rejected for empty password
  Given the user is not authenticated
  When the user attempts to log in with an empty password
  Then the login request should be rejected
  And the system should display PASSWORD_EMPTY error

@Negative
Scenario: Verify login rejected for session expired user
  Given the user's session has expired
  When the user attempts to log in
  Then the login request should be rejected
  And the system should display SESSION_EXPIRED error

@Negative
Scenario: Verify unauthorized access for user without permissions
  Given the user is authenticated but lacks permissions
  When the user attempts to access a restricted module
  Then the access request should be denied
  And the system should display ACCESS_DENIED error

@Validation
Scenario: Verify login rejected for username shorter than minimum length
  Given the user is not authenticated
  When the user attempts to log in with a username shorter than the minimum length
  Then the login request should be rejected
  And the system should display USERNAME_TOO_SHORT error

@Validation
Scenario: Verify login rejected for password shorter than minimum length
  Given the user is not authenticated
  When the user attempts to log in with a password shorter than the minimum length
  Then the login request should be rejected
  And the system should display PASSWORD_TOO_SHORT error

@Validation
Scenario: Verify login rejected for invalid credentials format
  Given the user is not authenticated
  When the user attempts to log in with invalid credentials format
  Then the login request should be rejected
  And the system should display INVALID_CREDENTIALS_FORMAT error

@Authorization
Scenario: Reject login for unauthorized user attempting to access restricted module
  Given the user is authenticated but lacks permissions
  When the user attempts to access a restricted module
  Then the access request should be denied
  And the system should display ACCESS_DENIED error

@Authorization
Scenario: Reject login for session-expired user
  Given the user's session has expired
  When the user attempts to log in
  Then the login request should be rejected
  And the system should display SESSION_EXPIRED error

@Dependency
Scenario: Verify login requires user to be logged out before attempting login
  Given the user is authenticated
  When the user attempts to log in
  Then the login request should be rejected
  And the system should display USER_ALREADY_LOGGED_IN error

@Workflow_Transition
Scenario: Verify transition from Logged Out to Logged In succeeds
  Given the user is not authenticated
  When the user attempts to log in
  Then the user should be logged in successfully

@Workflow_Transition
Scenario: Verify transition from Logged In to Logged Out is blocked without logout action
  Given the user is authenticated
  When the user attempts to log out
  Then the user should remain logged in

@Edge_Case
Scenario: Verify login with maximum allowed username length
  Given the user is not authenticated
  When the user attempts to log in with a username of maximum allowed length
  Then the user should be logged in successfully

@Edge_Case
Scenario: Verify login with maximum allowed password length
  Given the user is not authenticated
  When the user attempts to log in with a password of maximum allowed length
  Then the user should be logged in successfully

@Error_Handling
Scenario: Verify INVALID_CREDENTIALS error for invalid login attempt
  Given the user is not authenticated
  And the user attempts to log in with invalid credentials
  Then the login request should be rejected
  And the system should display INVALID_CREDENTIALS error

@Error_Handling
Scenario: Verify USERNAME_EMPTY error for empty username input
  Given the user is not authenticated
  When the user attempts to log in with an empty username
  Then the login request should be rejected
  And the system should display USERNAME_EMPTY error

@Error_Handling
Scenario: Verify PASSWORD_EMPTY error for empty password input
  Given the user is not authenticated
  When the user attempts to log in with an empty password
  Then the login request should be rejected
  And the system should display PASSWORD_EMPTY error

@Error_Handling
Scenario: Verify ACCESS_DENIED error for unauthorized access attempt
  Given the user is authenticated but lacks permissions
  When the user attempts to access a restricted module
  Then the access request should be denied
  And the system should display ACCESS_DENIED error

@Audit_Validation
Scenario: Verify successful login attempt is audit logged
  Given the user is authenticated
  When the user logs in successfully
  Then the login attempt should be audit logged

@Audit_Validation
Scenario: Verify failed login attempt is audit logged
  Given the user is not authenticated
  When the user attempts to log in with invalid credentials
  Then the login attempt should be audit logged

@Audit_Validation
Scenario: Verify audit log includes username, timestamp, and login status
  Given the user is authenticated
  When the user logs in successfully
  Then the audit log should include username, timestamp, and login status