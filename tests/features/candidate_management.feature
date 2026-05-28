Feature: Candidate Management

@Positive
Scenario: Verify candidate successfully added with valid details
  Given the user is authenticated as Recruiter
  When the user attempts to add a candidate with valid details
  Then the candidate should be added successfully
  And the candidate details should be audit logged

@Positive
Scenario: Verify resume successfully uploaded in PDF format
  Given the user is authenticated as Recruiter
  And a candidate exists
  When the user attempts to upload a resume in PDF format
  Then the resume should be uploaded successfully
  And the resume upload should be audit logged

@Positive
Scenario: Verify resume successfully uploaded in DOCX format
  Given the user is authenticated as Recruiter
  And a candidate exists
  When the user attempts to upload a resume in DOCX format
  Then the resume should be uploaded successfully
  And the resume upload should be audit logged

@Positive
Scenario: Verify interview scheduled with valid details
  Given the user is authenticated as Recruiter
  And a candidate exists
  When the user attempts to schedule an interview with valid details
  Then the interview should be scheduled successfully
  And the interview scheduling should be audit logged

@Negative
Scenario: Verify candidate addition rejected for missing mandatory fields
  Given the user is authenticated as Recruiter
  When the user attempts to add a candidate with missing mandatory fields
  Then the candidate addition should be rejected
  And the system should display MISSING_MANDATORY_FIELDS error

@Negative
Scenario: Verify candidate addition rejected for duplicate email
  Given the user is authenticated as Recruiter
  And a candidate with email "test@example.com" exists
  When the user attempts to add a candidate with the same email
  Then the candidate addition should be rejected
  And the system should display DUPLICATE_CANDIDATE error

@Negative
Scenario: Verify candidate addition rejected for unsupported resume format
  Given the user is authenticated as Recruiter
  When the user attempts to add a candidate with an unsupported resume format
  Then the candidate addition should be rejected
  And the system should display UNSUPPORTED_FILE_FORMAT error

@Negative
Scenario: Verify unauthorized user cannot access recruitment module
  Given the user's session has expired
  When the user attempts to access the recruitment module
  Then the access should be denied
  And the system should display UNAUTHORIZED_ACCESS error

@Validation
Scenario: Verify candidate addition rejected for non-unique email
  Given the user is authenticated as Recruiter
  And a candidate with email "test@example.com" exists
  When the user attempts to add a candidate with the same email
  Then the candidate addition should be rejected
  And the system should display DUPLICATE_CANDIDATE error

@Authorization
Scenario: Reject access for unauthorized user to recruitment module
  Given the user's session has expired
  When the user attempts to access the recruitment module
  Then the access should be denied
  And the system should display SESSION_EXPIRED error

@Authorization
Scenario: Reject access for user without recruitment permission
  Given the user is authenticated as User
  And the user does not have recruitment permissions
  When the user attempts to access the recruitment module
  Then the access should be denied
  And the system should display INVALID_PERMISSION error

@Dependency
Scenario: Verify candidate addition blocked without user authentication
  Given the user's session has expired
  When the user attempts to add a candidate
  Then the candidate addition should be blocked
  And the system should display SESSION_EXPIRED error

@Dependency
Scenario: Verify resume upload blocked without user authentication
  Given the user's session has expired
  When the user attempts to upload a resume
  Then the resume upload should be blocked
  And the system should display SESSION_EXPIRED error

@Workflow_Transition
Scenario: Verify transition from Application Initiated to Shortlisted succeeds
  Given the user is authenticated as Recruiter
  And a candidate exists in Application Initiated state
  When the user attempts to transition the candidate to Shortlisted
  Then the transition should be successful

@Workflow_Transition
Scenario: Verify transition from Shortlisted to Interview Scheduled succeeds
  Given the user is authenticated as Recruiter
  And a candidate exists in Shortlisted state
  When the user attempts to transition the candidate to Interview Scheduled
  Then the transition should be successful

@Workflow_Transition
Scenario: Verify transition from Interview Scheduled to Offered succeeds
  Given the user is authenticated as Recruiter
  And a candidate exists in Interview Scheduled state
  When the user attempts to transition the candidate to Offered
  Then the transition should be successful

@Workflow_Transition
Scenario: Verify transition from Offered to Hired succeeds
  Given the user is authenticated as Recruiter
  And a candidate exists in Offered state
  When the user attempts to transition the candidate to Hired
  Then the transition should be successful

@Workflow_Transition
Scenario: Verify transition from Offered to Rejected succeeds
  Given the user is authenticated as Recruiter
  And a candidate exists in Offered state
  When the user attempts to transition the candidate to Rejected
  Then the transition should be successful

@Edge_Case
Scenario: Verify candidate addition with maximum allowed email length
  Given the user is authenticated as Recruiter
  When the user attempts to add a candidate with maximum allowed email length
  Then the candidate should be added successfully
  And the candidate details should be audit logged

@Edge_Case
Scenario: Verify candidate addition with minimum valid name length
  Given the user is authenticated as Recruiter
  When the user attempts to add a candidate with minimum valid name length
  Then the candidate should be added successfully
  And the candidate details should be audit logged

@Edge_Case
Scenario: Verify candidate addition with maximum allowed vacancy length
  Given the user is authenticated as Recruiter
  When the user attempts to add a candidate with maximum allowed vacancy length
  Then the candidate should be added successfully
  And the candidate details should be audit logged

@Edge_Case
Scenario: Verify candidate addition with minimum valid vacancy length
  Given the user is authenticated as Recruiter
  When the user attempts to add a candidate with minimum valid vacancy length
  Then the candidate should be added successfully
  And the candidate details should be audit logged

@Cross_Module
Scenario: Verify audit log created for candidate addition
  Given the user is authenticated as Recruiter
  When the user attempts to add a candidate
  Then the audit log should be created

@Cross_Module
Scenario: Verify audit log created for resume upload
  Given the user is authenticated as Recruiter
  And a candidate exists
  When the user attempts to upload a resume
  Then the audit log should be created

@Error_Handling
Scenario: Verify DUPLICATE_CANDIDATE error for duplicate email
  Given the user is authenticated as Recruiter
  And a candidate with email "test@example.com" exists
  When the user attempts to add a candidate with the same email
  Then the candidate addition should be rejected
  And the system should display DUPLICATE_CANDIDATE error

@Error_Handling
Scenario: Verify UNSUPPORTED_FILE_FORMAT error for unsupported resume format
  Given the user is authenticated as Recruiter
  When the user attempts to add a candidate with an unsupported resume format
  Then the candidate addition should be rejected
  And the system should display UNSUPPORTED_FILE_FORMAT error

@Error_Handling
Scenario: Verify UNAUTHORIZED_ACCESS error for unauthorized user access
  Given the user's session has expired
  When the user attempts to access the recruitment module
  Then the access should be denied
  And the system should display UNAUTHORIZED_ACCESS error

@Audit_Validation
Scenario: Verify candidate lifecycle changes are audit logged
  Given the user is authenticated as Recruiter
  And a candidate exists
  When the user attempts to add a candidate
  Then the candidate details should be audit logged

@Audit_Validation
Scenario: Verify audit log captures candidate details on addition
  Given the user is authenticated as Recruiter
  When the user attempts to add a candidate
  Then the candidate details should be audit logged

@Audit_Validation
Scenario: Verify audit log captures resume upload details
  Given the user is authenticated as Recruiter
  And a candidate exists
  When the user attempts to upload a resume
  Then the resume upload details should be audit logged