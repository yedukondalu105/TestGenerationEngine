Feature: Dashboard Access

Background:
  Given I am logged in as Admin

@Positive
Scenario: Redirect authenticated user to dashboard after successful login
  Given the user is authenticated as Trader
  When the user successfully logs in
  Then the user should be redirected to the dashboard

@Positive
Scenario: Dashboard displays widgets based on user role
  Given the user is authenticated as Trader
  When the user accesses the dashboard
  Then the dashboard should display widgets relevant to the Trader role

@Negative
Scenario: Unauthenticated user cannot access dashboard
  Given the user's session has expired
  When the user attempts to access the dashboard
  Then the access should be denied
  And the system should display SESSION_EXPIRED error

@Negative
Scenario: Unauthorized access for user without dashboard permission
  Given the user is authenticated as Trader
  And the user does not have dashboard access permissions
  When the user attempts to access the dashboard
  Then the access should be denied
  And the system should display INVALID_PERMISSION error

@Validation
Scenario: Dashboard access rejected for unauthenticated user
  Given the user's session has expired
  When the user attempts to access the dashboard
  Then the access should be denied
  And the system should display SESSION_EXPIRED error

@Authorization
Scenario: Reject access for unauthenticated user trying to access dashboard
  Given the user's session has expired
  When the user attempts to access the dashboard
  Then the access should be denied
  And the system should display SESSION_EXPIRED error

@Authorization
Scenario: Reject access for authenticated user without dashboard permission
  Given the user is authenticated as Trader
  And the user does not have dashboard access permissions
  When the user attempts to access the dashboard
  Then the access should be denied
  And the system should display INVALID_PERMISSION error

@Dependency
Scenario: Dashboard access blocked without successful authentication
  Given the user is not authenticated
  When the user attempts to access the dashboard
  Then the access should be denied
  And the system should display SESSION_EXPIRED error

@Workflow Transition
Scenario: Transition from unauthenticated to dashboard access is blocked
  Given the user's session has expired
  When the user attempts to access the dashboard
  Then the access should be denied
  And the system should display SESSION_EXPIRED error

@Edge Case
Scenario: Dashboard access with maximum allowed user roles
  Given the user is authenticated as Trader
  And the user has the maximum allowed roles
  When the user accesses the dashboard
  Then the dashboard should display all widgets for the maximum allowed roles

@Edge Case
Scenario: Dashboard access with minimum allowed user roles
  Given the user is authenticated as Trader
  And the user has the minimum allowed roles
  When the user accesses the dashboard
  Then the dashboard should display widgets relevant to the minimum allowed roles