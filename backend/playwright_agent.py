import os
import sys
import re
import json
import uuid
import base64
import tempfile
import subprocess
import datetime
import difflib
from pathlib import Path
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

load_dotenv(override=True)

APP_URL = os.getenv("PLAYWRIGHT_APP_URL", "")

TESTS_DIR             = Path(__file__).parent.parent / "tests"
FEATURES_DIR          = TESTS_DIR / "features"
PAGES_DIR             = TESTS_DIR / "pages"
SUITES_DIR            = TESTS_DIR / "test_suites"
MANIFEST              = TESTS_DIR / "suites.json"
TEST_DATA_FILE        = TESTS_DIR / "test_data.json"
FAILURE_ARTIFACTS_DIR = TESTS_DIR / "failure_artifacts"
PROMPTS_DIR           = Path(__file__).parent / "prompts"

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


def _load_test_data() -> dict:
    if TEST_DATA_FILE.exists():
        return json.loads(TEST_DATA_FILE.read_text(encoding="utf-8"))
    return {"app": {}, "suites": {}}


def _merge_test_data(slug: str, suite_data: dict) -> None:
    td = _load_test_data()
    td.setdefault("suites", {})[slug] = suite_data
    TEST_DATA_FILE.write_text(json.dumps(td, indent=2), encoding="utf-8")


def _remove_test_data(slug: str) -> None:
    td = _load_test_data()
    td.get("suites", {}).pop(slug, None)
    TEST_DATA_FILE.write_text(json.dumps(td, indent=2), encoding="utf-8")


def _load_prompt(name: str) -> str:
    return (PROMPTS_DIR / f"{name}.md").read_text(encoding="utf-8")


# ─── Agent 0: Test data extraction ───────────────────────────────────────────

def test_data_agent(gherkin_json: str, use_case: str) -> dict:
    prompt = _load_prompt("test_data_agent").format(use_case=use_case, gherkin_json=gherkin_json)
    result = llm_codegen.invoke([HumanMessage(content=prompt)])
    content = result.content.strip()
    if content.startswith("```json"):
        content = content[7:]
    elif content.startswith("```"):
        content = content[3:]
    if content.endswith("```"):
        content = content[:-3]
    content = content.strip()
    try:
        data = json.loads(content)
        return {k: str(v) for k, v in data.items() if isinstance(v, (str, int, float, bool))}
    except Exception:
        return {}


# ─── Agent 1: Cucumber .feature file ─────────────────────────────────────────

def feature_file_agent(gherkin_json: str, use_case: str) -> str:
    prompt = _load_prompt("feature_file_agent").format(use_case=use_case, gherkin_json=gherkin_json)
    result = llm_codegen.invoke([HumanMessage(content=prompt)])
    content = result.content.strip()
    if content.startswith("```"):
        content = "\n".join(content.split("\n")[1:])
    if content.endswith("```"):
        content = content[:-3]
    return content.strip()


# ─── Agent 2: Page Object Model ───────────────────────────────────────────────

def page_object_agent(gherkin_json: str, use_case: str, class_name: str) -> str:
    prompt = _load_prompt("page_object_agent").format(app_url=APP_URL, use_case=use_case, class_name=class_name, gherkin_json=gherkin_json)
    result = llm_codegen.invoke([HumanMessage(content=prompt)])
    return _strip_fences(result.content)


# ─── Agent 3: pytest test suite ───────────────────────────────────────────────

def test_suite_agent(
    gherkin_json: str,
    use_case: str,
    class_name: str,
    module_name: str,
    scenario_count: int,
    page_content: str,
    slug: str = "",
    suite_test_data: dict | None = None,
) -> str:
    data_str = json.dumps(suite_test_data or {}, indent=2)
    prompt = _load_prompt("test_suite_agent").format(
        use_case=use_case,
        class_name=class_name,
        module_name=module_name,
        scenario_count=scenario_count,
        page_content=page_content,
        gherkin_json=gherkin_json,
        slug=slug,
        suite_test_data=data_str,
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


def save_approved_suite(
    use_case: str,
    slug: str,
    feature_content: str,
    page_content: str,
    test_content: str,
    scenario_count: int,
    suite_test_data: dict | None = None,
) -> str:
    """Save pre-generated content to disk and register in manifest. Returns suite_id."""
    suite_id = save_suite_files(use_case, slug, feature_content, page_content, test_content, scenario_count)
    if suite_test_data:
        _merge_test_data(slug, suite_test_data)
    return suite_id


def get_suite_files(suite_id: str) -> dict:
    """Read feature/POM/test file contents for a saved suite."""
    manifest = _load_manifest()
    suite = next((s for s in manifest["suites"] if s["id"] == suite_id), None)
    if not suite:
        raise ValueError(f"Suite '{suite_id}' not found")
    return {
        "suite_id":        suite_id,
        "use_case":        suite["use_case"],
        "feature_content": (TESTS_DIR / suite["feature_file"]).read_text(encoding="utf-8") if (TESTS_DIR / suite["feature_file"]).exists() else "",
        "page_content":    (TESTS_DIR / suite["page_file"]).read_text(encoding="utf-8")    if (TESTS_DIR / suite["page_file"]).exists()    else "",
        "test_content":    (TESTS_DIR / suite["test_file"]).read_text(encoding="utf-8")     if (TESTS_DIR / suite["test_file"]).exists()    else "",
    }


def delete_suite(suite_id: str) -> None:
    """Delete all generated files for a suite and remove from manifest."""
    manifest = _load_manifest()
    suite = next((s for s in manifest["suites"] if s["id"] == suite_id), None)
    if not suite:
        raise ValueError(f"Suite '{suite_id}' not found")
    for key in ("feature_file", "page_file", "test_file"):
        p = TESTS_DIR / suite[key]
        if p.exists():
            p.unlink()
    manifest["suites"] = [s for s in manifest["suites"] if s["id"] != suite_id]
    _save_manifest(manifest)
    _remove_test_data(suite["slug"])


def regenerate_scripts_for_suite(suite_id: str, feature_content: str, feedback: str) -> dict:
    """Re-generate POM + test for a saved suite using the (possibly edited) feature file as context. No save."""
    manifest = _load_manifest()
    suite = next((s for s in manifest["suites"] if s["id"] == suite_id), None)
    if not suite:
        raise ValueError(f"Suite '{suite_id}' not found")

    use_case      = suite["use_case"]
    slug          = suite["slug"]
    cls_name      = _class_name(slug)
    mod_name      = f"{slug}_page"
    scenario_count = suite.get("scenario_count", 0)

    suite_test_data = _load_test_data().get("suites", {}).get(slug, {})

    augmented = f"Feature file:\n{feature_content}\n\nReviewer feedback on scripts: {feedback}"
    page_content = page_object_agent(augmented, use_case, cls_name)
    test_content = test_suite_agent(
        augmented, use_case, cls_name, mod_name, scenario_count,
        page_content, slug=slug, suite_test_data=suite_test_data,
    )

    return {
        "use_case":    use_case,
        "slug":        slug,
        "page_content": page_content,
        "test_content": test_content,
    }


def update_suite_scripts(suite_id: str, feature_content: str, page_content: str, test_content: str) -> None:
    """Overwrite all 3 files for a saved suite and reset last_results (scripts changed, needs re-run)."""
    manifest = _load_manifest()
    suite = next((s for s in manifest["suites"] if s["id"] == suite_id), None)
    if not suite:
        raise ValueError(f"Suite '{suite_id}' not found")

    (TESTS_DIR / suite["feature_file"]).write_text(feature_content, encoding="utf-8")
    (TESTS_DIR / suite["page_file"]).write_text(page_content,    encoding="utf-8")
    (TESTS_DIR / suite["test_file"]).write_text(test_content,     encoding="utf-8")

    for s in manifest["suites"]:
        if s["id"] == suite_id:
            s["last_run_at"]  = None
            s["last_results"] = None
            break
    _save_manifest(manifest)


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

def run_test_file(test_file: Path, headed: bool = False) -> dict:
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
        "--timeout=60",  # per-test hard cap; Playwright action timeout is 15s
    ]
    if headed:
        cmd.append("--headed")
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=1200,
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
        results["execution_error"] = "Timed out after 20 minutes."
    except Exception as e:
        results["execution_error"] = str(e)

    return results


def run_single_test(suite_id: str, test_name: str, headed: bool = False) -> dict:
    """Run a single named test within a suite. Returns a PlaywrightExecutionResults dict."""
    manifest = _load_manifest()
    suite = next((s for s in manifest["suites"] if s["id"] == suite_id), None)
    if not suite:
        raise ValueError(f"Suite '{suite_id}' not found")

    test_file = TESTS_DIR / suite["test_file"]
    if not test_file.exists():
        raise ValueError(f"Test file not found: {suite['test_file']}")

    content = test_file.read_text(encoding="utf-8")
    class_match = re.search(r"^class\s+(\w+)", content, re.MULTILINE)
    # Use relative path + string concat — avoid Path("…::…") which is invalid on Windows
    if class_match:
        node_id = f"{suite['test_file']}::{class_match.group(1)}::{test_name}"
    else:
        node_id = f"{suite['test_file']}::{test_name}"

    results: dict = {
        "passed": 0, "failed": 0, "error": 0, "total": 0,
        "tests": [], "raw_output": "", "execution_error": None,
    }
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        report_file = Path(f.name)

    cmd = [
        sys.executable, "-m", "pytest", node_id,
        "--json-report",
        f"--json-report-file={report_file}",
        "--tb=short", "-v",
        "--browser", "chromium",
    ]
    if headed:
        cmd.append("--headed")

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

def generate_suite_preview(gherkin_json: str) -> dict:
    """Generate feature + POM + tests WITHOUT saving. Returns preview dict."""
    try:
        parsed = json.loads(gherkin_json)
    except Exception:
        parsed = {}

    use_case = parsed.get("use_case", "test_suite")
    scenarios = parsed.get("gherkin_scenarios", [])
    slug      = _slugify(use_case)
    cls_name  = _class_name(slug)
    mod_name  = f"{slug}_page"

    suite_test_data = test_data_agent(gherkin_json, use_case)
    feature_content = feature_file_agent(gherkin_json, use_case)
    page_content    = page_object_agent(gherkin_json, use_case, cls_name)
    test_content    = test_suite_agent(
        gherkin_json, use_case, cls_name, mod_name, len(scenarios),
        page_content, slug=slug, suite_test_data=suite_test_data,
    )

    return {
        "use_case":        use_case,
        "slug":            slug,
        "scenario_count":  len(scenarios),
        "feature_content": feature_content,
        "page_content":    page_content,
        "test_content":    test_content,
        "suite_test_data": suite_test_data,
    }


def regenerate_scripts(gherkin_json: str, feedback: str) -> dict:
    """Re-generate POM + test with reviewer feedback. Does NOT regenerate feature, does NOT save."""
    try:
        parsed = json.loads(gherkin_json)
    except Exception:
        parsed = {}

    use_case = parsed.get("use_case", "test_suite")
    scenarios = parsed.get("gherkin_scenarios", [])
    slug      = _slugify(use_case)
    cls_name  = _class_name(slug)
    mod_name  = f"{slug}_page"

    # Load existing test data for this slug (may not exist yet for preview regeneration)
    existing_td = _load_test_data()
    suite_test_data = existing_td.get("suites", {}).get(slug) or test_data_agent(gherkin_json, use_case)

    augmented = gherkin_json + f"\n\nReviewer feedback on scripts: {feedback}"
    page_content = page_object_agent(augmented, use_case, cls_name)
    test_content = test_suite_agent(
        augmented, use_case, cls_name, mod_name, len(scenarios),
        page_content, slug=slug, suite_test_data=suite_test_data,
    )

    return {
        "use_case":    use_case,
        "slug":        slug,
        "page_content": page_content,
        "test_content": test_content,
    }


def generate_suite_only(gherkin_json: str) -> dict:
    """Generate feature + POM + tests → save to disk. Does NOT run the tests."""
    preview  = generate_suite_preview(gherkin_json)
    suite_id = save_approved_suite(
        preview["use_case"],
        preview["slug"],
        preview["feature_content"],
        preview["page_content"],
        preview["test_content"],
        preview["scenario_count"],
        suite_test_data=preview.get("suite_test_data"),
    )
    return {
        "suite_id":        suite_id,
        "use_case":        preview["use_case"],
        "feature_content": preview["feature_content"],
        "page_content":    preview["page_content"],
        "test_content":    preview["test_content"],
    }


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

    suite_test_data = test_data_agent(gherkin_json, use_case)
    feature_content = feature_file_agent(gherkin_json, use_case)
    page_content    = page_object_agent(gherkin_json, use_case, cls_name)
    test_content    = test_suite_agent(
        gherkin_json, use_case, cls_name, mod_name, len(scenarios),
        page_content, slug=slug, suite_test_data=suite_test_data,
    )

    suite_id = save_suite_files(use_case, slug, feature_content, page_content, test_content, len(scenarios))
    if suite_test_data:
        _merge_test_data(slug, suite_test_data)

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


def rerun_suite(suite_id: str, headed: bool = False) -> dict:
    """Re-run a previously saved test suite by ID."""
    manifest = _load_manifest()
    suite = next((s for s in manifest["suites"] if s["id"] == suite_id), None)
    if not suite:
        raise ValueError(f"Suite '{suite_id}' not found")

    test_file = TESTS_DIR / suite["test_file"]
    if not test_file.exists():
        raise FileNotFoundError(f"Test file missing: {test_file}")

    execution_results = run_test_file(test_file, headed=headed)
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


# ─── Failure triage agent ─────────────────────────────────────────────────────

def _encode_screenshot(test_name: str) -> str | None:
    """Return base64-encoded PNG for a failed test, or None if not found."""
    path = FAILURE_ARTIFACTS_DIR / f"{test_name}.png"
    if path.exists():
        return base64.b64encode(path.read_bytes()).decode("utf-8")
    return None


def _triage_single_test(
    failure: dict,
    pom_content: str,
    test_content: str,
    feature_content: str,
    use_case: str,
    screenshot_b64: str | None,
) -> dict:
    """Triage one failed test. Uses GPT-4o vision when a screenshot is available."""
    has_vision = screenshot_b64 is not None

    vision_instruction = (
        "A full-page browser screenshot taken AT THE MOMENT OF FAILURE is attached.\n"
        "Use it to:\n"
        "  • Identify what is actually visible on the page (buttons, inputs, text, modals, banners)\n"
        "  • Find the correct element the test tried to interact with\n"
        "  • Propose a selector based on visible label text, placeholder, role, or aria-label\n"
        "  • Spot any visible error messages or unexpected UI state\n"
        "Base your proposed fix on what you SEE in the screenshot, not what you guess from HTML alone."
        if has_vision else
        "No screenshot available — base your analysis on the error message and DOM snapshot only."
    )

    prompt = _load_prompt("triage_agent").format(
        vision_instruction=vision_instruction,
        use_case=use_case,
        pom_content=pom_content[:12000],
        test_content=test_content[:12000],
        feature_content=feature_content[:4000],
        failure=json.dumps(failure, indent=2),
    )

    if has_vision:
        content: list = [
            {"type": "text", "text": prompt},
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{screenshot_b64}",
                    "detail": "high",
                },
            },
        ]
        msg = HumanMessage(content=content)
    else:
        msg = HumanMessage(content=prompt)

    raw = llm_codegen.invoke([msg]).content.strip()
    if raw.startswith("```json"):
        raw = raw[7:]
    elif raw.startswith("```"):
        raw = raw[3:]
    if raw.endswith("```"):
        raw = raw[:-3]
    raw = raw.strip()

    try:
        item = json.loads(raw)
        item["vision_used"] = has_vision
        return item
    except Exception:
        return {
            "test_name":    failure["test_name"],
            "category":     "product_defect",
            "confidence":   "low",
            "root_cause":   "Triage LLM returned unparseable JSON — review manually.",
            "proposed_fix": None,
            "vision_used":  False,
        }


def triage_failures_agent(suite_id: str, execution_results: dict) -> dict:
    """Classify each failed test using per-test vision-enhanced LLM calls."""
    manifest = _load_manifest()
    suite = next((s for s in manifest["suites"] if s["id"] == suite_id), None)
    if not suite:
        raise ValueError(f"Suite '{suite_id}' not found")

    pom_path     = PAGES_DIR    / suite["page_file"]
    test_path    = TESTS_DIR    / suite["test_file"]
    feature_path = FEATURES_DIR / suite["feature_file"]

    pom_content     = pom_path.read_text(encoding="utf-8")     if pom_path.exists()     else ""
    test_content    = test_path.read_text(encoding="utf-8")    if test_path.exists()    else ""
    feature_content = feature_path.read_text(encoding="utf-8") if feature_path.exists() else ""

    failed_tests = [t for t in execution_results.get("tests", []) if t["outcome"] != "passed"]
    if not failed_tests:
        return {"suite_id": suite_id, "triage": []}

    triage_list = []
    for t in failed_tests:
        dom_snapshot = ""
        dom_file = FAILURE_ARTIFACTS_DIR / f"{t['name']}.html"
        if dom_file.exists():
            dom_snapshot = dom_file.read_text(encoding="utf-8")[:3000]

        failure = {
            "test_name":     t["name"],
            "error_message": t.get("message", "")[:1000],
            "duration":      t.get("duration", 0),
            "dom_snapshot":  dom_snapshot,
        }

        screenshot_b64 = _encode_screenshot(t["name"])
        item = _triage_single_test(
            failure, pom_content, test_content, feature_content,
            suite["use_case"], screenshot_b64,
        )
        triage_list.append(item)

    triage_list = _validate_triage_fixes(triage_list, pom_content, test_content)
    return {"suite_id": suite_id, "triage": triage_list}


def _strip_lines(s: str) -> str:
    """Normalize CRLF → LF and strip trailing whitespace per line."""
    return "\n".join(line.rstrip() for line in s.replace("\r\n", "\n").split("\n"))


def _old_code_exists(content: str, old_code: str) -> bool:
    """Check whether old_code can be located using the same 3-pass logic as _apply_code_fix."""
    if old_code in content:
        return True
    if _strip_lines(old_code) in _strip_lines(content):
        return True
    c_lines = content.replace("\r\n", "\n").split("\n")
    o_lines = old_code.replace("\r\n", "\n").split("\n")
    while o_lines and not o_lines[0].strip():
        o_lines.pop(0)
    while o_lines and not o_lines[-1].strip():
        o_lines.pop()
    if not o_lines:
        return False
    o_stripped = [l.strip() for l in o_lines]
    n = len(o_stripped)
    for i in range(len(c_lines) - n + 1):
        if [l.strip() for l in c_lines[i : i + n]] == o_stripped:
            return True
    return False


def _find_actual_block(content: str, llm_old_code: str, threshold: float = 0.75) -> str | None:
    """Fuzzy-find the block in content most similar to llm_old_code; return actual file text or None."""
    c_lines = content.replace("\r\n", "\n").split("\n")
    o_lines = llm_old_code.replace("\r\n", "\n").split("\n")
    while o_lines and not o_lines[0].strip():
        o_lines.pop(0)
    while o_lines and not o_lines[-1].strip():
        o_lines.pop()
    if not o_lines:
        return None
    n = len(o_lines)
    o_key = "\n".join(l.strip() for l in o_lines)
    best_ratio = 0.0
    best_start = -1
    for i in range(max(1, len(c_lines) - n + 1)):
        block = c_lines[i : i + n]
        b_key = "\n".join(l.strip() for l in block)
        ratio = difflib.SequenceMatcher(None, o_key, b_key).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best_start = i
    if best_ratio >= threshold and best_start >= 0:
        return "\n".join(c_lines[best_start : best_start + n])
    return None


def _validate_triage_fixes(triage_items: list, pom_content: str, test_content: str) -> list:
    """
    Post-triage validation: verify each proposed_fix.old_code exists in the target file.
    If not found, attempt fuzzy correction. If still not found, mark fix_validated=False so
    the frontend can show the diff as a manual reference without offering auto-apply.
    """
    result = []
    for item in triage_items:
        fix = item.get("proposed_fix")
        if not fix or not fix.get("old_code") or not fix.get("new_code"):
            result.append(item)
            continue
        old_code = fix["old_code"]
        file_target = fix.get("file", "pom")
        content = pom_content if file_target == "pom" else test_content
        if _old_code_exists(content, old_code):
            item = dict(item)
            item["fix_validated"] = True
            result.append(item)
            continue
        actual = _find_actual_block(content, old_code, threshold=0.65)
        if actual is not None:
            item = dict(item)
            item["proposed_fix"] = dict(fix)
            item["proposed_fix"]["old_code"] = actual
            item["fix_validated"] = True
            result.append(item)
        else:
            # Keep the LLM diff visible as a manual reference — do not nullify
            item = dict(item)
            item["fix_validated"] = False
            result.append(item)
    return result


def _apply_code_fix(content: str, old_code: str, new_code: str) -> tuple[str, bool]:
    """
    Three-pass replacement with increasing tolerance for LLM whitespace drift.
    Pass 1 — exact substring match.
    Pass 2 — CRLF-normalized + trailing-whitespace-stripped match.
    Pass 3 — leading-whitespace-stripped line comparison (handles indentation drift);
             re-indents new_code to match the actual indentation found in the file.
    """
    # Pass 1: exact
    if old_code in content:
        return content.replace(old_code, new_code, 1), True

    # Pass 2: normalize line endings + trailing spaces
    nc = _strip_lines(content)
    no = _strip_lines(old_code)
    if no in nc:
        return nc.replace(no, _strip_lines(new_code), 1), True

    # Pass 3: strip ALL leading whitespace from each line for comparison,
    #         then re-indent the replacement using the matched block's actual indent.
    c_lines = content.replace("\r\n", "\n").split("\n")
    o_lines = old_code.replace("\r\n", "\n").split("\n")

    # Drop leading/trailing blank lines from the old_code pattern
    while o_lines and not o_lines[0].strip():
        o_lines.pop(0)
    while o_lines and not o_lines[-1].strip():
        o_lines.pop()
    if not o_lines:
        return content, False

    o_stripped = [l.strip() for l in o_lines]
    n = len(o_stripped)

    for i in range(len(c_lines) - n + 1):
        block = c_lines[i : i + n]
        if [l.strip() for l in block] == o_stripped:
            # Determine base indent from first non-empty line of the matched block
            first_non_empty = next((l for l in block if l.strip()), block[0])
            base_indent = len(first_non_empty) - len(first_non_empty.lstrip())
            indent_str = first_non_empty[:base_indent]  # preserve tabs vs spaces

            # Dedent new_code then re-indent with the matched block's base indent
            n_lines = new_code.replace("\r\n", "\n").split("\n")
            while n_lines and not n_lines[0].strip():
                n_lines.pop(0)
            while n_lines and not n_lines[-1].strip():
                n_lines.pop()

            new_base = min(
                (len(l) - len(l.lstrip()) for l in n_lines if l.strip()),
                default=0,
            )
            indented_new = []
            for l in n_lines:
                if not l.strip():
                    indented_new.append("")
                else:
                    rel = len(l) - len(l.lstrip()) - new_base
                    indented_new.append(indent_str + " " * max(0, rel) + l.lstrip())

            result = c_lines[:i] + indented_new + c_lines[i + n :]
            return "\n".join(result), True

    # Pass 4: fuzzy block replacement — find best matching block then do an
    # indentation-aware swap (covers cases where fix_validated=False slips through
    # or the LLM drifted slightly beyond what passes 1-3 tolerate).
    actual_block = _find_actual_block(content, old_code, threshold=0.5)
    if actual_block is not None:
        applied, ok = _apply_code_fix(content, actual_block, new_code)
        if ok:
            return applied, True

    return content, False


def apply_test_fix(suite_id: str, fixes: list) -> dict:
    """Apply a list of agent-proposed code fixes to POM or test files."""
    manifest = _load_manifest()
    suite = next((s for s in manifest["suites"] if s["id"] == suite_id), None)
    if not suite:
        raise ValueError(f"Suite '{suite_id}' not found")

    pom_path  = PAGES_DIR / suite["page_file"]
    test_path = TESTS_DIR / suite["test_file"]

    pom_content  = pom_path.read_text(encoding="utf-8")  if pom_path.exists()  else ""
    test_content = test_path.read_text(encoding="utf-8") if test_path.exists() else ""

    applied, errors = [], []

    for fix in fixes:
        file_target = fix.get("file", "pom")
        old_code    = fix.get("old_code", "")
        new_code    = fix.get("new_code", "")
        test_name   = fix.get("test_name", "")

        if not old_code or not new_code:
            errors.append({"test_name": test_name, "error": "Empty old_code or new_code"})
            continue

        if file_target == "pom":
            updated, ok = _apply_code_fix(pom_content, old_code, new_code)
            if ok:
                pom_content = updated
                applied.append({"test_name": test_name, "file": "pom"})
            else:
                errors.append({"test_name": test_name, "error": "old_code not found in POM file"})
        else:
            updated, ok = _apply_code_fix(test_content, old_code, new_code)
            if ok:
                test_content = updated
                applied.append({"test_name": test_name, "file": "test"})
            else:
                errors.append({"test_name": test_name, "error": "old_code not found in test file"})

    if any(f["file"] == "pom" for f in applied):
        pom_path.write_text(pom_content, encoding="utf-8")
    if any(f["file"] == "test" for f in applied):
        test_path.write_text(test_content, encoding="utf-8")

    return {
        "applied":      applied,
        "errors":       errors,
        "page_content": pom_content,
        "test_content": test_content,
    }
