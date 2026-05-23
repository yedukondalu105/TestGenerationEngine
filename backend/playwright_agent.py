import os
import sys
import json
import tempfile
import subprocess
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

load_dotenv(override=True)

APP_URL = os.getenv("PLAYWRIGHT_APP_URL", "")

llm_codegen = ChatOpenAI(model="gpt-4o", temperature=0.1)
llm_review  = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)

_CODEGEN_PROMPT = """You are a senior Playwright test automation engineer.

Your task: convert EVERY Gherkin BDD scenario below into a COMPLETE, FULLY IMPLEMENTED pytest-playwright test.

CRITICAL RULE: Every test MUST implement ALL Given/When/Then steps. A test that only logs in and does nothing else is WRONG.
After login, each test must navigate to the correct module and perform the FULL sequence of UI actions described by the scenario steps.

════════════════════════════════════════════════════════════
TARGET APP : {app_url}
CREDENTIALS: username=Admin  password=admin123
════════════════════════════════════════════════════════════

━━━ LOGIN HELPER (use at the start of every test) ━━━
    page.goto("{app_url}")
    page.wait_for_load_state("networkidle")
    page.get_by_placeholder("Username").fill("Admin")
    page.get_by_placeholder("Password").fill("admin123")
    page.get_by_role("button", name="Login").click()
    page.wait_for_url("**/dashboard/index")

━━━ ORANGEHRM NAVIGATION SELECTORS ━━━
Left sidebar menu items (click to open module):
    page.get_by_role("link", name="Admin")
    page.get_by_role("link", name="PIM")
    page.get_by_role("link", name="Leave")
    page.get_by_role("link", name="Time")
    page.get_by_role("link", name="Recruitment")
    page.get_by_role("link", name="My Info")
    page.get_by_role("link", name="Performance")
    page.get_by_role("link", name="Dashboard")
    page.get_by_role("link", name="Directory")
    page.get_by_role("link", name="Maintenance")
    page.get_by_role("link", name="Buzz")

Sub-menu items (appear after clicking main menu):
    page.get_by_role("menuitem", name="User Management")
    page.get_by_role("menuitem", name="Job")
    page.get_by_role("menuitem", name="Organization")
    page.get_by_role("menuitem", name="Qualifications")
    page.get_by_role("menuitem", name="Nationalities")
    page.get_by_role("menuitem", name="Configuration")

━━━ COMMON ORANGEHRM UI PATTERNS ━━━
Search/filter forms:
    page.get_by_role("button", name="Search").click()
    page.get_by_role("button", name="Reset").click()

Add / Save / Delete buttons:
    page.get_by_role("button", name="Add").click()
    page.get_by_role("button", name="Save").click()
    page.get_by_role("button", name="Delete").click()
    page.get_by_role("button", name="Yes, Delete").click()   # confirmation dialog

Input fields (OrangeHRM uses oxd-input):
    page.locator("input.oxd-input").nth(0).fill("value")
    page.get_by_role("textbox", name="First Name").fill("John")
    page.get_by_role("textbox", name="Last Name").fill("Doe")

Dropdowns (OrangeHRM custom select):
    page.locator(".oxd-select-text").nth(0).click()
    page.get_by_role("option", name="Option Text").click()

Tables / records:
    page.locator(".oxd-table-row").nth(1)          # first data row
    page.locator(".oxd-table-cell-actions").nth(0) # action buttons on first row
    page.get_by_role("button", name="Edit").first.click()

Toast / success messages:
    expect(page.locator(".oxd-toast")).to_be_visible()
    expect(page.locator(".oxd-toast--success")).to_be_visible()

Assertions:
    expect(page).to_have_url(re.compile(r".*/pim/.*"))
    expect(page.get_by_role("heading", name="Add Employee")).to_be_visible()
    expect(page.locator(".oxd-table-row")).to_have_count(...)

━━━ CODING RULES ━━━
- Each Gherkin scenario → one `def test_<snake_case_scenario_name>(page: Page):` function
- EVERY test must perform the FULL sequence from the scenario steps — not just login
- Use page.wait_for_load_state("networkidle") after navigation clicks
- Use page.wait_for_timeout(1000) sparingly when a dynamic element needs to appear
- Wrap assertions in expect() — never use assert statements
- Each test is fully independent (starts from the app URL, does full login)
- Only the `page` fixture is allowed
- Top of file imports ONLY: `import re`, `import pytest`, `from playwright.sync_api import Page, expect`
- Return ONLY valid Python. No markdown fences, no prose, no comments.

════════════════════════════════════════════════════════════
GHERKIN SCENARIOS JSON (implement EVERY scenario fully):
{gherkin_json}
════════════════════════════════════════════════════════════
"""


def playwright_codegen_agent(gherkin_json: str) -> str:
    """Convert Gherkin JSON scenarios to pytest-playwright Python test code."""
    prompt = _CODEGEN_PROMPT.format(app_url=APP_URL, gherkin_json=gherkin_json)
    result = llm_codegen.invoke([HumanMessage(content=prompt)])
    code = result.content.strip()
    if code.startswith("```python"):
        code = code[9:]
    elif code.startswith("```"):
        code = code[3:]
    if code.endswith("```"):
        code = code[:-3]
    return code.strip()


def playwright_executor_agent(test_code: str) -> dict:
    """Write test code to a temp file, run with pytest-playwright, return structured results."""
    results: dict = {
        "passed": 0,
        "failed": 0,
        "error": 0,
        "total": 0,
        "tests": [],
        "raw_output": "",
        "execution_error": None,
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        test_file   = os.path.join(tmpdir, "test_generated.py")
        report_file = os.path.join(tmpdir, "report.json")

        with open(test_file, "w", encoding="utf-8") as f:
            f.write(test_code)

        cmd = [
            sys.executable, "-m", "pytest", test_file,
            "--json-report",
            f"--json-report-file={report_file}",
            "--tb=short",
            "-v",
            "--browser", "chromium",
            "--headed",
        ]

        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
                cwd=tmpdir,
            )
            stdout = proc.stdout or ""
            stderr = proc.stderr or ""
            results["raw_output"] = stdout[-3000:] + ("\nSTDERR:\n" + stderr[-1000:] if stderr else "")

            if os.path.exists(report_file):
                with open(report_file, "r", encoding="utf-8") as f:
                    report = json.load(f)

                summary = report.get("summary", {})
                results["passed"] = summary.get("passed", 0)
                results["failed"] = summary.get("failed", 0)
                results["error"]  = summary.get("error", 0)
                results["total"]  = summary.get("total", 0)

                for test in report.get("tests", []):
                    outcome = test.get("outcome", "unknown")
                    longrepr = ""
                    if outcome != "passed":
                        raw = (
                            test.get("call", {}).get("longrepr", "") or
                            test.get("setup", {}).get("longrepr", "") or ""
                        )
                        if isinstance(raw, dict):
                            raw = raw.get("reprcrash", {}).get("message", "")
                        longrepr = str(raw)[:500]

                    results["tests"].append({
                        "name": test.get("nodeid", "").split("::")[-1],
                        "outcome": outcome,
                        "duration": round(test.get("duration", 0), 2),
                        "message": longrepr,
                    })
            else:
                results["execution_error"] = (
                    "No report file generated.\n" + results["raw_output"][:1000]
                )

        except subprocess.TimeoutExpired:
            results["execution_error"] = "Test execution timed out after 5 minutes."
        except Exception as e:
            results["execution_error"] = str(e)

    return results


def results_review_agent(gherkin_json: str, execution_results: dict) -> str:
    """LLM analysis of Playwright execution results — returns JSON string."""
    prompt = f"""You are a QA lead reviewing automated Playwright test results.

Application Under Test: {APP_URL}
Summary: {execution_results['total']} total | {execution_results['passed']} passed | {execution_results['failed']} failed | {execution_results['error']} errors

Per-Test Results:
{json.dumps(execution_results['tests'], indent=2)}

Original Gherkin (first 2000 chars):
{gherkin_json[:2000]}

Return a JSON object with EXACTLY this structure:
{{
  "overall_status": "Pass" | "Partial" | "Fail",
  "pass_rate": "X%",
  "summary": "2-3 sentence overview of the test run",
  "failed_analysis": [
    {{"test": "test_name", "likely_cause": "reason", "suggestion": "how to fix"}}
  ],
  "insights": ["observation 1", "observation 2"],
  "recommendations": ["actionable recommendation 1", "actionable recommendation 2"]
}}

Return ONLY valid JSON. No markdown fences. No prose.
"""
    result = llm_review.invoke([HumanMessage(content=prompt)])
    content = result.content.strip()
    if content.startswith("```json"):
        content = content[7:]
    elif content.startswith("```"):
        content = content[3:]
    if content.endswith("```"):
        content = content[:-3]
    return content.strip()
