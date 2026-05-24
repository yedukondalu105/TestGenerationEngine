"use client";

import { useState, useRef, useEffect, FormEvent, KeyboardEvent } from "react";
import {
  Send, Download, FileSpreadsheet, Bot, User,
  Loader2, ChevronDown, CheckCircle2, AlertCircle,
  Play, FlaskConical, X, RefreshCw, Clock, ChevronRight,
} from "lucide-react";
import {
  generateTestCases, downloadExcel, downloadZip, runPlaywright,
  getTestSuites, rerunTestSuite,
  GenerateResponse, PlaywrightResponse, RerunResponse, TestSuite,
} from "@/lib/api";

// ─── Types ───────────────────────────────────────────────────────────────────

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  data?: GenerateResponse;
  error?: boolean;
  timestamp: Date;
}

// ─── Constants ───────────────────────────────────────────────────────────────

const TYPE_COLORS: Record<string, string> = {
  "Positive":            "bg-green-100 text-green-800",
  "Negative":            "bg-red-100 text-red-800",
  "Validation":          "bg-yellow-100 text-yellow-800",
  "Authorization":       "bg-blue-100 text-blue-800",
  "Dependency":          "bg-purple-100 text-purple-800",
  "Workflow Transition": "bg-orange-100 text-orange-800",
  "Edge Case":           "bg-cyan-100 text-cyan-800",
  "Cross Module":        "bg-amber-100 text-amber-800",
  "Error Handling":      "bg-rose-100 text-rose-800",
  "Audit Validation":    "bg-emerald-100 text-emerald-800",
};

const PIPELINE_STEPS = ["RAG Retrieval", "Requirements", "Dependencies", "Scenarios", "Gherkin", "Review"];

const SUGGESTED_PROMPTS = [
  "Generate test cases for Trade Amendment workflow",
  "Generate test cases for user login and authentication",
  "Generate test cases for Trade Settlement process",
  "Generate test cases for Trade Approval workflow",
];

// ─── Helpers ─────────────────────────────────────────────────────────────────

function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const m = Math.floor(diff / 60000);
  if (m < 1) return "just now";
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  return `${Math.floor(h / 24)}d ago`;
}

// ─── Sub-components ──────────────────────────────────────────────────────────

function ReviewBadge({ reviewFeedback }: { reviewFeedback: string }) {
  let status = "Unknown";
  try { status = JSON.parse(reviewFeedback).overall_review_status || "Unknown"; } catch {}
  const colors: Record<string, string> = {
    Good:               "bg-green-100 text-green-700 border-green-300",
    Pass:               "bg-green-100 text-green-700 border-green-300",
    "Needs Improvement":"bg-yellow-100 text-yellow-700 border-yellow-300",
    Fail:               "bg-red-100 text-red-700 border-red-300",
  };
  return (
    <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold border ${colors[status] ?? "bg-gray-100 text-gray-600 border-gray-300"}`}>
      <CheckCircle2 className="w-3 h-3" /> Review: {status}
    </span>
  );
}

function ScenarioBreakdown({ finalOutput }: { finalOutput: string }) {
  const [open, setOpen] = useState(false);
  let scenarios: { scenario_type?: string }[] = [];
  try { scenarios = JSON.parse(finalOutput).gherkin_scenarios ?? []; } catch {}
  const counts: Record<string, number> = {};
  for (const s of scenarios) {
    const t = s.scenario_type ?? "Other";
    counts[t] = (counts[t] ?? 0) + 1;
  }
  return (
    <div className="mt-3">
      <button onClick={() => setOpen(o => !o)} className="flex items-center gap-1 text-xs text-blue-600 hover:text-blue-800 font-medium">
        <ChevronDown className={`w-3.5 h-3.5 transition-transform ${open ? "rotate-180" : ""}`} />
        {open ? "Hide" : "Show"} breakdown by type
      </button>
      {open && (
        <div className="mt-2 flex flex-wrap gap-1.5">
          {Object.entries(counts).map(([type, count]) => (
            <span key={type} className={`px-2 py-0.5 rounded-full text-xs font-semibold ${TYPE_COLORS[type] ?? "bg-gray-100 text-gray-700"}`}>
              {type}: {count}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

function PlaywrightResultsPanel({ data }: { data: PlaywrightResponse | RerunResponse }) {
  const [tab, setTab] = useState<"results" | "feature" | "pom" | "code" | "output">("results");

  let review: Record<string, unknown> = {};
  try { review = JSON.parse(data.review); } catch {}

  const ex = data.execution_results;
  const statusColors: Record<string, string> = {
    Pass:    "bg-green-100 text-green-700 border-green-300",
    Partial: "bg-yellow-100 text-yellow-700 border-yellow-300",
    Fail:    "bg-red-100 text-red-700 border-red-300",
  };
  const overallStatus = (review.overall_status as string) || (ex.execution_error ? "Fail" : ex.total > 0 ? "Pass" : "Unknown");

  const tabs: { key: typeof tab; label: string }[] = [
    { key: "results", label: "Results" },
    ...("feature_content" in data ? [
      { key: "feature" as typeof tab, label: "Feature" },
      { key: "pom"     as typeof tab, label: "Page Object" },
      { key: "code"    as typeof tab, label: "Test Code" },
    ] : []),
    { key: "output", label: "Output" },
  ];

  return (
    <div className="mt-4 border border-gray-200 rounded-xl overflow-hidden text-xs">
      <div className="flex items-center justify-between bg-gray-50 px-3 py-2 border-b border-gray-200">
        <span className="font-semibold text-gray-700 flex items-center gap-1.5">
          <Play className="w-3.5 h-3.5 text-violet-600" /> Playwright Results — {data.use_case}
        </span>
        <span className={`px-2 py-0.5 rounded-full font-semibold border ${statusColors[overallStatus] ?? "bg-gray-100 text-gray-600 border-gray-300"}`}>
          {overallStatus} · {ex.passed}/{ex.total} passed
        </span>
      </div>

      <div className="flex border-b border-gray-200 bg-white overflow-x-auto">
        {tabs.map(t => (
          <button key={t.key} onClick={() => setTab(t.key)}
            className={`px-3 py-1.5 whitespace-nowrap font-medium transition-colors ${tab === t.key ? "border-b-2 border-violet-500 text-violet-700" : "text-gray-500 hover:text-gray-700"}`}>
            {t.label}
          </button>
        ))}
      </div>

      <div className="bg-white p-3 max-h-72 overflow-y-auto">
        {tab === "results" && (
          <div className="space-y-1.5">
            {ex.execution_error && <p className="text-red-600 bg-red-50 px-2 py-1 rounded">{ex.execution_error}</p>}
            {typeof review.summary === "string" && <p className="text-gray-600 mb-2">{review.summary}</p>}
            {ex.tests.map((t, i) => (
              <div key={i} className={`flex items-start gap-2 px-2 py-1 rounded ${t.outcome === "passed" ? "bg-green-50" : "bg-red-50"}`}>
                <span className={`font-bold mt-0.5 ${t.outcome === "passed" ? "text-green-600" : "text-red-600"}`}>
                  {t.outcome === "passed" ? "✓" : "✗"}
                </span>
                <div className="flex-1 min-w-0">
                  <span className="font-mono text-gray-800">{t.name}</span>
                  <span className="ml-2 text-gray-400">{t.duration}s</span>
                  {t.message && <p className="text-red-500 mt-0.5 truncate">{t.message}</p>}
                </div>
              </div>
            ))}
            {ex.tests.length === 0 && !ex.execution_error && <p className="text-gray-400 italic">No test results recorded.</p>}
          </div>
        )}
        {"feature_content" in data && tab === "feature" && (
          <pre className="font-mono text-gray-700 whitespace-pre-wrap break-all">{data.feature_content}</pre>
        )}
        {"page_content" in data && tab === "pom" && (
          <pre className="font-mono text-gray-700 whitespace-pre-wrap break-all">{data.page_content}</pre>
        )}
        {"test_content" in data && tab === "code" && (
          <pre className="font-mono text-gray-700 whitespace-pre-wrap break-all">{data.test_content}</pre>
        )}
        {tab === "output" && (
          <pre className="font-mono text-gray-600 whitespace-pre-wrap break-all">{ex.raw_output || "(no output)"}</pre>
        )}
      </div>
    </div>
  );
}

// ─── Saved Suites Panel ───────────────────────────────────────────────────────

function SavedSuitesPanel({ onClose }: { onClose: () => void }) {
  const [suites, setSuites]     = useState<TestSuite[]>([]);
  const [loading, setLoading]   = useState(true);
  const [running, setRunning]   = useState<string | null>(null);
  const [results, setResults]   = useState<Record<string, RerunResponse>>({});
  const [error, setError]       = useState<string | null>(null);

  useEffect(() => {
    getTestSuites()
      .then(setSuites)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  const handleRun = async (suite: TestSuite) => {
    setRunning(suite.id);
    try {
      const result = await rerunTestSuite(suite.id);
      setResults(prev => ({ ...prev, [suite.id]: result }));
      setSuites(prev => prev.map(s => s.id !== suite.id ? s : {
        ...s,
        last_run_at: new Date().toISOString(),
        last_results: {
          passed: result.execution_results.passed,
          failed: result.execution_results.failed,
          total:  result.execution_results.total,
          overall_status: "Unknown",
        },
      }));
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : "Run failed");
    } finally {
      setRunning(null);
    }
  };

  const statusColor = (status: string | undefined) => {
    if (!status) return "bg-gray-100 text-gray-500";
    if (status === "Pass") return "bg-green-100 text-green-700";
    if (status === "Fail") return "bg-red-100 text-red-700";
    return "bg-yellow-100 text-yellow-700";
  };

  return (
    <div className="fixed inset-0 z-50 flex">
      <div className="absolute inset-0 bg-black/30" onClick={onClose} />
      <div className="relative ml-auto h-full w-full max-w-2xl bg-white shadow-2xl flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-200 bg-white flex-shrink-0">
          <div className="flex items-center gap-2">
            <FlaskConical className="w-5 h-5 text-violet-600" />
            <h2 className="font-semibold text-gray-900">Saved Test Suites</h2>
          </div>
          <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-gray-100 transition-colors">
            <X className="w-4 h-4 text-gray-500" />
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto p-5">
          {loading && (
            <div className="flex items-center gap-2 text-gray-500 text-sm">
              <Loader2 className="w-4 h-4 animate-spin" /> Loading suites…
            </div>
          )}
          {error && (
            <div className="flex items-center gap-2 text-red-600 text-sm bg-red-50 px-3 py-2 rounded-lg">
              <AlertCircle className="w-4 h-4" /> {error}
            </div>
          )}
          {!loading && !error && suites.length === 0 && (
            <div className="text-center text-gray-400 text-sm pt-12">
              <FlaskConical className="w-10 h-10 mx-auto mb-3 opacity-30" />
              No test suites yet. Generate and run tests from a chat response to save them here.
            </div>
          )}
          {!loading && suites.length > 0 && (
            <div className="space-y-3">
              {suites.map(suite => (
                <div key={suite.id} className="border border-gray-200 rounded-xl overflow-hidden">
                  {/* Suite header row */}
                  <div className="flex items-center justify-between px-4 py-3 bg-gray-50">
                    <div className="flex-1 min-w-0">
                      <p className="font-semibold text-gray-800 text-sm truncate">{suite.use_case}</p>
                      <div className="flex items-center gap-3 mt-0.5 text-xs text-gray-500">
                        <span>{suite.scenario_count} scenarios</span>
                        <span>·</span>
                        <span>Created {timeAgo(suite.created_at)}</span>
                        {suite.last_run_at && (
                          <>
                            <span>·</span>
                            <span className="flex items-center gap-1">
                              <Clock className="w-3 h-3" /> Last run {timeAgo(suite.last_run_at)}
                            </span>
                          </>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-2 ml-3 flex-shrink-0">
                      {suite.last_results && (
                        <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${statusColor(suite.last_results.overall_status)}`}>
                          {suite.last_results.passed}/{suite.last_results.total} passed
                        </span>
                      )}
                      <button
                        onClick={() => handleRun(suite)}
                        disabled={running === suite.id}
                        className="flex items-center gap-1.5 px-3 py-1.5 bg-violet-600 hover:bg-violet-700 disabled:bg-violet-300 text-white text-xs font-medium rounded-lg transition-colors"
                      >
                        {running === suite.id
                          ? <><Loader2 className="w-3 h-3 animate-spin" /> Running…</>
                          : <><RefreshCw className="w-3 h-3" /> Run</>
                        }
                      </button>
                    </div>
                  </div>

                  {/* File paths */}
                  <div className="px-4 py-2 bg-white border-t border-gray-100 text-xs text-gray-400 font-mono space-y-0.5">
                    <p>📄 tests/{suite.feature_file}</p>
                    <p>🏗 tests/{suite.page_file}</p>
                    <p>🧪 tests/{suite.test_file}</p>
                  </div>

                  {/* Inline results after rerun */}
                  {results[suite.id] && (
                    <div className="border-t border-gray-200">
                      <PlaywrightResultsPanel data={results[suite.id]} />
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ─── Assistant Card ───────────────────────────────────────────────────────────

function AssistantCard({
  message,
  onDownload,
  onDownloadZip,
}: {
  message: Message;
  onDownload: (data: GenerateResponse) => Promise<void>;
  onDownloadZip: (data: GenerateResponse) => Promise<void>;
}) {
  const [downloading, setDownloading]         = useState(false);
  const [downloadingZip, setDownloadingZip]   = useState(false);
  const [runningPlaywright, setRunningPlaywright] = useState(false);
  const [playwrightData, setPlaywrightData]   = useState<PlaywrightResponse | null>(null);
  const [playwrightError, setPlaywrightError] = useState<string | null>(null);

  if (message.error) {
    return (
      <div className="flex gap-3 items-start">
        <Avatar error />
        <div className="bg-red-50 border border-red-200 rounded-2xl rounded-tl-none px-4 py-3 max-w-2xl">
          <div className="flex items-center gap-2 text-red-700">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <p className="text-sm">{message.content}</p>
          </div>
        </div>
      </div>
    );
  }

  const handleDownload = async () => {
    if (!message.data) return;
    setDownloading(true);
    try { await onDownload(message.data); } finally { setDownloading(false); }
  };

  const handleDownloadZip = async () => {
    if (!message.data) return;
    setDownloadingZip(true);
    try { await onDownloadZip(message.data); } finally { setDownloadingZip(false); }
  };

  const handleRunPlaywright = async () => {
    if (!message.data) return;
    setRunningPlaywright(true);
    setPlaywrightData(null);
    setPlaywrightError(null);
    try {
      const result = await runPlaywright(message.data.final_output);
      setPlaywrightData(result);
    } catch (err: unknown) {
      setPlaywrightError(err instanceof Error ? err.message : "Test generation failed");
    } finally {
      setRunningPlaywright(false);
    }
  };

  return (
    <div className="flex gap-3 items-start">
      <Avatar />
      <div className="bg-white border border-gray-200 rounded-2xl rounded-tl-none px-5 py-4 max-w-2xl shadow-sm flex-1 min-w-0">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <p className="text-gray-800 font-medium text-sm leading-relaxed">{message.content}</p>
            {message.data && (
              <>
                <div className="flex items-center flex-wrap gap-2 mt-2">
                  <span className="text-xs text-gray-500">
                    Use case: <span className="font-semibold text-gray-700">{message.data.use_case || "—"}</span>
                  </span>
                  <span className="text-gray-300 text-xs">·</span>
                  <span className="text-xs text-gray-500">
                    <span className="font-bold text-blue-600">{message.data.scenario_count}</span> scenarios
                  </span>
                </div>
                <div className="mt-2">
                  <ReviewBadge reviewFeedback={message.data.review_feedback} />
                </div>
                <ScenarioBreakdown finalOutput={message.data.final_output} />
                {playwrightError && (
                  <div className="mt-3 flex items-center gap-2 text-red-600 text-xs bg-red-50 px-3 py-2 rounded-lg border border-red-200">
                    <AlertCircle className="w-3.5 h-3.5 flex-shrink-0" /> {playwrightError}
                  </div>
                )}
                {playwrightData && <PlaywrightResultsPanel data={playwrightData} />}
              </>
            )}
          </div>

          {message.data && (
            <div className="flex flex-col gap-2 flex-shrink-0">
              <button onClick={handleDownload} disabled={downloading}
                className="flex items-center gap-2 px-3.5 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white text-sm font-medium rounded-xl transition-colors shadow-sm">
                {downloading ? <Loader2 className="w-4 h-4 animate-spin" /> : <FileSpreadsheet className="w-4 h-4" />}
                {downloading ? "Generating…" : "Download Excel"}
              </button>
              <button onClick={handleDownloadZip} disabled={downloadingZip}
                className="flex items-center gap-2 px-3.5 py-2 bg-gray-700 hover:bg-gray-800 disabled:bg-gray-400 text-white text-sm font-medium rounded-xl transition-colors shadow-sm">
                {downloadingZip ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
                {downloadingZip ? "Packaging…" : "Download All"}
              </button>
              <button onClick={handleRunPlaywright} disabled={runningPlaywright}
                className="flex items-center gap-2 px-3.5 py-2 bg-violet-600 hover:bg-violet-700 disabled:bg-violet-300 text-white text-sm font-medium rounded-xl transition-colors shadow-sm">
                {runningPlaywright ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
                {runningPlaywright ? "Generating…" : "Generate & Run Tests"}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function Avatar({ error = false }: { error?: boolean }) {
  return (
    <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5 ${error ? "bg-red-100" : "bg-blue-600"}`}>
      <Bot className={`w-4 h-4 ${error ? "text-red-600" : "text-white"}`} />
    </div>
  );
}

function LoadingIndicator() {
  return (
    <div className="flex gap-3 items-start">
      <Avatar />
      <div className="bg-white border border-gray-200 rounded-2xl rounded-tl-none px-5 py-4 shadow-sm">
        <div className="flex items-center gap-2.5 text-gray-500 text-sm">
          <Loader2 className="w-4 h-4 text-blue-600 animate-spin flex-shrink-0" />
          <span>Running pipeline… this may take a minute</span>
        </div>
        <div className="mt-3 flex flex-wrap gap-1.5">
          {PIPELINE_STEPS.map(step => (
            <span key={step} className="text-xs text-gray-500 bg-gray-100 px-2.5 py-0.5 rounded-full">{step}</span>
          ))}
        </div>
      </div>
    </div>
  );
}

// ─── Main Component ───────────────────────────────────────────────────────────

export default function ChatInterface() {
  const [messages, setMessages]         = useState<Message[]>([]);
  const [input, setInput]               = useState("");
  const [loading, setLoading]           = useState(false);
  const [suitesOpen, setSuitesOpen]     = useState(false);
  const bottomRef                       = useRef<HTMLDivElement>(null);
  const textareaRef                     = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 128)}px`;
  }, [input]);

  const send = async (question: string) => {
    const q = question.trim();
    if (!q || loading) return;
    const userMsg: Message = { id: crypto.randomUUID(), role: "user", content: q, timestamp: new Date() };
    setMessages(prev => [...prev, userMsg]);
    setInput("");
    setLoading(true);
    try {
      const data = await generateTestCases(q);
      const botMsg: Message = {
        id: crypto.randomUUID(), role: "assistant",
        content: `Generated ${data.scenario_count} BDD scenarios for "${data.use_case || q}". Click Generate & Run Tests to create the Cucumber framework, Page Object Model, and execute against the app.`,
        data, timestamp: new Date(),
      };
      setMessages(prev => [...prev, botMsg]);
    } catch (err: unknown) {
      const detail = err instanceof Error ? err.message : "Something went wrong. Please try again.";
      setMessages(prev => [...prev, { id: crypto.randomUUID(), role: "assistant", content: detail, error: true, timestamp: new Date() }]);
    } finally {
      setLoading(false);
      setTimeout(() => textareaRef.current?.focus(), 50);
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(input); }
  };

  const isEmpty = messages.length === 0 && !loading;

  return (
    <div className="flex flex-col h-full bg-gray-50">

      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-3.5 flex items-center justify-between shadow-sm flex-shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-blue-600 flex items-center justify-center shadow-sm">
            <FileSpreadsheet className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="font-semibold text-gray-900 text-base leading-tight">QA Test Cases Generator</h1>
            <p className="text-xs text-gray-400">Graph RAG · LangGraph · BDD Gherkin · Playwright POM</p>
          </div>
        </div>
        <button
          onClick={() => setSuitesOpen(true)}
          className="flex items-center gap-2 px-4 py-2 bg-violet-50 hover:bg-violet-100 text-violet-700 text-sm font-medium rounded-xl transition-colors border border-violet-200"
        >
          <FlaskConical className="w-4 h-4" />
          Saved Test Suites
          <ChevronRight className="w-3.5 h-3.5" />
        </button>
      </header>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-6">
        <div className="max-w-3xl mx-auto space-y-5">
          {isEmpty && (
            <div className="text-center pt-12 pb-4">
              <div className="w-16 h-16 rounded-2xl bg-blue-100 flex items-center justify-center mx-auto mb-4">
                <Bot className="w-8 h-8 text-blue-600" />
              </div>
              <h2 className="text-xl font-semibold text-gray-800 mb-1">Generate BDD Test Cases</h2>
              <p className="text-sm text-gray-500 max-w-sm mx-auto">
                Describe a feature or use case. The pipeline produces Gherkin scenarios, a Cucumber feature file,
                Page Object Model, and executable Playwright tests.
              </p>
              <div className="mt-6 grid grid-cols-1 sm:grid-cols-2 gap-2.5 max-w-xl mx-auto">
                {SUGGESTED_PROMPTS.map(p => (
                  <button key={p} onClick={() => send(p)}
                    className="text-left px-4 py-3 bg-white border border-gray-200 hover:border-blue-400 hover:bg-blue-50 rounded-xl text-sm text-gray-700 transition-colors shadow-sm">
                    {p}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map(msg =>
            msg.role === "user" ? (
              <div key={msg.id} className="flex gap-3 justify-end items-end">
                <div className="bg-blue-600 text-white rounded-2xl rounded-br-none px-4 py-3 max-w-lg shadow-sm">
                  <p className="text-sm leading-relaxed">{msg.content}</p>
                </div>
                <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center flex-shrink-0">
                  <User className="w-4 h-4 text-gray-600" />
                </div>
              </div>
            ) : (
              <AssistantCard key={msg.id} message={msg}
                onDownload={async d => { await downloadExcel(d); }}
                onDownloadZip={async d => { await downloadZip(d); }}
              />
            )
          )}

          {loading && <LoadingIndicator />}
          <div ref={bottomRef} />
        </div>
      </div>

      {/* Input */}
      <div className="border-t border-gray-200 bg-white px-4 py-3.5 flex-shrink-0">
        <div className="max-w-3xl mx-auto">
          <div className="flex gap-2.5 items-end">
            <textarea ref={textareaRef} value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={loading}
              placeholder="Describe a feature or use case to generate test cases…"
              rows={1}
              className="flex-1 resize-none rounded-xl border border-gray-300 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 px-4 py-3 text-sm text-gray-900 placeholder-gray-400 bg-gray-50 outline-none transition-all overflow-y-auto disabled:opacity-50"
              style={{ minHeight: "48px", maxHeight: "128px" }}
            />
            <button onClick={() => send(input)} disabled={!input.trim() || loading}
              className="w-11 h-11 rounded-xl bg-blue-600 hover:bg-blue-700 disabled:bg-gray-200 flex items-center justify-center transition-colors flex-shrink-0 shadow-sm"
              aria-label="Send">
              <Send className="w-4 h-4 text-white" />
            </button>
          </div>
          <p className="text-xs text-gray-400 mt-1.5 text-center">Enter to send · Shift+Enter for new line</p>
        </div>
      </div>

      {/* Saved Suites Drawer */}
      {suitesOpen && <SavedSuitesPanel onClose={() => setSuitesOpen(false)} />}
    </div>
  );
}
