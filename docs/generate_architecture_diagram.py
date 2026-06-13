"""
Generate the AgenticQAEngine architecture flowchart as a high-resolution PNG.
Renders using matplotlib with custom patch/arrow drawing — no graphviz needed.
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import matplotlib.patheffects as pe

# ── Canvas ──────────────────────────────────────────────────────────────────
FIG_W, FIG_H = 22, 28
fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
ax.set_xlim(0, FIG_W)
ax.set_ylim(0, FIG_H)
ax.axis("off")
fig.patch.set_facecolor("#0f1117")
ax.set_facecolor("#0f1117")

# ── Palette ──────────────────────────────────────────────────────────────────
C = {
    "bg":         "#0f1117",
    "layer_bg":   "#1a1d2e",
    "frontend":   "#1e3a5f",
    "frontend_b": "#2196f3",
    "backend":    "#1a2e1a",
    "backend_b":  "#4caf50",
    "pipeline":   "#2d1b4e",
    "pipeline_b": "#9c27b0",
    "node":       "#3d2060",
    "node_b":     "#ce93d8",
    "rag":        "#2e1a0e",
    "rag_b":      "#ff9800",
    "playwright": "#1a2e2e",
    "playwright_b":"#00bcd4",
    "mcp":        "#1e2d1e",
    "mcp_b":      "#66bb6a",
    "data":       "#2a1a1a",
    "data_b":     "#ef5350",
    "arrow":      "#546e7a",
    "arrow_hl":   "#90caf9",
    "text_w":     "#ffffff",
    "text_m":     "#b0bec5",
    "text_d":     "#78909c",
    "hitl":       "#2e2800",
    "hitl_b":     "#ffc107",
}

# ── Helpers ──────────────────────────────────────────────────────────────────
def box(x, y, w, h, fc, ec, radius=0.3, lw=1.5, alpha=1.0, zorder=2):
    p = FancyBboxPatch((x, y), w, h,
                       boxstyle=f"round,pad=0,rounding_size={radius}",
                       facecolor=fc, edgecolor=ec,
                       linewidth=lw, alpha=alpha, zorder=zorder)
    ax.add_patch(p)
    return p

def label(x, y, text, size=9, color="#ffffff", weight="normal",
          ha="center", va="center", zorder=5):
    ax.text(x, y, text, fontsize=size, color=color,
            fontweight=weight, ha=ha, va=va, zorder=zorder,
            fontfamily="monospace")

def sublabel(x, y, text, size=7.5, color="#b0bec5"):
    ax.text(x, y, text, fontsize=size, color=color,
            ha="center", va="center", zorder=5, fontfamily="monospace")

def section_header(x, y, w, h, fc, ec, title, lw=2):
    box(x, y, w, h, fc, ec, radius=0.4, lw=lw, zorder=1)
    label(x + w/2, y + h - 0.35, title, size=9.5, color=ec, weight="bold")

def arrow(x1, y1, x2, y2, color="#546e7a", lw=1.5,
          style="->", zorder=3):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle=style,
                                color=color, lw=lw,
                                connectionstyle="arc3,rad=0.0"),
                zorder=zorder)

def curved_arrow(x1, y1, x2, y2, color="#546e7a", lw=1.5, rad=0.2):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="->",
                                color=color, lw=lw,
                                connectionstyle=f"arc3,rad={rad}"),
                zorder=3)

def node_box(x, y, w, h, num, title, subtitle="", fc=None, ec=None):
    fc = fc or C["node"]
    ec = ec or C["node_b"]
    box(x, y, w, h, fc, ec, radius=0.25, lw=1.5)
    # number badge
    circle = plt.Circle((x + 0.38, y + h/2), 0.22,
                         color=ec, zorder=6)
    ax.add_patch(circle)
    label(x + 0.38, y + h/2, str(num), size=8, color="#000", weight="bold", zorder=7)
    label(x + w/2 + 0.1, y + h/2 + (0.1 if subtitle else 0),
          title, size=8.5, color=C["text_w"], weight="bold")
    if subtitle:
        sublabel(x + w/2 + 0.1, y + h/2 - 0.22, subtitle, size=7)

# ════════════════════════════════════════════════════════════════════════════
#  TITLE
# ════════════════════════════════════════════════════════════════════════════
label(FIG_W/2, 27.4, "AgenticQAEngine — Complete Architecture",
      size=17, color="#ffffff", weight="bold")
label(FIG_W/2, 26.95, "LangGraph Multi-Agent Pipeline  ·  Graph RAG  ·  Playwright Automation  ·  MCP Servers",
      size=9, color=C["text_d"])

# ════════════════════════════════════════════════════════════════════════════
#  LAYER 1 — FRONTEND  (y: 24.5 → 26.4)
# ════════════════════════════════════════════════════════════════════════════
section_header(0.5, 24.4, 21, 2.2, C["frontend"], C["frontend_b"],
               "[1] FRONTEND  --  Next.js 14 · TypeScript · Tailwind CSS", lw=2)

# Three UI panels
for i, (title, sub) in enumerate([
    ("Chat Interface", "Question input · Suggested prompts"),
    ("Scenario Viewer", "Review Gate · Approve / Re-generate"),
    ("Playwright Console", "Script preview · Run · Triage · Fix"),
]):
    bx = 0.9 + i * 7.0
    box(bx, 24.65, 6.3, 1.7, C["frontend"], C["frontend_b"], radius=0.25, lw=1.2)
    label(bx + 3.15, 25.75, title, size=9, color=C["frontend_b"], weight="bold")
    sublabel(bx + 3.15, 25.35, sub, size=7.5)

# Connector between UI panels
arrow(7.2, 25.5, 7.9, 25.5, color=C["frontend_b"], lw=1.2)
arrow(14.2, 25.5, 14.9, 25.5, color=C["frontend_b"], lw=1.2)

# ════════════════════════════════════════════════════════════════════════════
#  Arrow: Frontend → Backend
# ════════════════════════════════════════════════════════════════════════════
arrow(11, 24.4, 11, 23.55, color=C["arrow_hl"], lw=2)
label(11.5, 23.97, "REST + SSE  /api/*", size=7.5, color=C["arrow_hl"])

# ════════════════════════════════════════════════════════════════════════════
#  LAYER 2 — BACKEND API  (y: 22.0 → 23.55)
# ════════════════════════════════════════════════════════════════════════════
section_header(0.5, 22.0, 21, 1.55, C["backend"], C["backend_b"],
               "[2] BACKEND API  --  FastAPI · Python · Uvicorn", lw=2)

for i, (title, sub) in enumerate([
    ("POST /api/generate", "Start pipeline · return thread_id"),
    ("POST /api/resume-with-feedback", "HITL resume from Node 4"),
    ("GET  /api/test-suites", "List saved suites"),
    ("POST /api/playwright-*", "Generate · Run · Triage · Fix"),
]):
    bx = 0.9 + i * 5.1
    box(bx, 22.2, 4.7, 1.1, C["backend"], C["backend_b"], radius=0.2, lw=1.0)
    label(bx + 2.35, 22.95, title, size=8, color=C["backend_b"], weight="bold")
    sublabel(bx + 2.35, 22.57, sub, size=7)

# ════════════════════════════════════════════════════════════════════════════
#  Arrows: Backend → Pipeline  and  Backend → Playwright
# ════════════════════════════════════════════════════════════════════════════
arrow(6.5, 22.0, 6.5, 21.15, color=C["pipeline_b"], lw=2)
label(7.5, 21.58, "agent.invoke()", size=7.5, color=C["pipeline_b"])

arrow(16.5, 22.0, 16.5, 17.75, color=C["playwright_b"], lw=2)
label(17.6, 19.8, "playwright_agent", size=7.5, color=C["playwright_b"])

# ════════════════════════════════════════════════════════════════════════════
#  LAYER 3 — LANGGRAPH PIPELINE  (y: 14.7 → 21.15)
# ════════════════════════════════════════════════════════════════════════════
section_header(0.5, 14.7, 13.5, 6.45, C["pipeline"], C["pipeline_b"],
               "[3] LangGraph Pipeline  --  GPT-4o-mini · MemorySaver Checkpointer", lw=2)

# Nodes
nodes = [
    (1, "retrieve_context",           "Graph RAG + Neo4j hybrid search"),
    (2, "requirement_understanding",  "Actors · pre/post-conditions · rules"),
    (3, "dependency_mapping",         "Cross-module dependency analysis"),
    (4, "scenario_generation",        "Positive · Negative · Edge · Auth"),
    (5, "gherkin_generation",         "Given / When / Then  BDD JSON"),
    (6, "review_agent",               "Quality gate · completeness check"),
]
NODE_X, NODE_W, NODE_H = 0.85, 12.8, 0.82
node_y_positions = []
for i, (num, title, sub) in enumerate(nodes):
    ny = 20.05 - i * 0.98
    node_y_positions.append(ny)
    node_box(NODE_X, ny, NODE_W, NODE_H, num, title, sub)
    if i < len(nodes) - 1:
        arrow(NODE_X + NODE_W/2, ny, NODE_X + NODE_W/2, ny - 0.15,
              color=C["pipeline_b"], lw=1.5)

# HITL interrupt badge
hitl_y = node_y_positions[5] - 0.05
box(1.2, hitl_y - 0.55, 6.5, 0.55, C["hitl"], C["hitl_b"],
    radius=0.18, lw=1.3, zorder=4)
label(4.45, hitl_y - 0.28,
      "|| interrupt_after=[\"review_agent\"]  --  Human-in-the-Loop gate",
      size=7.5, color=C["hitl_b"], weight="bold", zorder=6)

# Retry loop arrow
retry_y_top = node_y_positions[3] + NODE_H/2
retry_y_bot = node_y_positions[5] + NODE_H/2
curved_arrow(NODE_X + NODE_W, retry_y_bot, NODE_X + NODE_W, retry_y_top,
             color="#f06292", lw=1.5, rad=-0.4)
label(14.45, (retry_y_top + retry_y_bot)/2,
      "retry if\n'Needs\nImprovement'", size=7, color="#f06292",
      ha="center", va="center")

# MemorySaver badge
box(7.5, 15.0, 5.8, 0.55, "#1a0d2e", "#7b1fa2", radius=0.18, lw=1.2, zorder=4)
label(10.4, 15.27, "MemorySaver  ·  thread_id per request  ·  resume from Node 4",
      size=7.5, color="#ce93d8", zorder=6)

# ════════════════════════════════════════════════════════════════════════════
#  LAYER 4 — GRAPH RAG / KNOWLEDGE  (y: 10.8 → 14.7)
# ════════════════════════════════════════════════════════════════════════════
section_header(0.5, 10.8, 13.5, 3.9, C["rag"], C["rag_b"],
               "[4] Knowledge Layer  --  RequirementGraphEngine · Graph RAG", lw=2)

# Neo4j box
box(0.85, 11.05, 5.9, 3.4, "#1a1200", C["rag_b"], radius=0.3, lw=1.4)
label(3.8, 13.95, "Neo4j Knowledge Graph", size=9, color=C["rag_b"], weight="bold")
for i, t in enumerate([
    "Nodes: UseCase · Requirement · Actor",
    "Edges: DEPENDS_ON · TRIGGERS · VALIDATES",
    "Hybrid search: vector + fulltext",
    "EMBEDDING: all-MiniLM-L6-v2 (384-dim)",
]):
    sublabel(3.8, 13.5 - i*0.42, t, size=7.5)

# Confluence box
box(7.25, 11.05, 6.4, 3.4, "#001122", "#1976d2", radius=0.3, lw=1.4)
label(10.45, 13.95, "Confluence", size=9, color="#1976d2", weight="bold")
for i, t in enumerate([
    "Source of truth for BA requirements",
    "Loader: ConfluenceLoader (6 pages)",
    "Chunked: TokenTextSplitter(512, 24)",
    "Ingested via LLMGraphTransformer",
]):
    sublabel(10.45, 13.5 - i*0.42, t, size=7.5)

# Arrow: Node 1 → Neo4j
arrow(7.25, 20.05 + NODE_H/2, 7.25, 14.7,
      color=C["rag_b"], lw=1.5)
label(8.3, 17.7, "retrieve_raw_context()", size=7.5, color=C["rag_b"])

# Arrow: Confluence → Neo4j
arrow(7.25, 12.75, 6.75, 12.75, color="#1976d2", lw=1.2)
label(7.0, 13.05, "rebuild", size=7, color="#1976d2")

# ════════════════════════════════════════════════════════════════════════════
#  LAYER 5 — PLAYWRIGHT AGENT  (y: 10.8 → 17.75)
# ════════════════════════════════════════════════════════════════════════════
section_header(14.5, 10.8, 7.0, 6.95, C["playwright"], C["playwright_b"],
               "[5] Playwright Agent  --  GPT-4o", lw=2)

pw_steps = [
    ("Gherkin Input",         "Approved BDD scenarios"),
    ("Script Codegen",        "GPT-4o → Feature · POM · Test"),
    ("pytest-playwright",     "Chromium headless execution"),
    ("Failure Artifacts",     ".png screenshot + .html DOM"),
    ("Triage Agent",          "Root cause · fix category"),
    ("Apply Fix",             "Patch file · re-run single test"),
]
for i, (title, sub) in enumerate(pw_steps):
    py = 17.25 - i * 1.02
    box(14.8, py, 6.4, 0.82, C["playwright"], C["playwright_b"],
        radius=0.2, lw=1.0)
    label(18.0, py + 0.55, title, size=8.5, color=C["playwright_b"], weight="bold")
    sublabel(18.0, py + 0.22, sub, size=7)
    if i < len(pw_steps) - 1:
        arrow(18.0, py, 18.0, py - 0.18, color=C["playwright_b"], lw=1.3)

# ════════════════════════════════════════════════════════════════════════════
#  LAYER 6 — MCP SERVERS  (y: 7.5 → 10.8)
# ════════════════════════════════════════════════════════════════════════════
section_header(0.5, 7.5, 21, 3.3, C["mcp"], C["mcp_b"],
               "[6] MCP Servers  --  FastMCP · Claude Code Integration", lw=2)

# Neo4j MCP
box(0.85, 7.75, 9.5, 2.8, "#0d1a0d", C["mcp_b"], radius=0.3, lw=1.4)
label(6.1, 10.05, "neo4j_server.py", size=9, color=C["mcp_b"], weight="bold")
tools_neo4j = ["run_cypher", "get_schema", "get_use_case_graph",
               "list_all_use_cases", "get_error_codes", "debug_rag_retrieval"]
for i, t in enumerate(tools_neo4j):
    col = 1.3 if i < 3 else 5.7
    row = i % 3
    sublabel(col + 2.3, 9.6 - row * 0.4, f"• {t}", size=7.5)

# Confluence MCP
box(10.75, 7.75, 10.25, 2.8, "#0d1220", "#1976d2", radius=0.3, lw=1.4)
label(15.875, 10.05, "confluence_server.py", size=9, color="#1976d2", weight="bold")
tools_conf = ["get_page", "list_requirement_pages",
              "search_pages", "get_all_requirements", "create_test_plan"]
for i, t in enumerate(tools_conf):
    sublabel(15.875, 9.6 - i * 0.4, f"• {t}", size=7.5)

# ════════════════════════════════════════════════════════════════════════════
#  LAYER 7 — DATA STORES  (y: 4.8 → 7.5)
# ════════════════════════════════════════════════════════════════════════════
section_header(0.5, 4.8, 21, 2.7, C["data"], C["data_b"],
               "[7] Data Stores & Outputs", lw=2)

stores = [
    ("Neo4j\nGraph DB",         "bolt://localhost:7687\nRequirements KG"),
    ("Confluence\nWiki",        "atlassian.net\nBA requirements"),
    ("tests/\nfeatures/",       "Gherkin .feature files\n(version controlled)"),
    ("tests/\ntest_suites/",    "Playwright POM + tests\n(auto-generated)"),
    ("debug_outputs/\n{run_id}","Stage outputs per run\npipeline_summary.json"),
    ("suites.json\nmanifest",   "Suite registry\nlast run results"),
]
for i, (title, sub) in enumerate(stores):
    bx = 0.85 + i * 3.45
    box(bx, 5.05, 3.1, 2.2, C["data"], C["data_b"], radius=0.25, lw=1.2)
    label(bx + 1.55, 6.55, title, size=8, color=C["data_b"], weight="bold")
    sublabel(bx + 1.55, 5.95, sub, size=7)

# ════════════════════════════════════════════════════════════════════════════
#  LEGEND  (y: 2.8 → 4.6)
# ════════════════════════════════════════════════════════════════════════════
box(0.5, 2.8, 21, 1.8, "#111420", "#37474f", radius=0.3, lw=1)
label(11, 4.22, "LEGEND", size=8.5, color=C["text_m"], weight="bold")
legend_items = [
    (C["frontend_b"],   "Frontend (Next.js)"),
    (C["backend_b"],    "Backend (FastAPI)"),
    (C["pipeline_b"],   "LangGraph Pipeline"),
    (C["rag_b"],        "Knowledge Layer (RAG)"),
    (C["playwright_b"], "Playwright Agent"),
    (C["mcp_b"],        "MCP Servers"),
    (C["hitl_b"],       "HITL Interrupt"),
    ("#f06292",         "Auto-Retry Loop"),
]
for i, (color, label_text) in enumerate(legend_items):
    lx = 1.2 + i * 2.58
    rect = FancyBboxPatch((lx, 3.0), 0.35, 0.35,
                          boxstyle="round,pad=0,rounding_size=0.08",
                          facecolor=color, edgecolor=color, zorder=5)
    ax.add_patch(rect)
    ax.text(lx + 0.5, 3.17, label_text, fontsize=7.5,
            color=C["text_m"], va="center", fontfamily="monospace", zorder=5)

# ════════════════════════════════════════════════════════════════════════════
#  FOOTER
# ════════════════════════════════════════════════════════════════════════════
label(FIG_W/2, 2.35, "Tech Stack:  Python · FastAPI · LangGraph 1.2 · LangChain · Neo4j · Confluence · Playwright · Next.js 14 · TypeScript · Tailwind",
      size=8, color=C["text_d"])
label(FIG_W/2, 1.95, "Models:  GPT-4o (Playwright codegen)  ·  GPT-4o-mini (pipeline agents)  ·  all-MiniLM-L6-v2 (embeddings)",
      size=8, color=C["text_d"])
label(FIG_W/2, 1.55, "Agentic QA Engine  —  Trade Processing Platform  ·  2026",
      size=8, color="#546e7a")

# ════════════════════════════════════════════════════════════════════════════
#  SAVE
# ════════════════════════════════════════════════════════════════════════════
OUT = r"D:\Architect\TestCasesGenerator\docs\architecture_diagram.png"
plt.tight_layout(pad=0)
plt.savefig(OUT, dpi=180, bbox_inches="tight",
            facecolor=fig.get_facecolor())
plt.close()
print("Saved ->", OUT)
