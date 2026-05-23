import os
import json
import tempfile
import subprocess
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

load_dotenv(override=True)

APP_URL = os.getenv("PLAYWRIGHT_APP_URL", "")

llm_codegen = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)
llm_review  = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)

_CODEGEN_PROMPT = """You are a senior Playwright test automation engineer.

Convert the Gherkin BDD scenarios below into pytest-playwright Python test code.

Target application URL: {app_url}
OrangeHRM demo credentials: username=Admin, password=admin123

Common OrangeHRM selectors:
- Username input : page.get_by_placeholder("Username")
- Password input : page.get_by_placeholder("Password")
- Login button   : page.get_by_role("button", name="Login")
- Dashboard URL  : contains /dashboard/index after login

Coding rules:
- Each scenario → one `def test_<snake_case_scenario_name>(page: Page):` function
- Start every test: page.goto("{app_url}") then page.wait_for_load_state("networkidle")
- Use locators: page.locator(), page.get_by_label(), page.get_by_role(), page.get_by_placeholder(), page.get_by_text()
- Interactions: page.fill(), page.click(), page.select_option()
- Assertions: expect(page).to_have_url(...), expect(locator).to_be_visible(), expect(locator).to_have_text(), expect(locator).to_contain_text()
- For any login step always use the credentials above
- Each test is fully independent — starts fresh from the app URL
- Only fixtures allowed: `page`
- Top imports: `import pytest` and `from playwright.sync_api import Page, expect`
- Return ONLY valid Python. No markdown fences. No prose.

Gherkin Scenarios JSON:
{gherkin_json}
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
            "python", "-m", "pytest", test_file,
            "--json-report",
            f"--json-report-file={report_file}",
            "--tb=short",
            "-v",
            "--browser", "chromium",
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
