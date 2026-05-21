from RequirementGraphEngine import RequirementGraphEngine

engine = RequirementGraphEngine(rebuild=False)

import os
import sys
import time
import datetime
from typing import TypedDict
import json
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph

load_dotenv(override=True)

BASE_DIR = os.path.dirname(__file__)
PROMPTS_DIR = os.path.join(BASE_DIR, "prompts")
DEBUG_DIR = os.path.join(BASE_DIR, "debug_outputs")

# Per-run node timing collected across all nodes; keyed by run_id
_run_timings: dict = {}


def load_prompt_file(filename: str) -> str:
    path = os.path.join(PROMPTS_DIR, filename)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def strip_json_fences(content: str) -> str:
    """Remove markdown ```json / ``` wrappers that LLMs sometimes add."""
    content = content.strip()
    if content.startswith("```json"):
        content = content[7:]
    elif content.startswith("```"):
        content = content[3:]
    if content.endswith("```"):
        content = content[:-3]
    return content.strip()


def save_stage_output(stage_name: str, sections: dict, run_id: str, elapsed: float = 0.0) -> str:
    """Write a structured debug file for one pipeline stage.

    Args:
        stage_name: File prefix, e.g. "01_retrieve_context".
        sections:   Ordered dict of {SECTION TITLE: content_string}.
        run_id:     Used as the subdirectory name under debug_outputs/.
        elapsed:    Wall-clock seconds the node took.
    """
    run_dir = os.path.join(DEBUG_DIR, run_id)
    os.makedirs(run_dir, exist_ok=True)
    filepath = os.path.join(run_dir, f"{stage_name}.txt")

    header = [
        "=" * 80,
        f"STAGE  : {stage_name}",
        f"RUN ID : {run_id}",
        f"TIME   : {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"ELAPSED: {elapsed:.2f}s",
        "=" * 80,
    ]
    body = []
    for title, content in sections.items():
        body += [
            "",
            "─" * 40,
            f"[{title}]",
            "─" * 40,
            content if content else "(empty)",
        ]

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(header + body))

    print(f"  [DEBUG] Saved -> {filepath}")
    return filepath


def _record_timing(run_id: str, node: str, elapsed: float, output_chars: int) -> None:
    if run_id not in _run_timings:
        _run_timings[run_id] = []
    _run_timings[run_id].append({
        "node": node,
        "elapsed_seconds": round(elapsed, 2),
        "output_chars": output_chars,
        "completed_at": datetime.datetime.now().isoformat(),
    })


def save_pipeline_summary(state: dict, run_id: str) -> None:
    """Write 00_pipeline_summary.json after the final node completes."""
    run_dir = os.path.join(DEBUG_DIR, run_id)
    os.makedirs(run_dir, exist_ok=True)

    timings = _run_timings.get(run_id, [])
    summary = {
        "run_id": run_id,
        "question": state.get("question", ""),
        "completed_at": datetime.datetime.now().isoformat(),
        "total_elapsed_seconds": round(sum(t["elapsed_seconds"] for t in timings), 2),
        "node_timings": timings,
        "output_sizes_chars": {
            "retrieved_context": len(state.get("retrieved_context", "")),
            "structured_requirements": len(state.get("structured_requirements", "")),
            "dependency_mapping": len(state.get("dependency_mapping", "")),
            "generated_scenarios": len(state.get("generated_scenarios", "")),
            "generated_gherkin": len(state.get("generated_gherkin", "")),
            "review_feedback": len(state.get("review_feedback", "")),
        },
        "files_generated": [
            "00_pipeline_summary.json",
            "01_retrieve_context.txt",
            "02_requirement_understanding.txt",
            "03_dependency_mapping.txt",
            "04_scenario_generation.txt",
            "05_gherkin_generation.txt",
            "06_review_agent.txt",
            "07_final_output.txt",
        ],
    }
    filepath = os.path.join(run_dir, "00_pipeline_summary.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"  [DEBUG] Saved -> {filepath}")


class QuestionState(TypedDict):
    question: str
    run_id: str
    retrieved_context: str
    structured_requirements: str
    dependency_mapping: str
    generated_scenarios: str
    generated_gherkin: str
    review_feedback: str
    final_output: str
    retry_count: int


llm          = ChatOpenAI(model="gpt-4o-mini", temperature=0.4)  # requirement + dependency agents
llm_scenario = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)  # scenario generation
llm_gherkin  = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)  # gherkin (faithfulness > creativity)
llm_review   = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)  # review (consistency > creativity)


# STEP 1 — RAG Retrieval Node
def retrieve_context(state: QuestionState) -> dict:
    print("\n[NODE 1/6] retrieve_context — running...")

    # Auto-generate run_id when called from the API (no run_id in initial state)
    run_id = state.get("run_id") or datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + "_api"

    t0 = time.perf_counter()
    # Use raw retrieval — graph relationships + vector chunks — so downstream agents
    # receive factual knowledge-base content, not an LLM-generated answer that would
    # discard context and potentially pre-interpret the question as a task.
    context_str = engine.retrieve_raw_context(state["question"])
    elapsed = time.perf_counter() - t0

    save_stage_output(
        "01_retrieve_context",
        {
            "USER QUESTION": state["question"],
            "RETRIEVED CONTEXT": context_str,
        },
        run_id,
        elapsed,
    )
    _record_timing(run_id, "retrieve_context", elapsed, len(context_str))
    print(f"  Retrieved {len(context_str)} chars in {elapsed:.2f}s.")
    return {"retrieved_context": context_str, "run_id": run_id}


# STEP 2 — Requirement Understanding Agent
def requirement_understanding_agent(state: QuestionState) -> dict:
    print("\n[NODE 2/6] requirement_understanding — running...")
    t0 = time.perf_counter()

    prompt = (
        load_prompt_file("RequirementUnderstanding_template.txt")
        + "\n\n"
        + f"User Question:\n{state['question']}\n\n"
        + f"Retrieved Context:\n{state['retrieved_context']}"
    )
    result = llm.invoke([HumanMessage(content=prompt)])
    elapsed = time.perf_counter() - t0

    save_stage_output(
        "02_requirement_understanding",
        {
            "USER QUESTION": state["question"],
            "RETRIEVED CONTEXT": state["retrieved_context"],
            "PROMPT SENT TO LLM": prompt,
            "LLM OUTPUT": result.content,
        },
        state["run_id"],
        elapsed,
    )
    _record_timing(state["run_id"], "requirement_understanding", elapsed, len(result.content))
    print(f"  Structured requirements: {len(result.content)} chars in {elapsed:.2f}s.")
    return {"structured_requirements": result.content}


# STEP 3 — Dependency Mapping Agent
def dependency_mapping_agent(state: QuestionState) -> dict:
    print("\n[NODE 3/6] dependency_mapping — running...")
    t0 = time.perf_counter()

    prompt = (
        load_prompt_file("Dependency_prompt.txt")
        + "\n\n"
        + f"User Question:\n{state['question']}\n\n"
        + f"Retrieved Context:\n{state['retrieved_context']}\n\n"
        + f"Structured Requirements:\n{state['structured_requirements']}"
    )
    result = llm.invoke([HumanMessage(content=prompt)])
    elapsed = time.perf_counter() - t0

    save_stage_output(
        "03_dependency_mapping",
        {
            "USER QUESTION": state["question"],
            "RETRIEVED CONTEXT": state["retrieved_context"],
            "STRUCTURED REQUIREMENTS": state["structured_requirements"],
            "PROMPT SENT TO LLM": prompt,
            "LLM OUTPUT": result.content,
        },
        state["run_id"],
        elapsed,
    )
    _record_timing(state["run_id"], "dependency_mapping", elapsed, len(result.content))
    print(f"  Dependency mapping: {len(result.content)} chars in {elapsed:.2f}s.")
    return {"dependency_mapping": result.content}


# STEP 4 — Scenario Generation Agent
def scenario_generation_agent(state: QuestionState) -> dict:
    print("\n[NODE 4/6] scenario_generation — running...")
    t0 = time.perf_counter()
    retry_count = state.get("retry_count", 0)

    # On retry passes, append the gaps identified by the review agent
    retry_supplement = ""
    if retry_count > 0:
        try:
            fb = json.loads(strip_json_fences(state.get("review_feedback", "{}")))
            missing = (
                fb.get("missing_scenarios", [])
                + fb.get("missing_validation_coverage", [])
                + fb.get("missing_edge_cases", [])
                + fb.get("missing_error_handling", [])
                + fb.get("missing_dependency_coverage", [])
                + fb.get("missing_authorization_coverage", [])
            )
            if missing:
                retry_supplement = (
                    "\n\n--------------------------------------------------\n"
                    f"IMPROVEMENT PASS {retry_count} — ADD MISSING SCENARIOS\n"
                    "--------------------------------------------------\n\n"
                    "The previous generation was reviewed and found incomplete.\n"
                    "You MUST add scenarios covering ALL of the following gaps "
                    "in addition to the ones already generated:\n\n"
                    + "\n".join(f"- {m}" for m in missing)
                )
                print(f"  [RETRY] Injecting {len(missing)} missing scenario hints.")
        except Exception:
            pass

    prompt_template = load_prompt_file("Scenario_prompt.txt")
    prompt = f"""
{prompt_template}

--------------------------------------------------
USER QUESTION
--------------------------------------------------

{state.get("question", "")}

--------------------------------------------------
RETRIEVED CONTEXT
--------------------------------------------------

{state.get("retrieved_context", "")}

--------------------------------------------------
STRUCTURED REQUIREMENTS
--------------------------------------------------

{state.get("structured_requirements", "")}

--------------------------------------------------
DEPENDENCY MAPPING
--------------------------------------------------

{state.get("dependency_mapping", "")}

--------------------------------------------------
IMPORTANT INSTRUCTIONS
--------------------------------------------------

Generate comprehensive enterprise QA scenarios using:
- business rules
- validations
- dependencies
- workflow states
- authorization rules

Include:
- positive scenarios
- negative scenarios
- edge cases
- dependency-aware scenarios
- workflow transition scenarios
- validation scenarios

Return ONLY valid JSON.
Do not explain reasoning.
{retry_supplement}
"""
    try:
        result = llm_scenario.invoke([HumanMessage(content=prompt)])
        raw_content = result.content.strip()
        cleaned = strip_json_fences(raw_content)
        elapsed = time.perf_counter() - t0

        # Pretty-print if it is valid JSON
        try:
            pretty = json.dumps(json.loads(cleaned), indent=2)
        except json.JSONDecodeError:
            pretty = cleaned

        save_stage_output(
            "04_scenario_generation",
            {
                "PROMPT SENT TO LLM": prompt,
                "RAW LLM RESPONSE": raw_content,
                "CLEANED JSON OUTPUT": pretty,
            },
            state["run_id"],
            elapsed,
        )
        _record_timing(state["run_id"], "scenario_generation", elapsed, len(pretty))
        print(f"  Generated scenarios: {len(pretty)} chars in {elapsed:.2f}s.")
        return {"generated_scenarios": pretty}

    except Exception as e:
        elapsed = time.perf_counter() - t0
        fallback = {
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
            "important_notes": [f"Scenario generation failed: {str(e)}"],
        }
        fallback_str = json.dumps(fallback, indent=2)
        save_stage_output(
            "04_scenario_generation",
            {
                "PROMPT SENT TO LLM": prompt,
                "ERROR": str(e),
                "FALLBACK OUTPUT": fallback_str,
            },
            state["run_id"],
            elapsed,
        )
        _record_timing(state["run_id"], "scenario_generation", elapsed, 0)
        return {"generated_scenarios": fallback_str}


# STEP 5 — Gherkin Generation Agent
def gherkin_generation_agent(state: QuestionState) -> dict:
    print("\n[NODE 5/6] gherkin_generation — running...")
    t0 = time.perf_counter()

    prompt = (
        load_prompt_file("Gherkin_prompt.txt")
        + "\n\n"
        + f"Generated Scenarios:\n{state['generated_scenarios']}"
    )
    result = llm_gherkin.invoke([HumanMessage(content=prompt)])
    raw_content = result.content
    cleaned = strip_json_fences(raw_content)
    elapsed = time.perf_counter() - t0

    # Pretty-print if it is valid JSON
    try:
        pretty = json.dumps(json.loads(cleaned), indent=2)
    except json.JSONDecodeError:
        pretty = cleaned

    save_stage_output(
        "05_gherkin_generation",
        {
            "GENERATED SCENARIOS (INPUT)": state["generated_scenarios"],
            "PROMPT SENT TO LLM": prompt,
            "RAW LLM RESPONSE": raw_content,
            "CLEANED JSON OUTPUT": pretty,
        },
        state["run_id"],
        elapsed,
    )
    _record_timing(state["run_id"], "gherkin_generation", elapsed, len(pretty))
    print(f"  Gherkin output: {len(pretty)} chars in {elapsed:.2f}s.")
    return {"generated_gherkin": pretty}


# STEP 6 — Review Agent
def review_agent(state: QuestionState) -> dict:
    retry_count = state.get("retry_count", 0) + 1
    print(f"\n[NODE 6/6] review_agent — running... (pass {retry_count})")
    t0 = time.perf_counter()

    prompt = (
        load_prompt_file("Review_prompt.txt")
        + "\n\n"
        + f"Structured Requirements:\n{state['structured_requirements']}\n\n"
        + f"Dependency Mapping:\n{state['dependency_mapping']}\n\n"
        + f"Generated Scenarios:\n{state['generated_scenarios']}\n\n"
        + f"Generated Gherkin:\n{state['generated_gherkin']}"
    )
    result = llm_review.invoke([HumanMessage(content=prompt)])
    elapsed = time.perf_counter() - t0

    stage_suffix = f"_r{retry_count}" if retry_count > 1 else ""
    save_stage_output(
        f"06_review_agent{stage_suffix}",
        {
            "PASS": str(retry_count),
            "STRUCTURED REQUIREMENTS": state["structured_requirements"],
            "DEPENDENCY MAPPING": state["dependency_mapping"],
            "GENERATED SCENARIOS": state["generated_scenarios"],
            "GENERATED GHERKIN (INPUT)": state["generated_gherkin"],
            "PROMPT SENT TO LLM": prompt,
            "REVIEW FEEDBACK": result.content,
        },
        state["run_id"],
        elapsed,
    )
    # 07_final_output.txt — always updated to latest gherkin
    run_dir = os.path.join(DEBUG_DIR, state["run_id"])
    os.makedirs(run_dir, exist_ok=True)
    final_path = os.path.join(run_dir, "07_final_output.txt")
    with open(final_path, "w", encoding="utf-8") as f:
        f.write(state["generated_gherkin"])
    print(f"  [DEBUG] Saved -> {final_path}")

    _record_timing(state["run_id"], f"review_agent_pass{retry_count}", elapsed, len(result.content))
    print(f"  Review feedback: {len(result.content)} chars in {elapsed:.2f}s.")

    # Determine if a retry is warranted
    will_retry = False
    if retry_count < 2:
        try:
            fb = json.loads(strip_json_fences(result.content))
            if fb.get("overall_review_status") == "Needs Improvement":
                will_retry = True
                print(f"  [RETRY] Review status = Needs Improvement — scheduling pass {retry_count + 1}.")
        except Exception:
            pass

    final_state = {**state, "review_feedback": result.content, "final_output": state["generated_gherkin"], "retry_count": retry_count}

    # Only persist the pipeline summary on the final pass
    if not will_retry:
        save_pipeline_summary(final_state, state["run_id"])

    return {
        "review_feedback": result.content,
        "final_output": state["generated_gherkin"],
        "retry_count": retry_count,
    }


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


# BUILD GRAPH
def build_question_agent_graph():
    graph = StateGraph(QuestionState)

    graph.add_node("retrieve_context", retrieve_context)
    graph.add_node("requirement_understanding", requirement_understanding_agent)
    graph.add_node("dependency_mapping", dependency_mapping_agent)
    graph.add_node("scenario_generation", scenario_generation_agent)
    graph.add_node("gherkin_generation", gherkin_generation_agent)
    graph.add_node("review_agent", review_agent)

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

    return graph.compile()


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")

    agent = build_question_agent_graph()

    example_questions = [
        "Generate test cases for a login function that validates username and password."
    ]

    for idx, question in enumerate(example_questions, start=1):
        run_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + f"_q{idx}"
        print(f"\n{'='*60}")
        print(f"Question {idx}: {question}")
        print(f"Run ID   : {run_id}")
        print(f"{'='*60}")

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

        run_dir = os.path.join(DEBUG_DIR, run_id)
        timings = _run_timings.get(run_id, [])
        total = sum(t["elapsed_seconds"] for t in timings)

        print(f"\n{'='*60}")
        print(f"Pipeline complete  — total {total:.1f}s")
        print(f"Debug directory    : {run_dir}")
        print(f"  00_pipeline_summary.json")
        for t in timings:
            print(f"  {t['node']:35s}  {t['elapsed_seconds']:5.1f}s  {t['output_chars']} chars")
        print(f"{'='*60}")
        print(f"\n--- Final Gherkin Output ---\n{result.get('final_output')}")
        print(f"\n--- Review Feedback ---\n{result.get('review_feedback')}")
