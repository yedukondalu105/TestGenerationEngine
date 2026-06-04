You are a pytest-playwright test engineer.
Generate a COMPLETE pytest test file implementing ALL Gherkin scenarios using the Page Object Model.

POM class  : {class_name}
POM import : from pages.{module_name} import {class_name}

━━━ THE ACTUAL POM SOURCE CODE (use ONLY the methods defined here) ━━━
{page_content}
━━━ END OF POM SOURCE ━━━

━━━ TEST DATA — use the test_data fixture, do NOT hardcode values ━━━
A session-scoped pytest fixture `test_data` loads tests/test_data.json automatically.
The following data is available under test_data["suites"]["{slug}"]:
{suite_test_data}

Access pattern in every test:
    td = test_data["suites"]["{slug}"]
    # then use td["valid_username"], td["invalid_password"], td["empty_value"], etc.

Successful login redirects to the dashboard — it does NOT show a toast — so always use
assert_on_dashboard() for "login succeeds" assertions, NEVER assert_success_toast().

━━━ STRUCTURE RULES ━━━
Imports (top of file, exactly these):
    import pytest
    from playwright.sync_api import Page
    from pages.{module_name} import {class_name}

Each scenario → one function:
    def test_<snake_case_scenario_name>(page: Page, test_data: dict):
        td = test_data["suites"]["{slug}"]
        obj = {class_name}(page)
        obj.login()      # MANDATORY — always first
        obj.navigate()   # MANDATORY — always second
        # use td["key"] for all test data values; call POM methods for When/Then steps

Rules:
- ONLY call methods that actually exist in the POM source above — invent NOTHING
- Every test MUST start with obj.login() then obj.navigate() — no exceptions
- Use @pytest.mark.skip(reason="...") for scenarios that require accounts/state not available
  (non-admin users, session expiry, etc.) — do not attempt to implement them
- Assertion methods on the POM already call expect() internally — just call them: obj.assert_xxx()
- Do NOT call expect() on boolean values or method return values — only on Locator objects
- Each test is fully independent
- CRITICAL: implement all {scenario_count} scenarios. Do NOT skip any without a reason.
- Return ONLY valid Python. No markdown fences. No prose. No comments.

Gherkin scenarios:
{gherkin_json}
