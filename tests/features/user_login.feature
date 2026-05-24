Feature: User Login

@Positive
Scenario: Successful login with valid username and password
  Given the user provides a valid username
  And the user provides a valid password
  When the user attempts to log in
  Then the user should be logged in successfully
  And the user session should be created

@Positive
Scenario: Redirect to dashboard upon successful login
  Given the user is logged in successfully
  When the user attempts to access the dashboard
  Then the user should be redirected to the dashboard

@Positive
Scenario: User session is created after successful login
  Given the user provides a valid username
  And the user provides a valid password
  When the user attempts to log in
  Then the user session should be created

@Negative
Scenario: Login rejected for empty username
  Given the user provides an empty username
  And the user provides a valid password
  When the user attempts to log in
  Then the login request should be rejected
  And the system should display an error message for empty username

@Negative
Scenario: Login rejected for empty password
  Given the user provides a valid username
  And the user provides an empty password
  When the user attempts to log in
  Then the login request should be rejected
  And the system should display an error message for empty password

@Negative
Scenario: Login rejected for invalid credentials
  Given the user provides an invalid username
  And the user provides an invalid password
  When the user attempts to log in
  Then the login request should be rejected
  And the system should display INVALID_CREDENTIALS error

@Negative
Scenario: Unauthorized user cannot access Admin module
  Given the user is not authenticated
  When the user attempts to access the Admin module
  Then the access request should be rejected
  And the system should display ACCESS_DENIED error

@Negative
Scenario: Session expired user cannot access dashboard
  Given the user's session has expired
  When the user attempts to access the dashboard
  Then the access request should be rejected
  And the system should display SESSION_EXPIRED error

@Validation
Scenario: Validation error for empty username
  Given the user provides an empty username
  And the user provides a valid password
  When the user attempts to log in
  Then the login request should be rejected
  And the system should display an error message for empty username

@Validation
Scenario: Validation error for empty password
  Given the user provides a valid username
  And the user provides an empty password
  When the user attempts to log in
  Then the login request should be rejected
  And the system should display an error message for empty password

@Validation
Scenario: Validation error for invalid credentials
  Given the user provides an invalid username
  And the user provides an invalid password
  When the user attempts to log in
  Then the login request should be rejected
  And the system should display INVALID_CREDENTIALS error

@Authorization
Scenario: Reject access to Admin module for non-admin user
  Given the user is authenticated as a non-admin user
  When the user attempts to access the Admin module
  Then the access request should be rejected
  And the system should display ACCESS_DENIED error

@Authorization
Scenario: Reject access to Admin module for ESS user
  Given the user is authenticated as an ESS user
  When the user attempts to access the Admin module
  Then the access request should be rejected
  And the system should display ACCESS_DENIED error

@Dependency
Scenario: Access to dashboard is blocked for unauthorized users
  Given the user is not authenticated
  When the user attempts to access the dashboard
  Then the access request should be blocked
  And the system should display ACCESS_DENIED error

@Dependency
Scenario: Access to PIM module is blocked for unauthorized users
  Given the user is not authenticated
  When the user attempts to access the PIM module
  Then the access request should be blocked
  And the system should display ACCESS_DENIED error

@WorkflowTransition
Scenario: Transition from Logged Out to Logged In succeeds
  Given the user is logged out
  When the user attempts to log in
  Then the transition to Logged In should succeed

@WorkflowTransition
Scenario: Transition from Unauthorized to Access Granted is blocked
  Given the user is unauthorized
  When the user attempts to access a restricted area
  Then the transition should be blocked

@EdgeCase
Scenario: Login with maximum allowed username length
  Given the user provides a username of maximum length
  And the user provides a valid password
  When the user attempts to log in
  Then the user should be logged in successfully

@EdgeCase
Scenario: Login with maximum allowed password length
  Given the user provides a valid username
  And the user provides a password of maximum length
  When the user attempts to log in
  Then the user should be logged in successfully

@CrossModule
Scenario: Admin module access control after successful login
  Given the user is logged in successfully
  When the user attempts to access the Admin module
  Then the access should be granted

@CrossModule
Scenario: Dashboard access control after successful login
  Given the user is logged in successfully
  When the user attempts to access the dashboard
  Then the access should be granted

@ErrorHandling
Scenario: INVALID_CREDENTIALS error for invalid login attempt
  Given the user is authenticated as Trader
  And the user provides an invalid username
  And the user provides an invalid password
  When the user attempts to log in
  Then the login request should be rejected
  And the system should display INVALID_CREDENTIALS error

@ErrorHandling
Scenario: ACCESS_DENIED error for unauthorized access attempt
  Given the user is authenticated as Trader
  And the user is not authorized to access the Admin module
  When the user attempts to access the Admin module
  Then the access request should be rejected
  And the system should display ACCESS_DENIED error

@ErrorHandling
Scenario: SESSION_EXPIRED error for session timeout
  Given the user is authenticated as Trader
  And the user's session has expired
  When the user attempts to access the dashboard
  Then the access request should be rejected
  And the system should display SESSION_EXPIRED error

@AuditValidation
Scenario: Successful login attempt is audit logged
  Given the user provides a valid username
  And the user provides a valid password
  When the user attempts to log in
  Then the login attempt should be audit logged

@AuditValidation
Scenario: Failed login attempt is audit logged
  Given the user provides an invalid username
  And the user provides an invalid password
  When the user attempts to log in
  Then the failed login attempt should be audit logged

@AuditValidation
Scenario: Audit log includes username, timestamp, and login status
  Given the user provides a valid username
  And the user provides a valid password
  When the user attempts to log in
  Then the audit log should include the username, timestamp, and login status