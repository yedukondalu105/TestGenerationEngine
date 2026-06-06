Feature: User and Role Management

Background:
  Given I am logged in as Admin

@Positive
Scenario: Create new user with valid details
  Given the user is authenticated as Admin
  When the user attempts to create a new user with valid details
  Then the user should be created successfully
  And the operation should be audit logged

@Positive
Scenario: Assign role during user creation
  Given the user is authenticated as Admin
  When the user attempts to create a new user with a role assigned
  Then the user should be created with the assigned role
  And the operation should be audit logged

@Positive
Scenario: Search existing users by username
  Given the user is authenticated as Admin
  When the user attempts to search for users by username
  Then the search results should display the correct users
  And the operation should be audit logged

@Positive
Scenario: Search users by role
  Given the user is authenticated as Admin
  When the user attempts to search for users by role
  Then the search results should display users with the specified role
  And the operation should be audit logged

@Positive
Scenario: Search users by status
  Given the user is authenticated as Admin
  When the user attempts to search for users by status
  Then the search results should display users with the specified status
  And the operation should be audit logged

@Positive
Scenario: Disable a user
  Given the user is authenticated as Admin
  And an active user exists
  When the user attempts to disable the user
  Then the user should be disabled successfully
  And the operation should be audit logged

@Positive
Scenario: Access admin module after authentication
  Given the user is authenticated as Admin
  When the user attempts to access the admin module
  Then the admin module should be accessible
  And the operation should be audit logged

@Negative
Scenario: Fail user creation if employee does not exist
  Given the user is authenticated as Admin
  When the user attempts to create a new user with a non-existent employee
  Then the user creation should fail
  And the system should display USER_NOT_FOUND error

@Negative
Scenario: Fail creation for duplicate username
  Given the user is authenticated as Admin
  And a user with username "existing_user" exists
  When the user attempts to create a new user with username "existing_user"
  Then the user creation should fail
  And the system should display USERNAME_TAKEN error

@Negative
Scenario: Fail creation for invalid password
  Given the user is authenticated as Admin
  When the user attempts to create a new user with an invalid password
  Then the user creation should fail
  And the system should display INVALID_PASSWORD error

@Negative
Scenario: Reject access to admin module without authentication
  Given the user's session has expired
  When the user attempts to access the admin module
  Then access should be denied
  And the system should display SESSION_EXPIRED error

@Negative
Scenario: Fail disabling a user that does not exist
  Given the user is authenticated as Admin
  When the user attempts to disable a non-existent user
  Then the operation should fail
  And the system should display USER_NOT_FOUND error

@Negative
Scenario: Fail user creation for missing mandatory fields
  Given the user is authenticated as Admin
  When the user attempts to create a new user without mandatory fields
  Then the user creation should fail
  And the system should display MISSING_FIELDS error

@Negative
Scenario: Fail enabling a user that is already disabled
  Given the user is authenticated as Admin
  And a disabled user exists
  When the user attempts to enable the user
  Then the operation should fail
  And the system should display USER_ALREADY_ENABLED error

@Validation
Scenario: Error for empty employee name
  Given the user is authenticated as Admin
  When the user attempts to create a new user with an empty employee name
  Then the user creation should fail
  And the system should display MISSING_EMPLOYEE_NAME error

@Validation
Scenario: Error for empty username
  Given the user is authenticated as Admin
  When the user attempts to create a new user with an empty username
  Then the user creation should fail
  And the system should display MISSING_USERNAME error

@Validation
Scenario: Error for password not meeting security policies
  Given the user is authenticated as Admin
  When the user attempts to create a new user with a weak password
  Then the user creation should fail
  And the system should display WEAK_PASSWORD error

@Validation
Scenario: Error for username that is not unique
  Given the user is authenticated as Admin
  And a user with username "existing_user" exists
  When the user attempts to create a new user with username "existing_user"
  Then the user creation should fail
  And the system should display USERNAME_TAKEN error

@Authorization
Scenario: Reject access to admin module for non-admin user
  Given the user is authenticated as User
  When the user attempts to access the admin module
  Then access should be denied
  And the system should display UNAUTHORIZED_ACCESS error

@Authorization
Scenario: Reject access to admin module for unauthenticated user
  Given the user's session has expired
  When the user attempts to access the admin module
  Then access should be denied
  And the system should display SESSION_EXPIRED error

@Dependency
Scenario: Fail user creation if authentication is not completed
  Given the user's session has expired
  When the user attempts to create a new user
  Then the user creation should fail
  And the system should display SESSION_EXPIRED error

@Dependency
Scenario: Fail role assignment if the user does not exist
  Given the user is authenticated as Admin
  And a user does not exist
  When the user attempts to assign a role to the non-existent user
  Then the role assignment should fail
  And the system should display USER_NOT_FOUND error

@Workflow_Transition
Scenario: Transition from Active to Disabled state succeeds
  Given the user is authenticated as Admin
  And an active user exists
  When the user attempts to disable the user
  Then the user should be disabled successfully
  And the operation should be audit logged

@Workflow_Transition
Scenario: Transition from Disabled to Active state is blocked
  Given the user is authenticated as Admin
  And a disabled user exists
  When the user attempts to enable the user
  Then the user should remain disabled
  And the system should display USER_ALREADY_ENABLED error

@Edge_Case
Scenario: User creation with maximum allowed username length
  Given the user is authenticated as Admin
  When the user attempts to create a new user with maximum allowed username length
  Then the user should be created successfully
  And the operation should be audit logged

@Edge_Case
Scenario: User creation with minimum allowed password length
  Given the user is authenticated as Admin
  When the user attempts to create a new user with minimum allowed password length
  Then the user should be created successfully
  And the operation should be audit logged

@Edge_Case
Scenario: User creation with maximum allowed password length
  Given the user is authenticated as Admin
  When the user attempts to create a new user with maximum allowed password length
  Then the user should be created successfully
  And the operation should be audit logged

@Cross_Module
Scenario: Audit log entry created for user creation
  Given the user is authenticated as Admin
  When the user attempts to create a new user
  Then the audit log entry should be created

@Cross_Module
Scenario: Audit log entry created for role assignment
  Given the user is authenticated as Admin
  When the user attempts to assign a role to a user
  Then the audit log entry should be created

@Error_Handling
Scenario: Handle USERNAME_TAKEN error for duplicate username
  Given the user is authenticated as Admin
  And a user with username "existing_user" exists
  When the user attempts to create a new user with username "existing_user"
  Then the user creation should fail
  And the system should display USERNAME_TAKEN error

@Error_Handling
Scenario: Handle INVALID_PASSWORD error for weak password
  Given the user is authenticated as Admin
  When the user attempts to create a new user with a weak password
  Then the user creation should fail
  And the system should display INVALID_PASSWORD error

@Error_Handling
Scenario: Handle UNAUTHORIZED_ACCESS error for non-admin access attempt
  Given the user is authenticated as User
  When the user attempts to access the admin module
  Then access should be denied
  And the system should display UNAUTHORIZED_ACCESS error

@Audit_Validation
Scenario: Verify user creation operation is logged in audit
  Given the user is authenticated as Admin
  When the user attempts to create a new user
  Then the operation should be audit logged

@Audit_Validation
Scenario: Verify role assignment operation is logged in audit
  Given the user is authenticated as Admin
  When the user attempts to assign a role to a user
  Then the operation should be audit logged

@Audit_Validation
Scenario: Verify audit log captures all changes made to user roles
  Given the user is authenticated as Admin
  When the user attempts to change a user's role
  Then the previous and updated role values should be captured in the audit log