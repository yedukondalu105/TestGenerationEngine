# TestGenerationEngine.py — Architecture & Analysis

## Overview

`TestGenerationEngine.py` is an AI-driven QA test generation orchestration engine. Given a natural-language question (e.g., *"Generate test cases for Trade Amendment"*), it automatically produces enterprise-grade BDD Gherkin test scenarios by running a multi-agent LangGraph pipeline.

The engine targets a **Trade Processing Platform** domain (trade creation, approval, amendment, settlement, cancellation) but is generically structured for any requirements-driven test generation.

---

## Technology Stack

| Component | Library / Tool |
|-----------|---------------|
| LLM | `gpt-4o-mini` via `langchain_openai.ChatOpenAI` (4 separate instances) |
| Orchestration | `langgraph` — `StateGraph` with conditional retry loop |
| RAG Knowledge Layer | `RequirementGraphEngine` (local module) |
| Prompt Management | Plain `.txt` files in `prompts/` directory |
| Environment Config | `python-dotenv` |
| Debug Output | Structured per-run files under `debug_outputs/<run_id>/` |

---

## LLM Instances

Four separate `ChatOpenAI` instances are created at module level, each tuned for its specific role:

```python
llm          = ChatOpenAI(model="gpt-4o-mini", temperature=0.4)  # requirement_understanding + dependency_mapping
llm_scenario = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)  # scenario_generation
llm_gherkin  = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)  # gherkin_generation (faithfulness > creativity)
llm_review   = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)  # review_agent (consistency > creativity)
```

Lower temperature for Gherkin and Review agents enforces deterministic, consistent outputs — critical for structured JSON generation and duplicate detection.

---

## State Schema — `QuestionState`

All nodes share a single typed state dictionary that flows through the pipeline.

```
QuestionState
├── question                ← input: the user's natural-language question
├── run_id                  ← auto-generated on first node: YYYYMMDD_HHMMSS_api (or _q{n} from CLI)
├── retrieved_context       ← RAG output from RequirementGraphEngine
├── structured_requirements ← JSON: extracted business rules, validations, dependencies
├── dependency_mapping      ← JSON: prerequisite workflows, blockers, cross-module impacts
├── generated_scenarios     ← JSON: categorized test scenarios (10 categories)
├── generated_gherkin       ← JSON: BDD Gherkin scenarios
├── review_feedback         ← JSON: coverage analysis, gaps, improvements
├── final_output            ← copy of generated_gherkin (pipeline final value)
└── retry_count             ← int: incremented by review_agent each pass; max 2 retries
```

`run_id` is set by `retrieve_context` when not already present in the initial state (API path). The `retry_count` starts at `0` and is incremented to `1` after the first review pass, `2` after the second.

---

## Pipeline — Node-by-Node

The pipeline is **not purely linear**. After the review node, a conditional edge routes back to `scenario_generation` if quality is insufficient.

```
START
  │
  ▼
[1] retrieve_context
  │   reads:   question
  │   writes:  retrieved_context, run_id
  │   how:     calls RequirementGraphEngine.retrieve_raw_context()
  │            auto-generates run_id if not in initial state
  │
  ▼
[2] requirement_understanding
  │   reads:   question, retrieved_context
  │   writes:  structured_requirements
  │   llm:     llm (temperature=0.4)
  │   prompt:  RequirementUnderstanding_template.txt
  │   output:  JSON with module, actors, preconditions, business_rules,
  │            validations, workflow_states, allowed/blocked transitions,
  │            authorization_rules, dependencies, apis, error_conditions
  │
  ▼
[3] dependency_mapping
  │   reads:   question, retrieved_context, structured_requirements
  │   writes:  dependency_mapping
  │   llm:     llm (temperature=0.4)
  │   prompt:  Dependency_prompt.txt
  │   output:  JSON with prerequisite_workflows, upstream_dependencies,
  │            downstream_impacts, blocked_by, blocking_operations,
  │            authorization_dependencies, workflow_sequence,
  │            blocked_workflow_transitions, cross_module_impacts
  │
  ▼
[4] scenario_generation  ◄──────────────────────────────────────┐
  │   reads:   question, retrieved_context, structured_requirements,  │
  │            dependency_mapping, review_feedback (retry passes)     │
  │   writes:  generated_scenarios                                    │
  │   llm:     llm_scenario (temperature=0.3)                        │
  │   prompt:  Scenario_prompt.txt + retry_supplement (if retry>0)   │
  │   output:  JSON with 10 scenario categories (see below)          │
  │                                                                   │
  ▼                                                                   │
[5] gherkin_generation                                               │
  │   reads:   generated_scenarios                                    │
  │   writes:  generated_gherkin                                     │
  │   llm:     llm_gherkin (temperature=0.1)                         │
  │   prompt:  Gherkin_prompt.txt                                    │
  │   output:  JSON with gherkin_scenarios[] each containing         │
  │            scenario_type, scenario_name, gherkin (Given/When/Then)│
  │                                                                   │
  ▼                                                                   │
[6] review_agent                                                     │
  │   reads:   structured_requirements, dependency_mapping,          │
  │            generated_scenarios, generated_gherkin                │
  │   writes:  review_feedback, final_output, retry_count            │
  │   llm:     llm_review (temperature=0.1)                          │
  │   prompt:  Review_prompt.txt                                     │
  │   output:  JSON with coverage_summary, missing_scenarios,        │
  │            duplicate_scenarios, weak_scenarios, gherkin_issues,  │
  │            recommended_improvements, overall_review_status        │
  │                                                                   │
  ├── [overall_review_status == "Needs Improvement" AND retry_count < 2] ──►─┘
  │
  └── [Pass OR retry_count >= 2]
        │
        ▼
       END
```

---

## Retry Loop — `_should_retry`

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

- Returns `"retry"` → routes back to `scenario_generation` (skips RAG, requirement understanding, and dependency mapping — reuses existing context)
- Returns `"end"` → routes to `END`
- Hard cap: maximum 2 review passes (3 scenario generation passes total)
- Wired via: `graph.add_conditional_edges("review_agent", _should_retry, {"retry": "scenario_generation", "end": END})`

---

## Retry Supplement — Injected Missing Scenario Hints

On retry passes (`retry_count > 0`), `scenario_generation_agent` reads the previous review feedback and injects a supplement block into the scenario generation prompt:

```python
if retry_count > 0:
    missing = (
        fb.get("missing_scenarios", [])
        + fb.get("missing_validation_coverage", [])
        + fb.get("missing_edge_cases", [])
        + fb.get("missing_error_handling", [])
        + fb.get("missing_dependency_coverage", [])
        + fb.get("missing_authorization_coverage", [])
    )
    retry_supplement = (
        f"IMPROVEMENT PASS {retry_count} — ADD MISSING SCENARIOS\n"
        "You MUST add scenarios covering ALL of the following gaps ...\n"
        + "\n".join(f"- {m}" for m in missing)
    )
```

This converts the review agent's quality gap list directly into generation instructions for the next pass.

---

## Scenario Generation Output Schema (10 Categories)

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

`scenario_generation_agent` has a structured fallback: on any `Exception`, it returns this empty skeleton JSON so the pipeline can continue without crashing.

---

## Agent Roles

### 1. retrieve_context
Delegates to `RequirementGraphEngine` (Graph RAG). Calls `retrieve_raw_context()` — raw graph relationships + vector chunks — so downstream agents receive factual knowledge-base content rather than a pre-interpreted LLM answer. Also auto-generates `run_id` using `YYYYMMDD_HHMMSS_api` format when invoked from the API.

### 2. requirement_understanding_agent
Acts as a **business analyst**. Extracts and normalizes requirement intelligence into structured JSON. Key extractions: preconditions/postconditions, business rules, workflow state transitions (allowed and blocked), authorization rules, APIs, error codes, and cross-module dependencies.

### 3. dependency_mapping_agent
Acts as a **dependency analyst**. Maps all workflow relationships before scenario generation begins. Key extractions: prerequisite and upstream workflows, downstream impacts, blocker relationships (e.g., Settlement blocks Amendment), workflow sequence ordering, authorization and validation dependencies, cross-module impacts.

### 4. scenario_generation_agent
Acts as a **senior QA engineer**. Generates 10 categories of test scenarios using the structured requirements and dependency mapping. On retry passes, additionally consumes the review feedback gap list to fill identified holes.

| Category | Description |
|---|---|
| Positive | Happy-path successful operations |
| Negative | Invalid / rejected operations |
| Validation | Field and business rule validation (boundary inputs) |
| Authorization | Role-based access control checks |
| Dependency-aware | Prerequisite workflow enforcement |
| Workflow transition | State machine transition validation |
| Edge case | Boundary conditions |
| Cross-module | Multi-module integration impacts |
| Error handling | System error response structure validation |
| Audit validation | Audit logging requirements |

### 5. gherkin_generation_agent
Acts as a **BDD automation engineer**. Converts plain scenario descriptions into executable Cucumber/Playwright-compatible Gherkin syntax. Each output scenario contains `scenario_type`, `scenario_name`, and a `gherkin` string (multi-line `Given / When / Then / And`).

### 6. review_agent
Acts as a **senior QA reviewer / critic**. Reviews the full pipeline output to produce a quality report covering coverage gaps, duplicate detection, weak scenario identification, Gherkin syntax quality, and an `overall_review_status` of `Pass` / `Needs Improvement` / `Fail`.

- Increments `retry_count` before returning.
- Always writes `07_final_output.txt` with the latest Gherkin.
- Writes `06_review_agent.txt` on pass 1; `06_review_agent_r2.txt` on pass 2.
- Only writes `00_pipeline_summary.json` on the **final** pass (when no retry will follow).

> `final_output` is set to the Gherkin (not the review). The review is advisory quality metadata.

---

## Agent Contribution Analysis

Empirical analysis based on run `20260521_221500_api` (Trade Amendment, 89.57s total, single pass — review returned Pass immediately).

### Timing and output sizes

| Agent | Time | Input chars | Output chars | Expansion |
|-------|------|------------|-------------|-----------|
| retrieve_context | 2.69s | — | 10,126 | — |
| requirement_understanding | 6.33s | 10,126 | 1,430 | 0.14× (compression) |
| dependency_mapping | 5.91s | 11,556 | 1,382 | 0.12× (compression) |
| scenario_generation | 11.66s | ~15,000 | 2,399 | 0.16× (compression) |
| gherkin_generation | **59.95s** | 2,399 | 15,874 | **6.6× (expansion)** |
| review_agent | 3.03s | ~21,000 | 723 | — |

The pipeline compresses 10k chars of raw knowledge down to ~2.4k scenario names, then expands to 15.9k chars of Gherkin. Gherkin generation is 67% of total wall-clock time.

---

### Agent 1 — retrieve_context · Essential

Pulls grounded facts from Confluence via Graph RAG: 13 typed relationship triples (`REQUIRES`, `DEPENDENCY`, `ERROR_CODE`) plus 8 unstructured text chunks containing the actual business rules (*"only approved trades can be amended"*, *"amendment reason mandatory"*, settlement blocking, error codes, auth rules). This is the only node that knows what the actual system does — every downstream agent would hallucinate without it.

---

### Agent 2 — requirement_understanding · Useful but thin

Compresses 10,126 chars of mixed graph/text RAG output into 1,430 chars of clean structured JSON. Genuine contributions:
- Makes `allowed_transitions` and `blocked_transitions` explicit as typed fields
- Extracts `actors`, `postconditions`, `apis` — things not present in graph triples
- Normalises inconsistent wording across multiple Confluence chunks

**Limitation**: The output is almost a direct restatement of the RAG content — it formats rather than reasons. Every field maps 1:1 to something already present in the retrieved context. It acts as a structured formatter, not an analyst.

---

### Agent 3 — dependency_mapping · Most redundant in the current design

Receives both the RAG (10,126 chars) and the structured requirements (1,430 chars) — the same information twice — and produces another 1,382 chars of JSON. Fields it adds over Agent 2:

| New field | Value added |
|-----------|------------|
| `blocked_by: ["Settlement"]` | Already implied by Agent 2's `blocked_transitions` |
| `cross_module_impacts` | Partially duplicates Agent 2's `related_modules` |
| `workflow_sequence` | Derivable from Agent 2's `dependencies` + `allowed_transitions` |
| `dependency_risks` | Interesting, but not consumed by any downstream agent in a traceable way |

**Core problem**: `Scenario_prompt.txt` contains locked `REQUIRED NET-NEW SCENARIOS` rules that mandate dependency, cross-module, and workflow-transition scenarios by name regardless of what this agent outputs. The scenario agent would produce identical scenarios if Agent 3's output were empty because the prompt rules override the context. Agents 2 and 3 together cost ~12s and ~12k tokens of repeated RAG text for marginal differentiated value.

---

### Agent 4 — scenario_generation · Prompt follower in this domain

Produces 35 scenario names across 10 categories. For the Trade Amendment domain, `Scenario_prompt.txt` contains a locked `OUTPUT EXAMPLE` with the exact scenario names, exact category assignments, and exact input values (qty=-1, price=-100.00, "abc", "INVALID-ID", etc.). The agent's job is close to transcribing this example using the context as confirmation rather than derivation.

**Where it earns its cost**: For a completely new domain with no locked example, all the context from Agents 2 and 3 becomes essential — the agent must derive scenario categories and inputs from scratch. For Trade Amendment specifically, the prompt engineering has essentially pre-encoded the answer.

---

### Agent 5 — gherkin_generation · Does the most actual work

The only agent where output is substantially larger than input (6.6× expansion). Converts 35 plain scenario names into 15,874 chars of executable BDD Gherkin, applying 21 wording/category/input rules, concrete test data rules, and per-category differentiation rules. The quality of the final output is almost entirely determined by this agent — the reason the project required 10+ rounds of prompt engineering was almost exclusively about fixing this agent's output.

The 59.95s cost reflects the volume: generating consistent `Given / When / Then / And` blocks for 35 scenarios while maintaining cross-scenario consistency (no duplicate Given+When+Then pairs, correct error codes, correct audit assertions per scenario type).

---

### Agent 6 — review_agent · Safety net — high value when triggered

In clean runs it returns `Pass` in ~3s at negligible cost. Its value is conditional: when it fires the retry loop (status = `Needs Improvement`), it injects the gap list back into Agent 4 as explicit instructions, which in earlier runs caught real missing scenarios (missing 3rd Audit scenario, wrong error codes in Dependency scenarios, cross-category duplicates). The 39-rule review prompt acts as a compiled quality specification that prevents regression.

---

### Summary — value per agent

| Agent | Verdict | Rationale |
|-------|---------|-----------|
| retrieve_context | **Essential** | Only source of grounded domain facts |
| requirement_understanding | **Useful** | Compression + normalisation; mergeable with dep mapping |
| dependency_mapping | **Weakest case** | Mostly re-derives what Agent 2 already has; prompt rules make its output less load-bearing |
| scenario_generation | **Context-dependent** | High value for unknown domains; low marginal value for well-locked prompt domains |
| gherkin_generation | **Essential** | 67% of wall time, 6.6× output expansion, core deliverable |
| review_agent | **Essential** | Quality gate + retry trigger; cheap in passing runs, critical in failing ones |

### Potential optimisation

Agents 2 and 3 could be merged into a single *context normaliser* agent that produces both requirement and dependency structure in one LLM call. This would save one round-trip (~6s, ~12k prompt tokens of duplicated RAG content) with no meaningful loss in output quality for the current use case. The separation adds value primarily when the domain is unfamiliar and the dependency structure cannot be inferred from a single pass.

---

## Debug Infrastructure

Every node writes a structured debug file to `debug_outputs/<run_id>/`. A per-run timing registry (`_run_timings`) accumulates node wall-clock times and output sizes.

### `save_stage_output(stage_name, sections, run_id, elapsed)`
Writes a formatted `.txt` file with a standardized header (stage name, run ID, timestamp, elapsed seconds) followed by named sections (prompt sent, raw LLM response, cleaned output, etc.).

### `_record_timing(run_id, node, elapsed, output_chars)`
Appends a timing record to `_run_timings[run_id]`. Used to build the pipeline summary.

### `save_pipeline_summary(state, run_id)`
Writes `00_pipeline_summary.json` — called only on the final review pass. Contains:

```json
{
  "run_id": "...",
  "question": "...",
  "completed_at": "...",
  "total_elapsed_seconds": 0.0,
  "node_timings": [...],
  "output_sizes_chars": {
    "retrieved_context": 0,
    "structured_requirements": 0,
    "dependency_mapping": 0,
    "generated_scenarios": 0,
    "generated_gherkin": 0,
    "review_feedback": 0
  },
  "files_generated": [...]
}
```

### Debug Files per Run

| File | Written by | Contents |
|------|-----------|----------|
| `00_pipeline_summary.json` | `review_agent` (final pass only) | Timing, output sizes, file list |
| `01_retrieve_context.txt` | `retrieve_context` | Question + retrieved context |
| `02_requirement_understanding.txt` | `requirement_understanding_agent` | Prompt + LLM output |
| `03_dependency_mapping.txt` | `dependency_mapping_agent` | Prompt + LLM output |
| `04_scenario_generation.txt` | `scenario_generation_agent` | Prompt + raw response + cleaned JSON |
| `05_gherkin_generation.txt` | `gherkin_generation_agent` | Input scenarios + prompt + Gherkin JSON |
| `06_review_agent.txt` | `review_agent` (pass 1) | All inputs + review feedback |
| `06_review_agent_r2.txt` | `review_agent` (pass 2) | Same structure, retry pass |
| `07_final_output.txt` | `review_agent` (every pass) | Final Gherkin JSON (overwritten each pass) |

---

## Entry Point

### CLI (`__main__`)

```python
run_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + f"_q{idx}"
state = {
    "question": question,
    "run_id": run_id,
    "retrieved_context": "",
    "structured_requirements": "",
    "dependency_mapping": "",
    "generated_scenarios": "",
    "generated_gherkin": "",
    "review_feedback": "",
    "final_output": "",
    "retry_count": 0,
}
result = agent.invoke(state)
```

### API path

When invoked via the REST API, `run_id` and `retry_count` are not required in the initial state — `retrieve_context` auto-generates `run_id` using `YYYYMMDD_HHMMSS_api` format.

---

## Graph Wiring

```python
graph.add_edge(START, "retrieve_context")
graph.add_edge("retrieve_context", "requirement_understanding")
graph.add_edge("requirement_understanding", "dependency_mapping")
graph.add_edge("dependency_mapping", "scenario_generation")
graph.add_edge("scenario_generation", "gherkin_generation")
graph.add_edge("gherkin_generation", "review_agent")
graph.add_conditional_edges(
    "review_agent",
    _should_retry,
    {"retry": "scenario_generation", "end": END},
)
```

On retry, the loop re-enters at `scenario_generation` — RAG retrieval and requirement/dependency analysis are **not** re-run, preserving their outputs for the improved generation pass.

---

## Prompt File Mapping

| File | Used by | LLM instance |
|------|---------|-------------|
| `RequirementUnderstanding_template.txt` | `requirement_understanding_agent` | `llm` (temp=0.4) |
| `Dependency_prompt.txt` | `dependency_mapping_agent` | `llm` (temp=0.4) |
| `Scenario_prompt.txt` | `scenario_generation_agent` | `llm_scenario` (temp=0.3) |
| `Gherkin_prompt.txt` | `gherkin_generation_agent` | `llm_gherkin` (temp=0.1) |
| `Review_prompt.txt` | `review_agent` | `llm_review` (temp=0.1) |

---

## Data Flow Summary

```
User Question
    │
    ▼  [Graph RAG — retrieve_raw_context()]
Retrieved Context (requirement text from knowledge graph)
    │
    ▼  [llm temp=0.4 + RequirementUnderstanding_template.txt]
Structured Requirements (JSON: rules, validations, states, APIs)
    │
    ▼  [llm temp=0.4 + Dependency_prompt.txt]
Dependency Mapping (JSON: prerequisites, blockers, workflow sequence)
    │
    ▼  [llm_scenario temp=0.3 + Scenario_prompt.txt + retry_supplement?]
Generated Scenarios (JSON: 10 categories of plain-text scenarios)
    │
    ▼  [llm_gherkin temp=0.1 + Gherkin_prompt.txt]
Generated Gherkin (JSON: Given/When/Then BDD scenarios)
    │
    ▼  [llm_review temp=0.1 + Review_prompt.txt]
Review Feedback (JSON: gaps, quality, overall_review_status)
    │
    ├── [Needs Improvement + retry_count < 2] ──► back to Scenario Generation
    │
    └── [Pass OR retry exhausted] ──► final_output = Generated Gherkin
```

---

## Dependencies (External)

```
RequirementGraphEngine   ← local RAG module (Graph-based)
langchain_openai         ← LLM interface (gpt-4o-mini)
langgraph                ← state machine orchestration (conditional edges)
langchain_core           ← HumanMessage wrapper
python-dotenv            ← API key loading from .env
```

OpenAI API key must be present in `.env` as `OPENAI_API_KEY` (standard LangChain convention).
