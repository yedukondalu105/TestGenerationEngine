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
  suite_id: string;
  use_case: string;
  feature_content: string;
  page_content: string;
  test_content: string;
  execution_results: PlaywrightExecutionResults;
  review: string;
}

export interface TestSuiteLastResults {
  passed: number;
  failed: number;
  total: number;
  overall_status: string;
}

export interface TestSuite {
  id: string;
  use_case: string;
  slug: string;
  created_at: string;
  scenario_count: number;
  feature_file: string;
  page_file: string;
  test_file: string;
  last_run_at: string | null;
  last_results: TestSuiteLastResults | null;
}

export interface RerunResponse {
  suite_id: string;
  use_case: string;
  execution_results: PlaywrightExecutionResults;
  review: string;
}

export interface GenerateSuiteResponse {
  suite_id: string;
  use_case: string;
  feature_content: string;
  page_content: string;
  test_content: string;
}

export async function generatePlaywrightTests(final_output: string): Promise<GenerateSuiteResponse> {
  const res = await fetch("/api/playwright-generate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ final_output }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail || `Test generation failed (${res.status})`);
  }
  return res.json();
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

export async function getTestSuites(): Promise<TestSuite[]> {
  const res = await fetch("/api/test-suites");
  if (!res.ok) throw new Error("Failed to load test suites");
  const data = await res.json();
  return data.suites ?? [];
}

export async function rerunTestSuite(suiteId: string): Promise<RerunResponse> {
  const res = await fetch(`/api/test-suites/${suiteId}/run`, { method: "POST" });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Rerun failed (${res.status})`);
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
