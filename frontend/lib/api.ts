export interface GenerateResponse {
  question: string;
  final_output: string;
  review_feedback: string;
  generated_scenarios: string;
  scenario_count: number;
  use_case: string;
  retrieved_context: string;
  structured_requirements: string;
  dependency_mapping: string;
}

export async function generateTestCases(question: string): Promise<GenerateResponse> {
  const res = await fetch("/api/generate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Request failed (${res.status})`);
  }
  return res.json();
}

export async function downloadExcel(data: {
  question: string;
  final_output: string;
  review_feedback: string;
  generated_scenarios: string;
}): Promise<void> {
  const res = await fetch("/api/download", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Download failed");

  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `test_scenarios_${data.question.slice(0, 40).replace(/\s+/g, "_")}.xlsx`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

export interface PlaywrightTestResult {
  name: string;
  outcome: "passed" | "failed" | "error" | string;
  duration: number;
  message: string;
}

export interface PlaywrightExecutionResults {
  passed: number;
  failed: number;
  error: number;
  total: number;
  tests: PlaywrightTestResult[];
  raw_output: string;
  execution_error: string | null;
}

export interface PlaywrightResponse {
  test_code: string;
  execution_results: PlaywrightExecutionResults;
  review: string;
}

export async function runPlaywright(final_output: string): Promise<PlaywrightResponse> {
  const res = await fetch("/api/playwright-run", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ final_output }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Playwright run failed (${res.status})`);
  }
  return res.json();
}

export async function downloadZip(data: GenerateResponse): Promise<void> {
  const res = await fetch("/api/download-zip", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Download failed");

  const blob = await res.blob();
  const contentDisposition = res.headers.get("Content-Disposition") ?? "";
  const filenameMatch = contentDisposition.match(/filename="(.+?)"/);
  const filename = filenameMatch
    ? filenameMatch[1]
    : `test_cases_${data.question.slice(0, 40).replace(/\s+/g, "_")}.zip`;

  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
