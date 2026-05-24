import os
import sys
import re
import json
import uuid
import tempfile
import subprocess
import datetime
from pathlib import Path
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

load_dotenv(override=True)

APP_URL = os.getenv("PLAYWRIGHT_APP_URL", "")

TESTS_DIR   = Path(__file__).parent.parent / "tests"
FEATURES_DIR = TESTS_DIR / "features"
PAGES_DIR    = TESTS_DIR / "pages"
SUITES_DIR   = TESTS_DIR / "test_suites"
MANIFEST     = TESTS_DIR / "suites.json"

llm_codegen = ChatOpenAI(model="gpt-4o",     temperature=0.1)
llm_review  = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _slugify(text: str) -> str:
    slug = re.sub(r"[^\w\s]", "", text.lower())
    slug = re.sub(r"[\s_]+", "_", slug).strip("_")
    return slug[:50]


def _class_name(slug: str) -> str:
    return "".join(w.capitalize() for w in slug.split("_")) + "Page"


def _strip_fences(code: str) -> str:
    code = code.strip()
    if code.startswith("```python"):
        code = code[9:]
    elif code.startswith("```"):
        code = code[3:]
    if code.endswith("```"):
        code = code[:-3]
    return code.strip()


def _load_manifest() -> dict:
    if MANIFEST.exists():
        return json.loads(MANIFEST.read_text(encoding="utf-8"))
    return {"suites": []}


def _save_manifest(data: dict) -> None:
    MANIFEST.write_text(json.dumps(data, indent=2), encoding="utf-8")


# ─── Agent 1: Cucumber .feature file ─────────────────────────────────────────

_FEATURE_PROMPT = """You are a BDD expert. Convert the Gherkin JSON below into a well-formed Cucumber .feature file.

Feature name: {use_case}

Rules:
- First line: Feature: {use_case}
- Add a Background: section if login appears in most scenarios (Given I am logged in as Admin)
- Each scenario_name → Scenario: <name>  (preserve type in a @tag)
- Convert given/when/then arrays into proper Gherkin step lines
- Use tags from the scenario tags field (prefix with @)
- Return ONLY the .feature file content. No markdown fences. No prose.

Gherkin JSON:
{gherkin_json}
"""

def feature_file_agent(gherkin_json: str, use_case: str) -> str:
    prompt = _FEATURE_PROMPT.format(use_case=use_case, gherkin_json=gherkin_json)
    result = llm_codegen.invoke([HumanMessage(content=prompt)])
    content = result.content.strip()
    if content.startswith("```"):
        content = "\n".join(content.split("\n")[1:])
    if content.endswith("```"):
        content = content[:-3]
    return content.strip()


# ─── Agent 2: Page Object Model ───────────────────────────────────────────────

_POM_PROMPT = """You are a senior Playwright automation engineer.
Generate a Page Object Model (POM) Python class for the OrangeHRM application.

Target URL  : {app_url}
Class name  : {class_name}
Base class  : BasePage  (already has login() and navigate_to(menu_item) methods)

━━━ ORANGEHRM LOCATOR REFERENCE ━━━
Nav links        : self.page.get_by_role("link", name="<Module>").first
Sub-menu items   : self.page.get_by_role("menuitem", name="<Item>")
Primary button   : self.page.get_by_role("button", name="<Label>")
Text input nth   : self.page.locator("input.oxd-input").nth(N)
Named textbox    : self.page.get_by_role("textbox", name="<Label>")
Custom dropdown  : self.page.locator(".oxd-select-text").nth(N).click()
                   self.page.get_by_role("option", name="<Value>").click()
Autocomplete     : self.page.locator(".oxd-autocomplete-text-input input").nth(N).fill("text")
                   self.page.locator(".oxd-autocomplete-option", has_text="text").first.click()
Table rows       : self.page.locator(".oxd-table-row")
Row actions      : self.page.locator(".oxd-table-cell-actions").nth(N)
Edit icon        : self.page.locator(".oxd-table-cell-actions .oxd-icon-button").nth(N)
Toast success    : self.page.locator(".oxd-toast--success")
Modal confirm    : self.page.get_by_role("button", name="Yes, Delete")
Checkbox         : self.page.locator(".oxd-checkbox-input").nth(N)
Date input       : self.page.locator("input.oxd-date-input").nth(N)

━━━ CODING RULES ━━━
- from base_page import BasePage
- from playwright.sync_api import Page, expect
- Inherit: class {class_name}(BasePage)
- __init__(self, page: Page): call super().__init__(page), define all locators as self.xxx
- Do NOT redefine login() — it's on BasePage
- navigate(): call self.navigate_to("<MainMenu>") then click sub-menus if needed,
  call self.page.wait_for_load_state("networkidle")
- One method per meaningful action (add_record, search, edit_record, delete_record, etc.)
- Methods should use self.page.wait_for_load_state("networkidle") after actions that navigate
- Return ONLY valid Python. No markdown fences. No prose. No comments.

Scenarios to model:
{gherkin_json}
"""

def page_object_agent(gherkin_json: str, use_case: str, class_name: str) -> str:
    prompt = _POM_PROMPT.format(app_url=APP_URL, use_case=use_case, class_name=class_name)
    result = llm_codegen.invoke([HumanMessage(content=prompt)])
    return _strip_fences(result.content)


# ─── Agent 3: pytest test suite ───────────────────────────────────────────────

_TEST_PROMPT = """You are a pytest-playwright test engineer.
Generate a COMPLETE pytest test file implementing ALL Gherkin scenarios using the Page Object Model.

POM class  : {class_name}
POM import : from pages.{module_name} import {class_name}

━━━ STRUCTURE RULES ━━━
Imports (top of file, exactly these):
    import re
    import pytest
    from playwright.sync_api import Page, expect
    from pages.{module_name} import {class_name}

Each scenario → one function:
    def test_<snake_case_scenario_name>(page: Page):
        obj = {class_name}(page)
        obj.login()
        obj.navigate()
        # ... use POM methods to implement all When/Then steps

Rules:
- EVERY scenario must be fully implemented using POM methods — no raw Playwright calls in tests
- Every test calls obj.login() then obj.navigate() at the start
- Use expect() for ALL assertions — never use assert statements
- Each test is fully independent
- CRITICAL: Do NOT skip any scenario. Implement all {scenario_count} scenarios.
- Return ONLY valid Python. No markdown fences. No prose. No comments.

Gherkin scenarios:
{gherkin_json}
"""

def test_suite_agent(gherkin_json: str, use_case: str, class_name: str, module_name: str, scenario_count: int) -> str:
    prompt = _TEST_PROMPT.format(
        use_case=use_case,
        class_name=class_name,
        module_name=module_name,
        scenario_count=scenario_count,
        gherkin_json=gherkin_json,
    )
    result = llm_codegen.invoke([HumanMessage(content=prompt)])
    return _strip_fences(result.content)


# ─── Persistence ──────────────────────────────────────────────────────────────

def save_suite_files(
    use_case: str,
    slug: str,
    feature_content: str,
    page_content: str,
    test_content: str,
    scenario_count: int,
) -> str:
    """Write feature / POM / test files, register in suites.json. Returns suite_id."""
    for d in (FEATURES_DIR, PAGES_DIR, SUITES_DIR):
        d.mkdir(parents=True, exist_ok=True)
    (PAGES_DIR / "__init__.py").touch()

    (FEATURES_DIR / f"{slug}.feature").write_text(feature_content, encoding="utf-8")
    (PAGES_DIR    / f"{slug}_page.py").write_text(page_content,    encoding="utf-8")
    (SUITES_DIR   / f"test_{slug}.py").write_text(test_content,    encoding="utf-8")

    suite_id = str(uuid.uuid4())[:8]
    manifest = _load_manifest()
    manifest["suites"] = [s for s in manifest["suites"] if s["slug"] != slug]
    manifest["suites"].append({
        "id":             suite_id,
        "use_case":       use_case,
        "slug":           slug,
        "created_at":     datetime.datetime.now().isoformat(),
        "feature_file":   f"features/{slug}.feature",
        "page_file":      f"pages/{slug}_page.py",
        "test_file":      f"test_suites/test_{slug}.py",
        "scenario_count": scenario_count,
        "last_run_at":    None,
        "last_results":   None,
    })
    _save_manifest(manifest)
    return suite_id


def update_suite_results(suite_id: str, execution_results: dict, review: str) -> None:
    review_data: dict = {}
    try:
        review_data = json.loads(review)
    except Exception:
        pass
    manifest = _load_manifest()
    for suite in manifest["suites"]:
        if suite["id"] == suite_id:
            suite["last_run_at"] = datetime.datetime.now().isoformat()
            suite["last_results"] = {
                "passed":         execution_results.get("passed", 0),
                "failed":         execution_results.get("failed", 0),
                "total":          execution_results.get("total", 0),
                "overall_status": review_data.get("overall_status", "Unknown"),
            }
            break
    _save_manifest(manifest)


# ─── Test runner ──────────────────────────────────────────────────────────────

def run_test_file(test_file: Path) -> dict:
    results: dict = {
        "passed": 0, "failed": 0, "error": 0, "total": 0,
        "tests": [], "raw_output": "", "execution_error": None,
    }
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        report_file = Path(f.name)

    cmd = [
        sys.executable, "-m", "pytest", str(test_file),
        "--json-report",
        f"--json-report-file={report_file}",
        "--tb=short", "-v",
        "--browser", "chromium",
        "--headed",
    ]
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
            cwd=str(TESTS_DIR),
        )
        stdout = proc.stdout or ""
        stderr = proc.stderr or ""
        results["raw_output"] = stdout[-3000:] + ("\nSTDERR:\n" + stderr[-1000:] if stderr else "")

        if report_file.exists():
            report = json.loads(report_file.read_text(encoding="utf-8"))
            summary = report.get("summary", {})
            results["passed"] = summary.get("passed", 0)
            results["failed"] = summary.get("failed", 0)
            results["error"]  = summary.get("error", 0)
            results["total"]  = summary.get("total", 0)
            for test in report.get("tests", []):
                outcome = test.get("outcome", "unknown")
                longrepr = ""
                if outcome != "passed":
                    raw = (test.get("call", {}).get("longrepr", "") or
                           test.get("setup", {}).get("longrepr", "") or "")
                    if isinstance(raw, dict):
                        raw = raw.get("reprcrash", {}).get("message", "")
                    longrepr = str(raw)[:500]
                results["tests"].append({
                    "name":     test.get("nodeid", "").split("::")[-1],
                    "outcome":  outcome,
                    "duration": round(test.get("duration", 0), 2),
                    "message":  longrepr,
                })
            report_file.unlink(missing_ok=True)
        else:
            results["execution_error"] = "No report generated.\n" + results["raw_output"][:1000]
    except subprocess.TimeoutExpired:
        results["execution_error"] = "Timed out after 5 minutes."
    except Exception as e:
        results["execution_error"] = str(e)

    return results


# ─── Results review ───────────────────────────────────────────────────────────

def results_review_agent(gherkin_json: str, execution_results: dict) -> str:
    prompt = f"""You are a QA lead reviewing automated Playwright test results.

Application: {APP_URL}
Summary: {execution_results['total']} total | {execution_results['passed']} passed | {execution_results['failed']} failed | {execution_results['error']} errors

Per-Test Results:
{json.dumps(execution_results['tests'], indent=2)}

Original Gherkin (first 2000 chars):
{gherkin_json[:2000]}

Return a JSON object with EXACTLY this structure:
{{
  "overall_status": "Pass" | "Partial" | "Fail",
  "pass_rate": "X%",
  "summary": "2-3 sentence overview",
  "failed_analysis": [{{"test": "name", "likely_cause": "reason", "suggestion": "fix"}}],
  "insights": ["observation 1"],
  "recommendations": ["recommendation 1"]
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


# ─── Main orchestration ───────────────────────────────────────────────────────

def generate_and_run_suite(gherkin_json: str) -> dict:
    """Generate feature + POM + tests → save to disk → run → return full results."""
    try:
        parsed = json.loads(gherkin_json)
    except Exception:
        parsed = {}

    use_case = parsed.get("use_case", "test_suite")
    scenarios = parsed.get("gherkin_scenarios", [])
    slug      = _slugify(use_case)
    cls_name  = _class_name(slug)
    mod_name  = f"{slug}_page"

    feature_content = feature_file_agent(gherkin_json, use_case)
    page_content    = page_object_agent(gherkin_json, use_case, cls_name)
    test_content    = test_suite_agent(gherkin_json, use_case, cls_name, mod_name, len(scenarios))

    suite_id = save_suite_files(use_case, slug, feature_content, page_content, test_content, len(scenarios))

    test_file = SUITES_DIR / f"test_{slug}.py"
    execution_results = run_test_file(test_file)

    review = "{}"
    try:
        review = results_review_agent(gherkin_json, execution_results)
    except Exception:
        pass

    update_suite_results(suite_id, execution_results, review)

    return {
        "suite_id":         suite_id,
        "use_case":         use_case,
        "feature_content":  feature_content,
        "page_content":     page_content,
        "test_content":     test_content,
        "execution_results": execution_results,
        "review":           review,
    }


def rerun_suite(suite_id: str) -> dict:
    """Re-run a previously saved test suite by ID."""
    manifest = _load_manifest()
    suite = next((s for s in manifest["suites"] if s["id"] == suite_id), None)
    if not suite:
        raise ValueError(f"Suite '{suite_id}' not found")

    test_file = TESTS_DIR / suite["test_file"]
    if not test_file.exists():
        raise FileNotFoundError(f"Test file missing: {test_file}")

    execution_results = run_test_file(test_file)
    review = "{}"
    update_suite_results(suite_id, execution_results, review)

    return {
        "suite_id":          suite_id,
        "use_case":          suite["use_case"],
        "execution_results": execution_results,
        "review":            review,
    }


def list_suites() -> list:
    return _load_manifest().get("suites", [])
