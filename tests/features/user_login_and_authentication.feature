Feature: User Login and Authentication

Background:
  Given I am logged in as Admin

@Positive
Scenario: User can log in with valid credentials
  Given the user provides valid username and password
  When the user attempts to log in
  Then the user should be logged in successfully
  And the user session should be created

@Positive
Scenario: User session is created after successful login
  Given the user provides valid username and password
  When the user attempts to log in
  Then the user session should be created

@Positive
Scenario: User is redirected to dashboard after login
  Given the user provides valid username and password
  When the user attempts to log in
  Then the user should be redirected to the dashboard

@Positive
Scenario: Admin can access Admin module after successful login
  Given the user provides valid admin username and password
  When the user attempts to log in
  Then the user should be logged in successfully
  And the user should have access to the Admin module

@Negative
Scenario: Login rejected for empty username
  Given the user provides an empty username
  When the user attempts to log in
  Then the login request should be rejected
  And the system should display an error message

@Negative
Scenario: Login rejected for empty password
  Given the user provides an empty password
  When the user attempts to log in
  Then the login request should be rejected
  And the system should display an error message

@Negative
Scenario: Login rejected for invalid credentials
  Given the user provides invalid username and password
  When the user attempts to log in
  Then the login request should be rejected
  And the system should display an error message

@Negative
Scenario: Unauthorized user cannot access Admin module
  Given the user is authenticated as a regular user
  When the user attempts to access the Admin module
  Then the access should be denied
  And the system should display an error message

@Negative
Scenario: Session expired after 30 minutes of inactivity
  Given the user is logged in
  When the user remains inactive for 30 minutes
  Then the session should expire
  And the user should be redirected to the login page

@Validation
Scenario: Login rejected for username that is empty
  Given the user provides an empty username
  When the user attempts to log in
  Then the login request should be rejected
  And the system should display an error message

@Validation
Scenario: Login rejected for password that is empty
  Given the user provides an empty password
  When the user attempts to log in
  Then the login request should be rejected
  And the system should display an error message

@Validation
Scenario: Login rejected for invalid credentials format
  Given the user provides invalid username format
  When the user attempts to log in
  Then the login request should be rejected
  And the system should display an error message

@Validation
Scenario: Access denied for protected modules without active session
  Given the user is not logged in
  When the user attempts to access a protected module
  Then the access should be denied
  And the system should display an error message

@Authorization
Scenario: Reject login for unauthorized user attempting to access Admin module
  Given the user is not authorized to access the Admin module
  When the user attempts to log in
  Then the login request should be rejected
  And the system should display an error message

@Authorization
Scenario: Reject access to Admin module for authenticated user without Admin role
  Given the user is authenticated as a regular user
  When the user attempts to access the Admin module
  Then the access should be denied
  And the system should display an error message

@Dependency
Scenario: User must be authenticated before accessing dashboard
  Given the user is not logged in
  When the user attempts to access the dashboard
  Then the access should be denied
  And the system should display an error message

@Dependency
Scenario: User must be authenticated before accessing PIM module
  Given the user is not logged in
  When the user attempts to access the PIM module
  Then the access should be denied
  And the system should display an error message

@Workflow_Transition
Scenario: Transition from Logged Out to Logged In succeeds with valid credentials
  Given the user is logged out
  When the user attempts to log in with valid credentials
  Then the user should be logged in successfully

@Workflow_Transition
Scenario: Transition from Logged In to Logged Out succeeds after logout
  Given the user is logged in
  When the user attempts to log out
  Then the user should be logged out successfully

@Edge_Case
Scenario: Login with maximum allowed username length
  Given the user provides a username of maximum allowed length
  When the user attempts to log in
  Then the user should be logged in successfully

@Edge_Case
Scenario: Login with maximum allowed password length
  Given the user provides a password of maximum allowed length
  When the user attempts to log in
  Then the user should be logged in successfully

@Edge_Case
Scenario: Login with special characters in username
  Given the user provides a username with special characters
  When the user attempts to log in
  Then the user should be logged in successfully

@Edge_Case
Scenario: Login with special characters in password
  Given the user provides a password with special characters
  When the user attempts to log in
  Then the user should be logged in successfully

@Cross_Module
Scenario: Dashboard access is granted after successful login
  Given the user provides valid username and password
  When the user attempts to log in
  Then the user should be redirected to the dashboard

@Cross_Module
Scenario: Session management impacts PIM and Recruitment modules after login
  Given the user is logged in
  When the user accesses the PIM module
  Then the user should have access to the PIM module
  And when the user accesses the Recruitment module
  Then the user should have access to the Recruitment module

@Error_Handling
Scenario: INVALID_CREDENTIALS error for invalid username/password combination
  Given the user is authenticated as Trader
  And the user provides invalid username and password
  When the user attempts to log in
  Then the login request should be rejected
  And the system should display INVALID_CREDENTIALS error

@Error_Handling
Scenario: ACCESS_DENIED error for unauthorized access attempt
  Given the user is authenticated as Trader
  And the user attempts to access the Admin module without permission
  When the user attempts to access the Admin module
  Then the access should be denied
  And the system should display ACCESS_DENIED error

@Error_Handling
Scenario: SESSION_EXPIRED error for session timeout
  Given the user is authenticated as Trader
  And the user remains inactive for 30 minutes
  When the user attempts to access the dashboard
  Then the access should be denied
  And the system should display SESSION_EXPIRED error

@Error_Handling
Scenario: Audit log entry for failed login attempt
  Given the user provides invalid username and password
  When the user attempts to log in
  Then the failed login attempt should be logged in the audit

@Audit_Validation
Scenario: Successful login attempt is logged in audit
  Given the user provides valid username and password
  When the user attempts to log in
  Then the successful login attempt should be logged in the audit

@Audit_Validation
Scenario: Failed login attempt is logged in audit
  Given the user provides invalid username and password
  When the user attempts to log in
  Then the failed login attempt should be logged in the audit

@Audit_Validation
Scenario: Audit log includes username, timestamp, and login status
  Given the user provides valid username and password
  When the user attempts to log in
  Then the audit log should include username, timestamp, and login status