import sys
import os
import io
import json
import asyncio

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# Allow importing from both the backend/ dir and the project root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from TestGenerationEngine import build_question_agent_graph
from excel_generator import generate_excel
from zip_generator import generate_zip
from playwright_agent import playwright_codegen_agent, playwright_executor_agent, results_review_agent

app = FastAPI(title="QA Test Cases Generator API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Build once at startup — avoids reloading embedding weights on every request
agent = build_question_agent_graph()


class GenerateRequest(BaseModel):
    question: str


class DownloadRequest(BaseModel):
    question: str
    final_output: str
    review_feedback: str
    generated_scenarios: str


class DownloadZipRequest(BaseModel):
    question: str
    final_output: str
    review_feedback: str
    generated_scenarios: str
    retrieved_context: str = ""
    structured_requirements: str = ""
    dependency_mapping: str = ""


class PlaywrightRunRequest(BaseModel):
    final_output: str


@app.post("/api/generate")
async def generate(request: GenerateRequest):
    initial_state = {
        "question": request.question,
        "retrieved_context": "",
        "structured_requirements": "",
        "dependency_mapping": "",
        "generated_scenarios": "",
        "generated_gherkin": "",
        "review_feedback": "",
        "final_output": "",
        "retry_count": 0,
    }

    try:
        result = await asyncio.to_thread(agent.invoke, initial_state)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    scenario_count = 0
    use_case = ""
    try:
        raw = result.get("final_output", "{}")
        raw = raw.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
        gherkin_data = json.loads(raw)
        scenario_count = len(gherkin_data.get("gherkin_scenarios", []))
        use_case = gherkin_data.get("use_case", "")
    except Exception:
        pass

    return {
        "question": request.question,
        "final_output": result.get("final_output", ""),
        "review_feedback": result.get("review_feedback", ""),
        "generated_scenarios": result.get("generated_scenarios", ""),
        "scenario_count": scenario_count,
        "use_case": use_case,
        # Agent outputs not used by Excel but exposed for ZIP download
        "retrieved_context": result.get("retrieved_context", ""),
        "structured_requirements": result.get("structured_requirements", ""),
        "dependency_mapping": result.get("dependency_mapping", ""),
    }


@app.post("/api/download")
async def download(request: DownloadRequest):
    try:
        excel_bytes = generate_excel(
            question=request.question,
            final_output=request.final_output,
            review_feedback=request.review_feedback,
            generated_scenarios=request.generated_scenarios,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    safe_name = request.question[:40].replace(" ", "_").replace("/", "_")
    filename = f"test_scenarios_{safe_name}.xlsx"

    return StreamingResponse(
        io.BytesIO(excel_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.post("/api/download-zip")
async def download_zip(request: DownloadZipRequest):
    try:
        zip_bytes = generate_zip(
            question=request.question,
            final_output=request.final_output,
            review_feedback=request.review_feedback,
            generated_scenarios=request.generated_scenarios,
            retrieved_context=request.retrieved_context,
            structured_requirements=request.structured_requirements,
            dependency_mapping=request.dependency_mapping,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    safe_name = request.question[:40].replace(" ", "_").replace("/", "_")
    filename = f"test_cases_{safe_name}.zip"

    return StreamingResponse(
        io.BytesIO(zip_bytes),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.post("/api/playwright-run")
async def playwright_run(request: PlaywrightRunRequest):
    try:
        test_code = await asyncio.to_thread(playwright_codegen_agent, request.final_output)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Code generation failed: {e}")

    try:
        execution_results = await asyncio.to_thread(playwright_executor_agent, test_code)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Test execution failed: {e}")

    try:
        review = await asyncio.to_thread(results_review_agent, request.final_output, execution_results)
    except Exception as e:
        review = "{}"

    return {
        "test_code": test_code,
        "execution_results": execution_results,
        "review": review,
    }
