# AgenticQAEngine — Architecture & Analysis

## Overview

**AgenticQAEngine** is an end-to-end agentic QA platform that takes a natural-language feature description and produces enterprise-grade BDD Gherkin scenarios, a Playwright Page Object Model test suite, and executes those tests — all driven by a multi-agent LangGraph pipeline backed by a Graph RAG knowledge layer.

The system targets a **Trade Processing Platform** domain (trade creation, approval, amendment, settlement, cancellation) but is generically structured for any requirements-driven test generation.

### 3-Phase User Workflow

```
① Generate Scenarios          ② Generate Tests              ③ Run Tests
  Gherkin BDD via RAG    →     Playwright POM          →    Saved Test Suites
  (chat prompt → AI)           (one-click codegen)          (re-run any time)
```

---

## System Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│  Next.js Frontend (port 3000)                                    │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │  ChatInterface.tsx                                          │ │
│  │  • Chat UI: send prompts, receive BDD scenarios             │ │
│  │  • AssistantCard: phase tracker (Scenarios→Tests→Run)       │ │
│  │  • LoadingIndicator: animated 6-step pipeline               │ │
│  │  • SuiteGeneratedPanel: Feature/POM/Test code tabs          │ │
│  │  • SavedSuitesPanel: visual pass/fail bar, re-run trigger   │ │
│  └─────────────────────────────────────────────────────────────┘ │
│  Next.js API Routes (proxy layer — /app/api/*)                   │
│    /api/generate           → POST /api/generate                  │
│    /api/playwright-generate→ POST /api/playwright-generate       │
│    /api/test-suites        → GET  /api/test-suites               │
│    /api/test-suites/[id]/run→POST /api/test-suites/{id}/run      │
│    /api/download           → POST /api/download                  │
│    /api/download-zip       → POST /api/download-zip              │
└────────────────────────┬─────────────────────────────────────────┘
                         │ HTTP
┌────────────────────────▼─────────────────────────────────────────┐
│  FastAPI Backend (port 8000)   backend/main.py                   │
│  • /api/generate           — runs LangGraph pipeline             │
│  • /api/playwright-generate— generates+saves POM suite           │
│  • /api/playwright-run     — generates+saves+executes suite      │
│  • /api/test-suites        — lists suites from suites.json       │
│  • /api/test-suites/{id}/run— re-runs saved suite                │
│  • /api/download           — streams Excel file                  │
│  • /api/download-zip       — streams ZIP bundle                  │
└────────┬───────────────────────────────┬─────────────────────────┘
         │                               │
┌────────▼──────────┐         ┌──────────▼──────────────────────────┐
│ LangGraph Pipeline│         │  Playwright Agent (playwright_agent) │
│ TestGenerationEngine│        │  • LLM codegen: .feature, POM, test │
│ 6 nodes (see below)│        │  • Saves to tests/ + suites.json    │
│ gpt-4o-mini        │        │  • pytest-playwright subprocess exec │
└────────┬──────────┘         └──────────────────────────────────────┘
         │
┌────────▼──────────────────────────────────────────────────────────┐
│  Knowledge Layer                                                  │
│  Neo4j Graph DB ──► RequirementGraphEngine (Graph RAG)            │
│  Confluence ──────► MCP server (requirement pages, test plans)    │
└───────────────────────────────────────────────────────────────────┘
```

---

## Technology Stack

| Layer | Component | Library / Tool |
|-------|-----------|---------------|
| Frontend | UI framework | Next.js 14 (App Router) |
| Frontend | Styling | Tailwind CSS |
| Frontend | Icons | lucide-react |
| Frontend | API client | `lib/api.ts` — typed fetch wrappers |
| Backend | HTTP server | FastAPI + uvicorn |
| Backend | Async bridge | `asyncio.to_thread` (runs sync LangGraph in event loop) |
| AI Pipeline | Orchestration | LangGraph `StateGraph` with conditional retry loop |
| AI Pipeline | LLM | `gpt-4o-mini` via `langchain_openai.ChatOpenAI` |
| AI Pipeline | RAG | `RequirementGraphEngine` — Neo4j graph + vector search |
| Test Codegen | Agent | `playwright_agent.py` — LLM-driven POM codegen |
| Test Execution | Runner | `pytest-playwright` (Chromium, headed mode) |
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
  └── [Pass OR retry_count >= 2]  ──► END
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

### LLM Instances

```python
llm          = ChatOpenAI(model="gpt-4o-mini", temperature=0.4)  # req understanding + dep mapping
llm_scenario = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)  # scenario generation
llm_gherkin  = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)  # gherkin (faithfulness > creativity)
llm_review   = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)  # review (consistency > creativity)
```

### Scenario Output Schema (10 Categories)

```json
{
  "use_case": "",
  "positive_scenarios": [],
  "negative_scenarios": [],
  "validation_scenarios": [],
  "authorization_scenarios": [],
  "dependency_scenarios": [],
  "workflow_transition_scenarios": [],
  "edge_case_scenarios": [],
  "cross_module_scenarios": [],
  "error_handling_scenarios": [],
  "audit_validation_scenarios": [],
  "important_notes": []
}
```

---

## Phase 2 — Playwright Test Generation (`playwright_agent.py`)

### Overview

`playwright_agent.py` takes the `final_output` Gherkin JSON from Phase 1 and uses an LLM to generate three files that form a complete Playwright + pytest-BDD test suite:

| File | Location | Description |
|------|----------|-------------|
| `{slug}.feature` | `tests/features/` | Cucumber feature file (Gherkin) |
| `{slug}_page.py` | `tests/pages/` | Page Object Model class (inherits `BasePage`) |
| `test_{slug}.py` | `tests/test_suites/` | pytest test file with all scenarios |

### Two Functions

**`generate_suite_only(gherkin_json)`** — Phase 2a (generate without running):
- Parses Gherkin JSON, extracts use case and scenarios
- Calls LLM with `_FEATURE_PROMPT`, `_POM_PROMPT`, `_TEST_PROMPT` in sequence
- Saves all 3 files to disk
- Registers suite in `tests/suites.json` manifest
- Returns `{suite_id, use_case, feature_content, page_content, test_content}`

**`generate_and_run_suite(gherkin_json)`** — Phase 2b (generate + execute):
- Calls `generate_suite_only()` first
- Then runs the suite via `rerun_suite()`

**`rerun_suite(suite_id)`** — Phase 3 (re-run any saved suite):
- Looks up suite in `suites.json` by ID
- Runs `pytest tests/test_suites/{test_file} --headed --json-report ...` as subprocess
- Parses JSON report → structured result dict
- Updates `last_run_at` and `last_results` in `suites.json`

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

Generated subclasses **must** override `login()` and `navigate()` to define page-specific setup. Key LLM prompt constraints:

- Use `.oxd-alert-content` for invalid credential errors (top-level banner)
- Use `.oxd-input-field-error-message` for empty field validation (inline "Required")
- Use `to_be_visible()` not `to_have_text("...")` for error assertions
- Use `assert_on_dashboard()` for successful login (redirect, no toast)
- Credentials: `Admin` / `admin123` (hardcoded, not placeholders)
- Mark untestable scenarios (non-admin users, session expiry, unauthenticated navigation) with `@pytest.mark.skip`

### Suite Manifest (`tests/suites.json`)

```json
{
  "suites": [
    {
      "id": "uuid4",
      "use_case": "User Login and Authentication",
      "slug": "user_login_and_authentication",
      "created_at": "2026-05-25T10:00:00",
      "scenario_count": 15,
      "feature_file": "features/user_login_and_authentication.feature",
      "page_file": "pages/user_login_and_authentication_page.py",
      "test_file": "test_suites/test_user_login_and_authentication.py",
      "last_run_at": "2026-05-25T11:00:00",
      "last_results": {
        "passed": 8,
        "failed": 2,
        "total": 10,
        "overall_status": "Partial"
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

All tests run with a 60-second timeout to handle OrangeHRM demo site rate limiting.

---

## Phase 3 — Test Execution & Results

Tests are executed via subprocess:

```python
subprocess.run([
    "python", "-m", "pytest",
    f"tests/test_suites/{test_file}",
    "--headed",
    "--json-report",
    f"--json-report-file={report_path}",
    "-v",
])
```

Results are parsed from the JSON report into:

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

### Component Tree

```
ChatInterface (main)
├── Header: AgenticQAEngine branding + Saved Test Suites button
├── Messages list
│   ├── User bubble
│   └── AssistantCard
│       ├── ReviewBadge (Pass/Needs Improvement/Fail)
│       ├── ScenarioBreakdown (collapsible type breakdown)
│       ├── Phase tracker: ✓ Scenarios → [○/✓] Tests → ○ Run
│       ├── SuiteGeneratedPanel (Feature/POM/Test tabs, after codegen)
│       └── Action buttons: Download Excel | Download All | Generate Tests
├── LoadingIndicator (animated pipeline steps)
└── SavedSuitesPanel (slide-in drawer)
    └── Suite cards: name, metadata, Never run badge / pass-fail bar, Run button
```

### Key UI Behaviours

**Empty state** — 3-step workflow diagram with suggested prompts:
- `① Generate Scenarios` (blue) → `② Generate Tests` (violet) → `③ Run Tests` (green)

**LoadingIndicator** — Animated step progression using `useState` + `useEffect`:
```typescript
// Steps light up one-by-one every 900ms
// Pending: gray  |  Active: blue + pulse ring  |  Done: green + ✓
```

**AssistantCard phase tracker** — Reflects real-time state:
- "Scenarios": always green ✓ (card exists = scenarios generated)
- "Tests": gray circle → violet spinner during generation → green ✓ when done
- "Run": gray circle → violet + clickable (opens Saved Test Suites) when tests generated

**SavedSuitesPanel pass/fail display**:
- Suite with results: `{passed}/{total} passed` label + proportional green/red bar
- Suite never run: `Never run` badge (gray)

### API Layer (`lib/api.ts`)

| Function | Endpoint | Purpose |
|----------|----------|---------|
| `generateTestCases()` | POST `/api/generate` | Run LangGraph pipeline |
| `generatePlaywrightTests()` | POST `/api/playwright-generate` | Generate+save POM suite |
| `runPlaywright()` | POST `/api/playwright-run` | Generate+save+run suite |
| `getTestSuites()` | GET `/api/test-suites` | List all saved suites |
| `rerunTestSuite(id)` | POST `/api/test-suites/{id}/run` | Re-run a saved suite |
| `downloadExcel()` | POST `/api/download` | Stream `.xlsx` download |
| `downloadZip()` | POST `/api/download-zip` | Stream `.zip` bundle |

All Next.js API routes use `export const dynamic = "force-dynamic"` and `cache: "no-store"` to bypass the App Router's default fetch caching.

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
├── backend/
│   ├── main.py                      # FastAPI app, all endpoints
│   ├── TestGenerationEngine.py      # LangGraph 6-node pipeline
│   ├── playwright_agent.py          # POM codegen + pytest execution
│   ├── excel_generator.py           # .xlsx export
│   ├── zip_generator.py             # .zip bundle export
│   └── prompts/                     # Prompt .txt files for each agent
├── frontend/
│   ├── app/
│   │   ├── layout.tsx               # AgenticQAEngine metadata
│   │   ├── page.tsx                 # Root page
│   │   └── api/                     # Next.js proxy routes (force-dynamic)
│   ├── components/
│   │   └── ChatInterface.tsx        # Full UI (chat, panels, drawers)
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

## Dependencies

```
# AI / Orchestration
langchain_openai     ← LLM interface (gpt-4o-mini)
langgraph            ← state machine (conditional edges, retry loop)
langchain_core       ← HumanMessage wrapper

# Backend
fastapi              ← REST API
uvicorn              ← ASGI server
pydantic             ← request/response models

# Test Execution
pytest               ← test runner
pytest-playwright    ← Playwright fixtures (headed Chromium)
pytest-json-report   ← structured JSON result output

# Exports
openpyxl             ← Excel generation
python-dotenv        ← .env config

# Knowledge Layer
neo4j                ← Graph DB driver
RequirementGraphEngine ← local RAG module
```

OpenAI API key must be present in `.env` as `OPENAI_API_KEY`.
