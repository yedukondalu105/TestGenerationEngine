# MCP Servers

Model Context Protocol servers that expose project knowledge base tools to Claude Code.

## Architecture

```
mcp_servers/
├── neo4j_server.py       ← Graph database tools (6 tools)
├── confluence_server.py  ← Requirement page tools (5 tools)
└── README.md
```

Both servers are registered in `.mcp.json` at the project root and load credentials
from `.env` automatically.

---

## Neo4j Server — `neo4j`

Exposes the knowledge graph built by `RequirementGraphEngine.py`.

| Tool | Description |
|------|-------------|
| `run_cypher` | Run an arbitrary Cypher query. Takes `query` string and optional `params` JSON string. |
| `get_schema` | Return all node labels, relationship types, and property keys. |
| `get_use_case_graph` | Retrieve the full relationship subgraph for a named use case (e.g. "Trade Amendment"). |
| `list_all_use_cases` | List every entity ID in the graph — useful for discovery. |
| `get_error_codes` | Find error code entities and their descriptions. |
| `debug_rag_retrieval` | Reproduce what `RequirementGraphEngine._retriever()` would return for a question, without calling the LLM. |

---

## Confluence Server — `confluence`

Exposes the Confluence requirement pages configured in `.env`.

| Tool | Description |
|------|-------------|
| `get_page` | Fetch a page by ID and return its plain-text content. |
| `list_requirement_pages` | List all pages configured via `CONFLUENCE_PAGE_ID_*` env vars. |
| `search_pages` | CQL keyword search across the configured space. |
| `get_all_requirements` | Fetch and combine content from all configured requirement pages in one call. |
| `create_test_plan` | Create a new Confluence page with test plan content. |

---

## Setup

### 1. Install dependencies

```bash
pip install fastmcp
# or via requirements:
pip install -r requirements.txt
```

### 2. Configure `.env`

All credentials are read from the project root `.env`. Required keys:

```
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=...
NEO4J_DATABASE=neo4j

CONFLUENCE_URL=https://your-domain.atlassian.net/wiki
CONFLUENCE_USERNAME=your@email.com
CONFLUENCE_API_TOKEN=...
CONFLUENCE_SPACE_KEY=YOURSPACE
CONFLUENCE_PAGE_ID_1=...
```

See `.env.example` for the full list.

### 3. Build the knowledge graph

The Neo4j tools require the graph to be populated first:

```python
from RequirementGraphEngine import RequirementGraphEngine
engine = RequirementGraphEngine(rebuild=True)
```

### 4. Activate in Claude Code

The `.mcp.json` at the project root is picked up automatically when you open
this directory in Claude Code. Restart the session after first setup.

To verify the servers are loaded, run in Claude Code:

```
/mcp
```

---

## Adding More Servers

Planned additions:
- **Playwright** — browser automation for end-to-end test execution
- **GitHub** — PR and issue management for test plan tracking

Add each new server file here and register it in `.mcp.json`.
