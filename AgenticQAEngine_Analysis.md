# AgenticQAEngine — Architecture & Analysis

## Overview

**AgenticQAEngine** is an end-to-end agentic QA platform that takes a natural-language feature description and produces enterprise-grade BDD Gherkin scenarios, a Playwright Page Object Model test suite, and executes those tests — all driven by a multi-agent LangGraph pipeline backed by a Graph RAG knowledge layer.

The system targets a **Trade Processing Platform** domain (trade creation, approval, amendment, settlement, cancellation) but is generically structured for any requirements-driven test generation.

### User Workflow (5 phases with Human-in-the-Loop)

```
① Generate Scenarios     ② Review Scenarios     ③ Review & Save Tests    ④ Run Tests
  Gherkin BDD via RAG  →  Human gate: approve,  →  Human gate: edit/     →  Saved Test Suites
  (chat prompt → AI)       feedback, upload JSON    re-gen scripts, save     (re-run any time)
```

Human checkpoints allow reviewers to:
- **Gate 1 (Scenario Review)**: inspect Gherkin scenarios by type, provide feedback to re-generate the full pipeline, or upload a modified JSON file before any code is generated
- **Gate 2 (Script Review)**: read and directly edit the generated Feature file, Page Object, and Test Code; provide feedback to re-generate only the scripts (feature file preserved); approve to persist the suite to disk

---

## System Architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│  Next.js Frontend (port 3000)                                            │
│  ┌───────────────────────────────────────────────────────────────────┐   │
│  │  ChatInterface.tsx                                                │   │
│  │  • Chat UI: send prompts, receive BDD scenarios                   │   │
│  │  • AssistantCard: WorkflowStage state machine                     │   │
│  │  • ScenarioReviewGate: approve/re-gen/upload JSON                 │   │
│  │  • ScriptReviewGate: edit tabs, re-gen with feedback, save        │   │
│  │  • SuiteSavedPanel: post-save confirmation                        │   │
│  │  • LoadingIndicator: animated 6-step pipeline                     │   │
│  │  • SavedSuitesPanel: expandable cards, file viewer, delete        │   │
│  └───────────────────────────────────────────────────────────────────┘   │
│  Next.js API Routes (proxy layer — /app/api/*)                           │
│    /api/generate                   → POST /api/generate                  │
│    /api/playwright-generate        → POST /api/playwright-generate       │
│    /api/playwright-save            → POST /api/playwright-save           │
│    /api/regenerate-scenarios       → POST /api/regenerate-scenarios      │
│    /api/regenerate-scripts         → POST /api/regenerate-scripts        │
│    /api/test-suites                → GET  /api/test-suites               │
│    /api/test-suites/[id]/run       → POST /api/test-suites/{id}/run      │
│    /api/test-suites/[id]/files     → GET  /api/test-suites/{id}/files    │
│    /api/test-suites/[id]           → DELETE /api/test-suites/{id}        │
│    /api/download                   → POST /api/download                  │
│    /api/download-zip               → POST /api/download-zip              │
└──────────────────────────────┬───────────────────────────────────────────┘
                               │ HTTP
┌──────────────────────────────▼───────────────────────────────────────────┐
│  FastAPI Backend (port 8000)   backend/main.py                           │
│                                                                          │
│  Scenario generation                                                     │
│  • POST /api/generate              — runs LangGraph pipeline             │
│  • POST /api/regenerate-scenarios  — re-runs pipeline with feedback      │
│                                                                          │
│  Script generation (no save until approved)                              │
│  • POST /api/playwright-generate   — generate preview (no save)          │
│  • POST /api/regenerate-scripts    — re-gen POM+test with feedback       │
│  • POST /api/playwright-save       — save approved scripts to disk       │
│  • POST /api/playwright-run        — generate+save+execute (legacy)      │
│                                                                          │
│  Suite management                                                        │
│  • GET  /api/test-suites           — list suites from suites.json        │
│  • GET  /api/test-suites/{id}/files— read feature/POM/test file contents │
│  • POST /api/test-suites/{id}/run  — re-run a saved suite                │
│  • DELETE /api/test-suites/{id}    — delete suite files + manifest entry │
│                                                                          │
│  Export                                                                  │
│  • POST /api/download              — streams Excel file                  │
│  • POST /api/download-zip          — streams ZIP bundle                  │
└────────┬─────────────────────────────────────┬────────────────────────────┘
         │                                     │
┌────────▼──────────┐             ┌────────────▼──────────────────────────┐
│ LangGraph Pipeline│             │  Playwright Agent (playwright_agent)   │
│ TestGenerationEngine│           │  • generate_suite_preview() — no save │
│ 6 nodes (see below)│            │  • save_approved_suite() — persist    │
│ gpt-4o-mini        │            │  • regenerate_scripts() — POM+test    │
└────────┬──────────┘             │  • get_suite_files() — read from disk │
         │                        │  • delete_suite() — remove files+entry│
         │                        │  • rerun_suite() — pytest subprocess  │
┌────────▼──────────────────────────────────────────────────────────────────┐
│  Knowledge Layer                                                          │
│  Neo4j Graph DB ──► RequirementGraphEngine (Graph RAG)                    │
│  Confluence ──────► MCP server (requirement pages, test plans)            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## Technology Stack

| Layer | Component | Library / Tool |
|-------|-----------|---------------|
| Frontend | UI framework | Next.js 14 (App Router) |
| Frontend | Styling | Tailwind CSS |
| Frontend | Icons | lucide-react |
| Frontend | API client | `lib/api.ts` — typed fetch wrappers |
| Backend | HTTP server | FastAPI + uvicorn (no `--reload`) |
| Backend | Async bridge | `asyncio.to_thread` (runs sync LangGraph in event loop) |
| AI Pipeline | Orchestration | LangGraph `StateGraph` with conditional retry loop |
| AI Pipeline | LLM (scenario) | `gpt-4o-mini` via `langchain_openai.ChatOpenAI` |
| AI Pipeline | LLM (codegen) | `gpt-4o` for feature/POM/test generation |
| AI Pipeline | LLM (review) | `gpt-4o-mini` for results review |
| AI Pipeline | RAG | `RequirementGraphEngine` — Neo4j graph + vector search |
| Test Codegen | Agent | `playwright_agent.py` — LLM-driven POM codegen |
| Test Execution | Runner | `pytest-playwright` (Chromium, headless, 600s timeout) |
| Test Execution | Reporting | `pytest-json-report` → parsed result dict |
| Persistence | Suite manifest | `tests/suites.json` |
| Knowledge | Graph DB | Neo4j (6 MCP tools) |
| Knowledge | Docs | Confluence (5 MCP tools) |
| Config | Environment | `python-dotenv` |

---

## Phase 1 — BDD Scenario Generation (LangGraph Pipeline)

### State Schema — `QuestionState`

```
QuestionState
├── question                ← input: natural-language feature description
├── run_id                  ← auto-generated: YYYYMMDD_HHMMSS_api (or _q{n} from CLI)
├── retrieved_context       ← RAG output from RequirementGraphEngine
├── structured_requirements ← JSON: business rules, validations, dependencies
├── dependency_mapping      ← JSON: prerequisite workflows, blockers, cross-module impacts
├── generated_scenarios     ← JSON: 10-category test scenarios
├── generated_gherkin       ← JSON: BDD Gherkin scenarios
├── review_feedback         ← JSON: coverage analysis, gaps, overall_review_status
├── final_output            ← copy of generated_gherkin (pipeline final value)
└── retry_count             ← int: max 2 retries (3 generation passes total)
```

### Pipeline Topology

```
START
  │
  ▼
[1] retrieve_context          reads: question
  │                           writes: retrieved_context, run_id
  │                           how: RequirementGraphEngine.retrieve_raw_context()
  ▼
[2] requirement_understanding reads: question, retrieved_context
  │                           writes: structured_requirements
  │                           llm: temp=0.4, RequirementUnderstanding_template.txt
  ▼
[3] dependency_mapping        reads: question, retrieved_context, structured_requirements
  │                           writes: dependency_mapping
  │                           llm: temp=0.4, Dependency_prompt.txt
  ▼
[4] scenario_generation  ◄────────────────────────────────────────────┐
  │                           reads: all above + review_feedback (retry)│
  │                           writes: generated_scenarios               │
  │                           llm: temp=0.3, Scenario_prompt.txt        │
  ▼                                                                     │
[5] gherkin_generation        reads: generated_scenarios               │
  │                           writes: generated_gherkin                │
  │                           llm: temp=0.1, Gherkin_prompt.txt        │
  ▼                                                                     │
[6] review_agent              reads: requirements, scenarios, gherkin  │
  │                           writes: review_feedback, final_output    │
  │                           llm: temp=0.1, Review_prompt.txt         │
  │                                                                     │
  ├── [Needs Improvement AND retry_count < 2] ────────────────────────►┘
  │
  └── [Pass OR retry_count >= 2]  ──► END (→ Scenario Review Gate)
```

### Retry Loop

```python
def _should_retry(state: QuestionState) -> str:
    if state.get("retry_count", 0) >= 2:
        return "end"
    try:
        fb = json.loads(strip_json_fences(state.get("review_feedback", "{}")))
        if fb.get("overall_review_status") == "Needs Improvement":
            return "retry"
    except Exception:
        pass
    return "end"
```

On retry, the loop re-enters at `scenario_generation` — RAG retrieval and requirement/dependency analysis are **not** re-run. The review agent's gap list (`missing_scenarios`, `missing_validation_coverage`, etc.) is injected as an explicit `IMPROVEMENT PASS` supplement into the scenario generation prompt.

### Scenario Re-generation (Human Feedback)

When the human reviewer provides feedback at Gate 1, `POST /api/regenerate-scenarios` re-runs the full LangGraph pipeline with an augmented question:

```python
augmented_question = request.question + "\n\nReviewer feedback: " + request.feedback
```

This allows targeted improvements (e.g. "add more edge cases for empty fields") without changing the original question. The result replaces `localFinalOutput` in the frontend state — the reviewer then decides to approve the new scenarios or iterate again.

---

## Phase 2 — Playwright Script Generation (`playwright_agent.py`)

### Overview

`playwright_agent.py` takes the `final_output` Gherkin JSON from Phase 1 (or re-generation) and uses an LLM to generate three files that form a complete Playwright + pytest test suite. Script generation is **split into preview and save** to support the human-in-the-loop review gate.

| File | Location | Description |
|------|----------|-------------|
| `{slug}.feature` | `tests/features/` | Cucumber feature file (Gherkin) |
| `{slug}_page.py` | `tests/pages/` | Page Object Model class (inherits `BasePage`) |
| `test_{slug}.py` | `tests/test_suites/` | pytest test file with all scenarios |

### Function Reference

**`generate_suite_preview(gherkin_json)`** — generate without saving (called by `/api/playwright-generate`):
- Parses Gherkin JSON, extracts use case and scenarios
- Calls LLM agents: `feature_file_agent` → `page_object_agent` → `test_suite_agent`
- Returns `{use_case, slug, scenario_count, feature_content, page_content, test_content}` — **no suite_id, nothing written to disk**

**`save_approved_suite(use_case, slug, feature_content, page_content, test_content, scenario_count)`** — persist approved scripts (called by `/api/playwright-save`):
- Writes all 3 files to `tests/features/`, `tests/pages/`, `tests/test_suites/`
- Registers suite in `tests/suites.json` manifest with a new UUID-8 `suite_id`
- Returns `suite_id`

**`regenerate_scripts(gherkin_json, feedback)`** — re-generate POM + test only (called by `/api/regenerate-scripts`):
- Appends feedback to the gherkin JSON prompt: `"\n\nReviewer feedback on scripts: {feedback}"`
- Re-runs `page_object_agent` and `test_suite_agent` only — **feature file is NOT regenerated**
- Returns `{use_case, slug, page_content, test_content}` (frontend merges into existing `previewData`, preserving `feature_content`)

**`get_suite_files(suite_id)`** — read saved files from disk:
- Looks up manifest entry by ID, reads the 3 files
- Returns `{suite_id, use_case, feature_content, page_content, test_content}`

**`delete_suite(suite_id)`** — remove suite entirely:
- Deletes the 3 files from disk (missing_ok)
- Removes the manifest entry from `suites.json`

**`generate_suite_only(gherkin_json)`** — generate + save in one call (legacy, used by `/api/playwright-run`):
- Delegates to `generate_suite_preview()` then `save_approved_suite()`
- Returns `{suite_id, use_case, feature_content, page_content, test_content}`

**`rerun_suite(suite_id)`** — re-run saved tests:
- Looks up manifest, runs `pytest` subprocess, updates `last_run_at` and `last_results`

### LLM Instances

```python
llm_codegen = ChatOpenAI(model="gpt-4o",      temperature=0.1)  # feature, POM, test generation
llm_review  = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)  # results review
```

### Page Object Model Design

Generated POM classes inherit from `BasePage` which provides:

```python
class BasePage:
    APP_URL = "https://opensource-demo.orangehrmlive.com"

    def goto_app(self) -> None:
        self.page.goto(self.APP_URL)
        self.page.wait_for_load_state("networkidle")

    def login(self, username="Admin", password="admin123") -> None:
        self.goto_app()
        self.page.get_by_placeholder("Username").fill(username)
        self.page.get_by_placeholder("Password").fill(password)
        self.page.get_by_role("button", name="Login").click()
        self.page.wait_for_url("**/dashboard/index")

    def navigate_to(self, menu_item: str) -> None:
        self.page.get_by_role("link", name=menu_item).first.click()
        self.page.wait_for_load_state("networkidle")
```

Key LLM prompt constraints enforced in `_POM_PROMPT`:

- Use `.oxd-alert-content` for invalid credential errors (top-level banner)
- Use `.oxd-input-field-error-message` for empty field validation (inline "Required")
- Use `to_be_visible()`, never `to_have_text("...")` for error assertions
- Use `assert_on_dashboard()` (URL match) for successful login assertions
- Credentials: `Admin` / `admin123` (hardcoded, not placeholders)
- Mark untestable scenarios (non-admin users, session expiry) with `@pytest.mark.skip`
- Login-page POM must override both `login()` and `navigate()` to interact with the login form

### Suite Manifest (`tests/suites.json`)

```json
{
  "suites": [
    {
      "id": "61cc8f0d",
      "use_case": "User Login",
      "slug": "user_login",
      "created_at": "2026-05-25T10:00:00",
      "scenario_count": 26,
      "feature_file": "features/user_login.feature",
      "page_file": "pages/user_login_page.py",
      "test_file": "test_suites/test_user_login.py",
      "last_run_at": "2026-05-25T11:00:00",
      "last_results": {
        "passed": 8,
        "failed": 8,
        "total": 26,
        "overall_status": "Unknown"
      }
    }
  ]
}
```

### conftest.py — Test Configuration

```python
@pytest.fixture(autouse=True)
def set_timeouts(page):
    page.set_default_navigation_timeout(60_000)
    page.set_default_timeout(60_000)
```

All tests run with a 60-second per-action timeout to handle OrangeHRM demo site rate limiting.

---

## Phase 3 — Test Execution & Results

Tests are executed headless via subprocess (no `--headed`; headless is 3-5× faster):

```python
cmd = [
    sys.executable, "-m", "pytest", str(test_file),
    "--json-report",
    f"--json-report-file={report_file}",
    "--tb=short", "-v",
    "--browser", "chromium",
]
proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600, cwd=str(TESTS_DIR))
```

Key constraints:
- `timeout=600` (10 minutes) — headless Chromium across 26 tests
- `cwd=TESTS_DIR` — ensures `from pages.xxx import` resolution
- Backend must run **without `--reload`** — uvicorn `--reload` restarts the process mid-run when watched files change, killing the in-flight subprocess

Results are parsed from the JSON report:

```typescript
interface PlaywrightExecutionResults {
  passed: number;
  failed: number;
  error: number;
  total: number;
  tests: PlaywrightTestResult[];   // name, outcome, duration, message per test
  raw_output: string;
  execution_error: string | null;
}
```

---

## Frontend — ChatInterface

### WorkflowStage State Machine

Each `AssistantCard` (one per AI response) manages an independent `WorkflowStage`:

```typescript
type WorkflowStage =
  | "scenario_review"         // Gate 1 open: showing ScenarioReviewGate
  | "regenerating_scenarios"  // Re-running full LangGraph pipeline
  | "generating_scripts"      // Calling /api/playwright-generate
  | "script_review"           // Gate 2 open: showing ScriptReviewGate
  | "regenerating_scripts"    // Calling /api/regenerate-scripts
  | "suite_saved";            // Suite persisted: showing SuiteSavedPanel
```

Transitions:

```
scenario_review
  ├── "Re-generate" → regenerating_scenarios → scenario_review (new localFinalOutput)
  └── "Approve & Generate Tests" → generating_scripts → script_review

script_review
  ├── "Re-generate Scripts" → regenerating_scripts → script_review (merged previewData)
  └── "Approve & Save Suite" → suite_saved
```

`localFinalOutput` starts from `message.data.final_output` and can be replaced by scenario re-generation or JSON file upload. `previewData` starts null, is set by `/api/playwright-generate`, and is updated (POM+test only, feature preserved) by `/api/regenerate-scripts`.

### Component Tree

```
ChatInterface (main)
├── Header: AgenticQAEngine branding + Saved Test Suites button
├── Messages list
│   ├── User bubble
│   └── AssistantCard
│       ├── ReviewBadge (Pass/Needs Improvement/Fail)
│       ├── Phase tracker: ✓ Scenarios → [○/✓] Tests → ○ Run
│       ├── ScenarioReviewGate  [stage=scenario_review | regenerating_scenarios]
│       │   ├── ScenarioBreakdown: grouped collapsible by type
│       │   ├── Feedback textarea → Re-generate Scenarios button
│       │   ├── Upload modified JSON button
│       │   └── Approve & Generate Tests → button
│       ├── Spinner [stage=generating_scripts | regenerating_scripts]
│       ├── ScriptReviewGate  [stage=script_review]
│       │   ├── Tabs: Feature File / Page Object / Test Code (editable textareas)
│       │   ├── Feedback textarea → Re-generate Scripts button
│       │   └── Approve & Save Suite button
│       ├── SuiteSavedPanel  [stage=suite_saved]
│       └── Download buttons: Excel | Download All
├── LoadingIndicator (animated 6-step pipeline steps)
└── SavedSuitesPanel (slide-in drawer)
    └── SuiteCard (per suite)
        ├── Header: use case, scenario count, timestamps, pass/fail bar, Run / Delete buttons
        ├── Expandable body (lazy loads files via GET /api/test-suites/{id}/files)
        │   ├── File paths (feature/page/test)
        │   └── File viewer tabs: Feature | Page Object | Test Code (read-only)
        └── Inline run results (PlaywrightResultsPanel after re-run)
```

### Key UI Behaviours

**Scenario Review Gate** (amber panel):
- Groups scenarios by type using collapsible `ScenarioTypeGroup` components
- File upload: reads JSON, validates `JSON.parse`, calls `onFinalOutputChange`
- Re-generate: passes feedback to parent → calls `POST /api/regenerate-scenarios` → replaces `localFinalOutput`
- Approve: calls `POST /api/playwright-generate` → sets `previewData` → transitions to `script_review`

**Script Review Gate** (violet panel):
- Editable textareas per tab, synced from `previewData` via `useEffect([previewData.page_content, previewData.test_content])` — feature tab not synced on regen since feature is preserved
- On "Approve & Save": passes locally edited content (not the server-generated content) to `POST /api/playwright-save`
- Re-generate: `setStage("regenerating_scripts")` hides the gate; on completion, merges `{ page_content, test_content }` into existing `previewData` preserving `feature_content`

**SavedSuitesPanel**:
- Expand/collapse: clicking header triggers lazy `GET /api/test-suites/{id}/files` (only on first expand)
- Delete: 2-click confirmation — first click shows "Confirm?" in red, second click within 5s deletes; `setTimeout` auto-resets to avoid accidental deletes
- Pass/fail bar: proportional green/red segments, "Never run" badge when `last_results === null`

**LoadingIndicator** — Animated step progression:
- Steps light up one-by-one every 900ms
- Pending: gray | Active: blue + pulse ring | Done: green + ✓

### API Layer (`lib/api.ts`)

| Function | Endpoint | Purpose |
|----------|----------|---------|
| `generateTestCases()` | POST `/api/generate` | Run LangGraph pipeline |
| `regenerateScenarios(question, feedback)` | POST `/api/regenerate-scenarios` | Re-run pipeline with feedback |
| `generatePlaywrightTests(final_output)` | POST `/api/playwright-generate` | Generate scripts preview (no save) |
| `regenerateScripts(final_output, feedback)` | POST `/api/regenerate-scripts` | Re-gen POM+test with feedback |
| `saveSuite(previewData)` | POST `/api/playwright-save` | Persist approved suite to disk |
| `getTestSuites()` | GET `/api/test-suites` | List all saved suites |
| `rerunTestSuite(id)` | POST `/api/test-suites/{id}/run` | Re-run a saved suite |
| `getSuiteFiles(id)` | GET `/api/test-suites/{id}/files` | Read file contents for suite |
| `deleteSuite(id)` | DELETE `/api/test-suites/{id}` | Delete suite files + manifest entry |
| `downloadExcel()` | POST `/api/download` | Stream `.xlsx` download |
| `downloadZip()` | POST `/api/download-zip` | Stream `.zip` bundle |

**Return type changes**: `generatePlaywrightTests()` now returns `SuitePreviewResponse` (no `suite_id` — suite is not saved at this stage).

### Node v24 + Next.js 14 — Dynamic Route Constraint

All Next.js dynamic `[id]` route handlers must extract the ID from `req.nextUrl.pathname` instead of `params` destructuring. `params` destructuring crashes the Jest compilation worker on Node v24:

```typescript
// WRONG — crashes Node v24
export async function GET(req, { params }: { params: { id: string } }) {
  const id = params.id;  // ← crashes
}

// CORRECT — all [id] routes use this pattern
export async function GET(req: NextRequest) {
  const segments = req.nextUrl.pathname.split("/");
  const id = segments[segments.length - 2]; // for .../[id]/sub-route
  // or segments[segments.length - 1]        // for .../[id]
}
```

---

## Agent Contribution Analysis

Empirical analysis based on run `20260521_221500_api` (Trade Amendment, 89.57s total, single pass).

### Timing and Output Sizes

| Agent | Time | Input chars | Output chars | Expansion |
|-------|------|------------|-------------|-----------|
| retrieve_context | 2.69s | — | 10,126 | — |
| requirement_understanding | 6.33s | 10,126 | 1,430 | 0.14× (compression) |
| dependency_mapping | 5.91s | 11,556 | 1,382 | 0.12× (compression) |
| scenario_generation | 11.66s | ~15,000 | 2,399 | 0.16× (compression) |
| gherkin_generation | **59.95s** | 2,399 | 15,874 | **6.6× (expansion)** |
| review_agent | 3.03s | ~21,000 | 723 | — |

The pipeline compresses 10k chars of raw knowledge to ~2.4k scenario names, then expands to 15.9k chars of Gherkin. Gherkin generation is 67% of total wall-clock time.

### Agent Value Summary

| Agent | Verdict | Rationale |
|-------|---------|-----------|
| retrieve_context | **Essential** | Only source of grounded domain facts |
| requirement_understanding | **Useful** | Compression + normalisation; mergeable with dep mapping |
| dependency_mapping | **Weakest case** | Mostly re-derives Agent 2; prompt rules override its output |
| scenario_generation | **Context-dependent** | High value for unknown domains; low marginal value for well-locked prompt domains |
| gherkin_generation | **Essential** | 67% of wall time, 6.6× output expansion, core deliverable |
| review_agent | **Essential** | Quality gate + retry trigger; cheap when passing, critical when not |

### Potential Optimisation

Agents 2 and 3 could be merged into a single *context normaliser* that produces both requirement and dependency structure in one LLM call — saving ~6s and ~12k prompt tokens of duplicated RAG content with no meaningful loss in output quality.

---

## Debug Infrastructure

Every pipeline node writes to `debug_outputs/<run_id>/`:

| File | Written by | Contents |
|------|-----------|----------|
| `00_pipeline_summary.json` | `review_agent` (final pass) | Timing, output sizes, file list |
| `01_retrieve_context.txt` | `retrieve_context` | Question + retrieved context |
| `02_requirement_understanding.txt` | `requirement_understanding_agent` | Prompt + LLM output |
| `03_dependency_mapping.txt` | `dependency_mapping_agent` | Prompt + LLM output |
| `04_scenario_generation.txt` | `scenario_generation_agent` | Prompt + raw response + cleaned JSON |
| `05_gherkin_generation.txt` | `gherkin_generation_agent` | Input scenarios + prompt + Gherkin JSON |
| `06_review_agent.txt` | `review_agent` (pass 1) | All inputs + review feedback |
| `06_review_agent_r2.txt` | `review_agent` (pass 2) | Same structure, retry pass |
| `07_final_output.txt` | `review_agent` (every pass) | Final Gherkin JSON |

---

## File Structure

```
TestCasesGenerator/
├── AgenticQAEngine_Analysis.md      # This document
├── backend/
│   ├── main.py                      # FastAPI app, all endpoints
│   ├── TestGenerationEngine.py      # LangGraph 6-node pipeline
│   ├── playwright_agent.py          # POM codegen + pytest execution
│   │                                #   generate_suite_preview, save_approved_suite,
│   │                                #   regenerate_scripts, get_suite_files, delete_suite
│   ├── excel_generator.py           # .xlsx export
│   ├── zip_generator.py             # .zip bundle export
│   └── prompts/                     # Prompt .txt files for each agent
├── frontend/
│   ├── app/
│   │   ├── layout.tsx               # AgenticQAEngine metadata
│   │   ├── page.tsx                 # Root page
│   │   └── api/                     # Next.js proxy routes
│   │       ├── generate/route.ts
│   │       ├── playwright-generate/route.ts
│   │       ├── playwright-save/route.ts      ← NEW
│   │       ├── regenerate-scenarios/route.ts ← NEW
│   │       ├── regenerate-scripts/route.ts   ← NEW
│   │       ├── download/route.ts
│   │       ├── download-zip/route.ts
│   │       └── test-suites/
│   │           ├── route.ts                  # GET list
│   │           └── [id]/
│   │               ├── route.ts              ← NEW (DELETE)
│   │               ├── run/route.ts          # POST run
│   │               └── files/route.ts        ← NEW (GET files)
│   ├── components/
│   │   └── ChatInterface.tsx        # Full UI — chat, review gates, panels
│   └── lib/
│       └── api.ts                   # Typed fetch client for all endpoints
├── tests/
│   ├── conftest.py                  # 60s timeout autouse fixture
│   ├── suites.json                  # Suite manifest (id, files, last results)
│   ├── pages/
│   │   ├── base_page.py             # BasePage: goto_app, login, navigate_to
│   │   └── *_page.py                # Generated POM classes (one per suite)
│   ├── features/
│   │   └── *.feature                # Generated Gherkin feature files
│   └── test_suites/
│       └── test_*.py                # Generated pytest test files
└── mcp_servers/
    ├── neo4j_mcp_server.py          # 6 Neo4j tools (Graph RAG)
    └── confluence_mcp_server.py     # 5 Confluence tools (requirements)
```

---

## Backend Startup

The backend must be started **without `--reload`** to prevent uvicorn from killing in-flight test runs when source files change mid-execution:

```bash
# Correct — no hot reload
.venv/Scripts/python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000

# Incorrect — file watcher restarts server mid-run, killing subprocess tests
.venv/Scripts/python.exe -m uvicorn backend.main:app --reload
```

At startup, `build_question_agent_graph()` and embedding weights are loaded once and shared across all requests, avoiding re-loading on each call.

---

## Dependencies

```
# AI / Orchestration
langchain_openai     ← LLM interface (gpt-4o, gpt-4o-mini)
langgraph            ← state machine (conditional edges, retry loop)
langchain_core       ← HumanMessage wrapper

# Backend
fastapi              ← REST API
uvicorn              ← ASGI server (run without --reload)
pydantic             ← request/response models

# Test Execution
pytest               ← test runner
pytest-playwright    ← Playwright fixtures (headless Chromium)
pytest-json-report   ← structured JSON result output

# Exports
openpyxl             ← Excel generation
python-dotenv        ← .env config

# Knowledge Layer
neo4j                ← Graph DB driver
RequirementGraphEngine ← local RAG module
```

OpenAI API key must be present in `.env` as `OPENAI_API_KEY`.
