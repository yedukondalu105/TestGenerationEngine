---
marp: true
theme: default
paginate: true
style: |
  section {
    font-family: 'Segoe UI', Arial, sans-serif;
    background: #ffffff;
    color: #1a1a2e;
    padding: 48px 64px;
  }
  section.title {
    background: linear-gradient(135deg, #0f3460 0%, #16213e 60%, #0d7377 100%);
    color: #ffffff;
    text-align: center;
    justify-content: center;
  }
  section.title h1 { font-size: 2.4rem; margin-bottom: 0.3em; }
  section.title p  { font-size: 1.1rem; opacity: 0.85; }
  section.section-header {
    background: #0f3460;
    color: #ffffff;
    justify-content: center;
    text-align: center;
  }
  section.section-header h2 { font-size: 2.2rem; }
  h1 { color: #0f3460; font-size: 1.8rem; border-bottom: 3px solid #0d7377; padding-bottom: 8px; }
  h2 { color: #0f3460; font-size: 1.5rem; }
  h3 { color: #0d7377; font-size: 1.1rem; }
  code { background: #f0f4f8; border-radius: 4px; padding: 2px 6px; color: #0d7377; font-size: 0.85em; }
  pre  { background: #1a1a2e; color: #e2e8f0; border-radius: 8px; padding: 16px; font-size: 0.78rem; }
  table { width: 100%; border-collapse: collapse; font-size: 0.88rem; }
  th { background: #0f3460; color: #fff; padding: 8px 12px; }
  td { padding: 7px 12px; border-bottom: 1px solid #e2e8f0; }
  tr:nth-child(even) td { background: #f7fafc; }
  .pill { display: inline-block; background: #0d7377; color: #fff; border-radius: 12px; padding: 2px 10px; font-size: 0.78rem; margin: 2px; }
  footer { font-size: 0.7rem; color: #888; }
---

<!-- _class: title -->

# Agentic QA Engine
## AI-Powered Test Case Generation Platform

**Senior Leadership Demo**
Trade Processing Platform · June 2026

---

# The Problem We Solved

Manual QA test generation is a **bottleneck** at every release cycle.

| Pain Point | Impact |
|---|---|
| QA engineers write test cases by hand | 3–5 days per feature module |
| Requirements scattered across Confluence | Context lost between teams |
| No traceability from requirement → test | Audit failures, missed edge cases |
| Playwright scripts written from scratch | Inconsistent coverage |

> **Goal:** Turn a natural-language question into executable BDD test cases — in seconds, not days.

---

# Solution at a Glance

```
Engineer types a question
        ↓
  AI Pipeline (LangGraph)
        ↓
  Gherkin Test Cases  ←→  Human Review
        ↓
  Playwright Scripts (auto-generated)
        ↓
  Browser Test Execution + Failure Triage
```

- **No prompt engineering expertise required** from QA engineers
- **Full traceability** — every scenario linked to a source requirement
- **One-click** from question to running browser tests

---

<!-- _class: section-header -->

## Architecture Deep Dive

---

# Full-Stack Architecture

```
┌─────────────────────────────────────────────────────┐
│                 Next.js Frontend (React + Tailwind)  │
│   Chat UI  │  Scenario Viewer  │  Playwright Console │
└────────────────────────┬────────────────────────────┘
                         │  REST + SSE Streaming
┌────────────────────────▼────────────────────────────┐
│              FastAPI Backend (Python)                │
│  /generate  │  /download  │  /playwright/*           │
└──────┬──────────────────────────┬───────────────────┘
       │                          │
┌──────▼──────────┐    ┌──────────▼──────────────────┐
│ TestGeneration  │    │      Playwright Agent        │
│ Engine          │    │  (GPT-4o codegen + runner)   │
│ (LangGraph)     │    └─────────────────────────────┘
└──────┬──────────┘
       │
┌──────▼──────────────────────────────────────────────┐
│          RequirementGraphEngine (Graph RAG)          │
│              Neo4j Knowledge Graph                   │
└─────────────────────────────────────────────────────┘
```

---

# LangGraph Pipeline — 5 Nodes

```
START
  │
  ▼
┌──────────────────────┐
│  1. retrieve_context │  Graph RAG → Neo4j use-case nodes
└──────────┬───────────┘  + Confluence requirement pages
           │
           ▼
┌──────────────────────┐
│  2. requirement_     │  Structured extraction of actors,
│     understanding    │  pre/post-conditions, business rules
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  3. scenario_        │  Happy path + edge cases + error paths
│     generation       │  mapped to each requirement
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  4. gherkin_         │  Given / When / Then BDD syntax
│     generation       │  structured JSON + human-readable
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  5. review_agent     │  Quality gate: completeness, clarity,
│                      │  traceability check
└──────────┬───────────┘
           │
          END
```

---

# Knowledge Layer — Graph RAG

**RequirementGraphEngine** wraps Neo4j with semantic retrieval.

```python
# What happens at Node 1
context = engine.retrieve_relevant_context(question)
# → vector similarity over use-case embeddings
# → graph traversal: use_case → requirements → actors → error_codes
```

### Why a Knowledge Graph?

- Requirements have **relationships** — a graph captures what flat docs cannot
- `get_use_case_graph` returns the full subgraph for any module
- `debug_rag_retrieval` exposes what the model actually sees

### Confluence Integration

- `list_requirement_pages` → enumerate all BA requirement docs
- `get_all_requirements` → bulk-load into the graph on rebuild
- Single source of truth: **Confluence stays the system of record**

---

# MCP Servers — Claude Code Integration

Two **FastMCP** servers expose the knowledge base as tools directly in Claude Code.

| Server | Tools | Purpose |
|---|---|---|
| `neo4j_server.py` | `run_cypher`, `get_schema`, `get_use_case_graph`, `list_all_use_cases`, `get_error_codes`, `debug_rag_retrieval` | Query the knowledge graph live |
| `confluence_server.py` | `get_page`, `list_requirement_pages`, `search_pages`, `get_all_requirements`, `create_test_plan` | Read & write Confluence docs |

> Engineers can ask Claude Code: *"Show me all error codes for the Trade Settlement use case"* — answered directly from Neo4j, no manual query.

---

<!-- _class: section-header -->

## Playwright Test Execution

---

# Playwright Agent — End-to-End Automation

Once Gherkin scenarios are approved, the **Playwright Agent** takes over.

```
Approved Gherkin Suite
        │
        ▼
  GPT-4o Codegen
  ├── Page Object files  (tests/pages/)
  └── Test scripts       (tests/test_suites/)
        │
        ▼
  pytest-playwright runner
  ├── Chromium (headless)
  └── Failure artifacts: .png screenshots + .html DOM snapshots
        │
        ▼
  AI Failure Triage Agent
  ├── Classifies each failure (selector / timing / logic / env)
  └── Suggests targeted fix → one-click Apply
```

---

# Playwright Agent — Key Capabilities

| Capability | Description |
|---|---|
| `generate_suite_preview` | Dry-run: generate scripts without saving |
| `generate_and_run_suite` | Full cycle: generate → save → execute |
| `triage_failures_agent` | AI analysis of failed tests with fix suggestions |
| `apply_test_fix` | Patches the script file with the suggested fix |
| `run_single_test` | Re-run one test after a fix to confirm it passes |
| `regenerate_scripts` | Re-generate scripts from updated Gherkin |

**Models used:**
- `gpt-4o` — Playwright script generation (high accuracy code)
- `gpt-4o-mini` — Failure triage & review (fast, cost-efficient)

---

# Frontend — QA Engineer Workflow

```
┌──────────────────────────────────────────────────────┐
│  1. Chat Input                                       │
│     "Generate test cases for User Role Management"  │
│                          ↓ streaming response        │
│  2. Scenario Viewer                                  │
│     Tabbed view: Requirements | Scenarios | Gherkin  │
│                          ↓ approve                   │
│  3. Playwright Console                               │
│     Generate Scripts → Run Suite → View Results      │
│                          ↓                           │
│  4. Triage Panel                                     │
│     Failure list → AI analysis → Apply Fix button    │
└──────────────────────────────────────────────────────┘
```

Built with **Next.js 14 · TypeScript · Tailwind CSS**
Server-Sent Events (SSE) for real-time pipeline streaming

---

# Technology Stack

| Layer | Technology | Role |
|---|---|---|
| **Frontend** | Next.js 14, TypeScript, Tailwind | QA engineer UI |
| **Backend** | FastAPI, Python | REST API + SSE streaming |
| **AI Pipeline** | LangGraph, LangChain | Multi-agent orchestration |
| **LLM** | GPT-4o, GPT-4o-mini | Generation + review |
| **Knowledge Graph** | Neo4j + Graph RAG | Requirement retrieval |
| **Docs** | Confluence (MCP) | Source of truth |
| **Test Execution** | Playwright + pytest | Browser automation |
| **MCP Servers** | FastMCP | Claude Code integration |

---

<!-- _class: section-header -->

## Results & Impact

---

# What It Delivers

### Time Savings
- **Manual:** 3–5 days to write test cases for one module
- **With Agentic QA Engine:** Under 2 minutes end-to-end

### Coverage
- Happy path + edge cases + error paths — generated automatically
- Every scenario traceable back to a Confluence requirement page

### Quality Gate
- `review_agent` enforces completeness, clarity, and BDD correctness before any script is generated
- AI triage catches root cause of test failures — not just "test failed"

### Reusability
- Page Object Model pattern — pages shared across test suites
- Gherkin feature files are human-readable and version-controlled

---

# Live Demo Flow

1. **Enter a question** in the chat UI
   > *"Create test cases for User and Role Management in the Admin module"*

2. **Watch the pipeline stream** — 5 nodes execute in sequence

3. **Review Gherkin output** — structured scenarios with Given/When/Then

4. **Approve & generate Playwright scripts** — one click

5. **Run the suite** — browser tests execute against the application

6. **View triage results** — failures analyzed with fix suggestions

7. **Apply fix & rerun** — confirm the test passes

---

# Roadmap

| Priority | Item | Status |
|---|---|---|
| **Done** | LangGraph 5-node pipeline | ✅ |
| **Done** | FastAPI + Next.js full-stack | ✅ |
| **Done** | Playwright script gen + execution | ✅ |
| **Done** | AI failure triage with fix | ✅ |
| **Done** | Neo4j + Confluence MCP servers | ✅ |
| **Next** | Dependency agent (wired into pipeline) | 🔄 |
| **Next** | Playwright MCP server for Claude Code | 🔄 |
| **Next** | GitHub MCP — auto-PR for approved suites | 🔄 |
| **Future** | Multi-browser parallel execution | 📋 |
| **Future** | Historical test trend dashboard | 📋 |

---

<!-- _class: title -->

# Thank You

**Questions?**

Agentic QA Engine · Trade Processing Platform
uppalayk105@gmail.com
