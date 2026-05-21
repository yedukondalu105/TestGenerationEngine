import io
import zipfile

from excel_generator import generate_excel


def generate_zip(
    question: str,
    final_output: str,
    review_feedback: str,
    generated_scenarios: str,
    retrieved_context: str = "",
    structured_requirements: str = "",
    dependency_mapping: str = "",
) -> bytes:
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        # Excel file (identical to the standalone download)
        excel_bytes = generate_excel(
            question=question,
            final_output=final_output,
            review_feedback=review_feedback,
            generated_scenarios=generated_scenarios,
        )
        safe_name = question[:40].replace(" ", "_").replace("/", "_")
        zf.writestr(f"test_scenarios_{safe_name}.xlsx", excel_bytes)

        # One text file per agent / pipeline node
        agents = [
            ("01_retrieve_context.txt", retrieved_context),
            ("02_requirement_understanding.txt", structured_requirements),
            ("03_dependency_mapping.txt", dependency_mapping),
            ("04_scenario_generation.txt", generated_scenarios),
            ("05_gherkin_generation.txt", final_output),
            ("06_review_agent.txt", review_feedback),
        ]
        for filename, content in agents:
            zf.writestr(filename, content if content else "(No output captured)")

    return zip_buffer.getvalue()
