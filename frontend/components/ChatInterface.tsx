"use client";

import { useState, useRef, useEffect, KeyboardEvent } from "react";
import {
  Send, Download, FileSpreadsheet, Bot, User,
  Loader2, ChevronDown, CheckCircle2, AlertCircle,
  Play, FlaskConical, X, RefreshCw, Clock, ChevronRight,
  Trash2, Eye, Upload, MessageSquare, Save, Pencil,
} from "lucide-react";
import {
  generateTestCases, downloadExcel, downloadZip,
  generatePlaywrightTests, saveSuite, regenerateScenarios, regenerateScripts,
  getTestSuites, rerunTestSuite, getSuiteFiles, deleteSuite,
  regenerateSuiteScripts, updateSuiteScripts,
  GenerateResponse, SuitePreviewResponse,
  PlaywrightResponse, RerunResponse, TestSuite, SuiteFilesResponse,
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

type WorkflowStage =
  | "scenario_review"
  | "regenerating_scenarios"
  | "generating_scripts"
  | "script_review"
  | "regenerating_scripts"
  | "suite_saved";

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
  let scenarios: { scenario_type?: string; scenario_name?: string }[] = [];
  try { scenarios = JSON.parse(finalOutput).gherkin_scenarios ?? []; } catch {}
  const grouped: Record<string, { scenario_type?: string; scenario_name?: string }[]> = {};
  for (const s of scenarios) {
    const t = s.scenario_type ?? "Other";
    if (!grouped[t]) grouped[t] = [];
    grouped[t].push(s);
  }
  return (
    <div className="mt-3">
      <button onClick={() => setOpen(o => !o)} className="flex items-center gap-1 text-xs text-blue-600 hover:text-blue-800 font-medium">
        <ChevronDown className={`w-3.5 h-3.5 transition-transform ${open ? "rotate-180" : ""}`} />
        {open ? "Hide" : "Show"} breakdown by type ({scenarios.length} total)
      </button>
      {open && (
        <div className="mt-2 space-y-2">
          {Object.entries(grouped).map(([type, items]) => (
            <ScenarioTypeGroup key={type} type={type} items={items} />
          ))}
        </div>
      )}
    </div>
  );
}

function ScenarioTypeGroup({ type, items }: { type: string; items: { scenario_name?: string }[] }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden">
      <button
        onClick={() => setOpen(o => !o)}
        className="w-full flex items-center justify-between px-3 py-1.5 bg-gray-50 hover:bg-gray-100 text-xs font-medium text-gray-700"
      >
        <span className="flex items-center gap-2">
          <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${TYPE_COLORS[type] ?? "bg-gray-100 text-gray-700"}`}>{type}</span>
          <span className="text-gray-500">{items.length} scenario{items.length !== 1 ? "s" : ""}</span>
        </span>
        <ChevronDown className={`w-3.5 h-3.5 text-gray-400 transition-transform ${open ? "rotate-180" : ""}`} />
      </button>
      {open && (
        <div className="divide-y divide-gray-100">
          {items.map((item, i) => (
            <div key={i} className="px-3 py-1.5 text-xs text-gray-600 bg-white">
              {item.scenario_name ?? `Scenario ${i + 1}`}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ─── Scenario Review Gate ────────────────────────────────────────────────────

function ScenarioReviewGate({
  finalOutput,
  onFinalOutputChange,
  onApprove,
  onRegenerate,
  regenerating,
}: {
  finalOutput: string;
  onFinalOutputChange: (newOutput: string) => void;
  onApprove: () => void;
  onRegenerate: (feedback: string) => void;
  regenerating: boolean;
}) {
  const [feedback, setFeedback] = useState("");
  const [uploadError, setUploadError] = useState<string | null>(null);

  const handleUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploadError(null);
    const reader = new FileReader();
    reader.onload = (ev) => {
      const text = ev.target?.result as string;
      try {
        JSON.parse(text);
        onFinalOutputChange(text);
      } catch {
        setUploadError("Invalid JSON file. Please upload a valid Gherkin JSON.");
      }
    };
    reader.readAsText(file);
    e.target.value = "";
  };

  let scenarioCount = 0;
  try { scenarioCount = JSON.parse(finalOutput).gherkin_scenarios?.length ?? 0; } catch {}

  return (
    <div className="mt-4 border border-amber-200 rounded-xl overflow-hidden text-xs bg-amber-50">
      <div className="flex items-center gap-2 px-3 py-2 bg-amber-100 border-b border-amber-200">
        <MessageSquare className="w-3.5 h-3.5 text-amber-700" />
        <span className="font-semibold text-amber-800">Review Generated Scenarios</span>
        <span className="ml-auto text-amber-600 font-medium">{scenarioCount} scenarios ready</span>
      </div>

      <div className="p-3 space-y-3 bg-white">
        <p className="text-gray-600 text-xs">
          Review the scenarios below. You can approve them to generate Playwright tests, provide feedback for re-generation, or upload a modified JSON file.
        </p>

        <ScenarioBreakdown finalOutput={finalOutput} />

        <div className="space-y-2">
          <label className="block text-xs font-medium text-gray-700">Feedback for re-generation (optional)</label>
          <textarea
            value={feedback}
            onChange={e => setFeedback(e.target.value)}
            placeholder="E.g. Add more edge cases for empty fields, include concurrent login scenarios…"
            rows={3}
            className="w-full resize-none rounded-lg border border-gray-300 focus:border-amber-400 focus:ring-1 focus:ring-amber-200 px-3 py-2 text-xs text-gray-900 placeholder-gray-400 bg-gray-50 outline-none"
          />
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          <label className="flex items-center gap-1.5 px-3 py-1.5 border border-gray-300 rounded-lg text-gray-600 hover:bg-gray-50 cursor-pointer transition-colors">
            <Upload className="w-3.5 h-3.5" />
            Upload modified JSON
            <input type="file" accept=".json" className="hidden" onChange={handleUpload} />
          </label>
          {uploadError && <span className="text-red-500 text-xs">{uploadError}</span>}
        </div>

        <div className="flex items-center gap-2 pt-1 border-t border-gray-100">
          <button
            onClick={() => onRegenerate(feedback)}
            disabled={regenerating}
            className="flex items-center gap-1.5 px-3 py-1.5 border border-amber-400 text-amber-700 hover:bg-amber-50 disabled:opacity-50 rounded-lg font-medium transition-colors"
          >
            {regenerating ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <RefreshCw className="w-3.5 h-3.5" />}
            Re-generate Scenarios
          </button>
          <button
            onClick={onApprove}
            disabled={regenerating}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-violet-600 hover:bg-violet-700 disabled:opacity-50 text-white rounded-lg font-medium transition-colors ml-auto"
          >
            <FlaskConical className="w-3.5 h-3.5" />
            Approve &amp; Generate Tests →
          </button>
        </div>
      </div>
    </div>
  );
}

// ─── Script Review Gate ───────────────────────────────────────────────────────

function ScriptReviewGate({
  previewData,
  finalOutput,
  onApprove,
  onRegenerate,
  regenerating,
}: {
  previewData: SuitePreviewResponse;
  finalOutput: string;
  onApprove: (data: SuitePreviewResponse) => void;
  onRegenerate: (feedback: string) => void;
  regenerating: boolean;
}) {
  const [tab, setTab] = useState<"feature" | "pom" | "code">("feature");
  const [feedback, setFeedback] = useState("");
  const [featureText, setFeatureText] = useState(previewData.feature_content);
  const [pomText, setPomText]         = useState(previewData.page_content);
  const [codeText, setCodeText]       = useState(previewData.test_content);

  // Sync textarea state when previewData changes after regen
  useEffect(() => {
    setPomText(previewData.page_content);
    setCodeText(previewData.test_content);
  }, [previewData.page_content, previewData.test_content]);

  const handleApprove = () => {
    onApprove({
      ...previewData,
      feature_content: featureText,
      page_content: pomText,
      test_content: codeText,
    });
  };

  const tabs: { key: typeof tab; label: string }[] = [
    { key: "feature", label: "Feature File" },
    { key: "pom",     label: "Page Object" },
    { key: "code",    label: "Test Code" },
  ];

  return (
    <div className="mt-4 border border-violet-200 rounded-xl overflow-hidden text-xs">
      <div className="flex items-center gap-2 px-3 py-2 bg-violet-50 border-b border-violet-200">
        <Eye className="w-3.5 h-3.5 text-violet-700" />
        <span className="font-semibold text-violet-800">Review Generated Scripts</span>
        <span className="ml-auto text-violet-600 font-medium">{previewData.use_case}</span>
      </div>

      <div className="bg-white">
        <div className="flex border-b border-gray-200 overflow-x-auto">
          {tabs.map(t => (
            <button key={t.key} onClick={() => setTab(t.key)}
              className={`px-3 py-1.5 whitespace-nowrap font-medium transition-colors ${tab === t.key ? "border-b-2 border-violet-500 text-violet-700" : "text-gray-500 hover:text-gray-700"}`}>
              {t.label}
            </button>
          ))}
        </div>

        <div className="p-3">
          {tab === "feature" && (
            <textarea
              value={featureText}
              onChange={e => setFeatureText(e.target.value)}
              rows={12}
              className="w-full font-mono text-xs text-gray-700 bg-gray-50 border border-gray-200 rounded-lg px-3 py-2 resize-y outline-none focus:border-violet-300 focus:ring-1 focus:ring-violet-100"
            />
          )}
          {tab === "pom" && (
            <textarea
              value={pomText}
              onChange={e => setPomText(e.target.value)}
              rows={12}
              className="w-full font-mono text-xs text-gray-700 bg-gray-50 border border-gray-200 rounded-lg px-3 py-2 resize-y outline-none focus:border-violet-300 focus:ring-1 focus:ring-violet-100"
            />
          )}
          {tab === "code" && (
            <textarea
              value={codeText}
              onChange={e => setCodeText(e.target.value)}
              rows={12}
              className="w-full font-mono text-xs text-gray-700 bg-gray-50 border border-gray-200 rounded-lg px-3 py-2 resize-y outline-none focus:border-violet-300 focus:ring-1 focus:ring-violet-100"
            />
          )}
        </div>

        <div className="px-3 pb-3 space-y-2 border-t border-gray-100 pt-2">
          <label className="block text-xs font-medium text-gray-700">Feedback for script re-generation (optional)</label>
          <textarea
            value={feedback}
            onChange={e => setFeedback(e.target.value)}
            placeholder="E.g. Use more specific locators, add wait_for_load_state after navigation…"
            rows={2}
            className="w-full resize-none rounded-lg border border-gray-300 focus:border-violet-400 focus:ring-1 focus:ring-violet-200 px-3 py-2 text-xs text-gray-900 placeholder-gray-400 bg-gray-50 outline-none"
          />
          <div className="flex items-center gap-2">
            <button
              onClick={() => onRegenerate(feedback)}
              disabled={regenerating}
              className="flex items-center gap-1.5 px-3 py-1.5 border border-violet-400 text-violet-700 hover:bg-violet-50 disabled:opacity-50 rounded-lg font-medium transition-colors"
            >
              {regenerating ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <RefreshCw className="w-3.5 h-3.5" />}
              Re-generate Scripts
            </button>
            <button
              onClick={handleApprove}
              disabled={regenerating}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white rounded-lg font-medium transition-colors ml-auto"
            >
              <Save className="w-3.5 h-3.5" />
              Approve &amp; Save Suite
            </button>
          </div>
        </div>
      </div>
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

// ─── Suite Script Editor ──────────────────────────────────────────────────────

function SuiteScriptEditor({
  suiteId,
  initialFiles,
  onSaved,
  onClose,
}: {
  suiteId: string;
  initialFiles: SuiteFilesResponse;
  onSaved: (updated: SuiteFilesResponse) => void;
  onClose: () => void;
}) {
  const [tab, setTab]             = useState<"feature" | "pom" | "code">("feature");
  const [featureText, setFeature] = useState(initialFiles.feature_content);
  const [pomText, setPom]         = useState(initialFiles.page_content);
  const [codeText, setCode]       = useState(initialFiles.test_content);
  const [feedback, setFeedback]   = useState("");
  const [regenerating, setRegen]  = useState(false);
  const [saving, setSaving]       = useState(false);
  const [error, setError]         = useState<string | null>(null);
  const [savedOk, setSavedOk]     = useState(false);

  const handleRegen = async () => {
    setError(null);
    setRegen(true);
    try {
      const result = await regenerateSuiteScripts(suiteId, featureText, feedback);
      setPom(result.page_content);
      setCode(result.test_content);
      setTab("pom");
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Re-generation failed");
    } finally {
      setRegen(false);
    }
  };

  const handleSave = async () => {
    setError(null);
    setSaving(true);
    try {
      await updateSuiteScripts(suiteId, featureText, pomText, codeText);
      setSavedOk(true);
      onSaved({ ...initialFiles, feature_content: featureText, page_content: pomText, test_content: codeText });
      setTimeout(() => setSavedOk(false), 3000);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Save failed");
    } finally {
      setSaving(false);
    }
  };

  const tabs: { key: typeof tab; label: string }[] = [
    { key: "feature", label: "Feature File" },
    { key: "pom",     label: "Page Object" },
    { key: "code",    label: "Test Code" },
  ];

  return (
    <div className="border-t border-violet-200 bg-white">
      <div className="flex items-center justify-between px-4 py-2 bg-violet-50 border-b border-violet-200">
        <span className="text-xs font-semibold text-violet-800 flex items-center gap-1.5">
          <Pencil className="w-3.5 h-3.5" /> Edit Scripts
        </span>
        <button onClick={onClose} className="text-xs text-gray-400 hover:text-gray-600 flex items-center gap-1">
          <X className="w-3.5 h-3.5" /> Close
        </button>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-gray-200 overflow-x-auto bg-white">
        {tabs.map(t => (
          <button key={t.key} onClick={() => setTab(t.key)}
            className={`px-3 py-1.5 text-xs whitespace-nowrap font-medium transition-colors ${tab === t.key ? "border-b-2 border-violet-500 text-violet-700" : "text-gray-500 hover:text-gray-700"}`}>
            {t.label}
          </button>
        ))}
      </div>

      <div className="p-3">
        {tab === "feature" && (
          <textarea value={featureText} onChange={e => setFeature(e.target.value)} rows={12}
            className="w-full font-mono text-xs text-gray-700 bg-gray-50 border border-gray-200 rounded-lg px-3 py-2 resize-y outline-none focus:border-violet-300 focus:ring-1 focus:ring-violet-100" />
        )}
        {tab === "pom" && (
          <textarea value={pomText} onChange={e => setPom(e.target.value)} rows={12}
            className="w-full font-mono text-xs text-gray-700 bg-gray-50 border border-gray-200 rounded-lg px-3 py-2 resize-y outline-none focus:border-violet-300 focus:ring-1 focus:ring-violet-100" />
        )}
        {tab === "code" && (
          <textarea value={codeText} onChange={e => setCode(e.target.value)} rows={12}
            className="w-full font-mono text-xs text-gray-700 bg-gray-50 border border-gray-200 rounded-lg px-3 py-2 resize-y outline-none focus:border-violet-300 focus:ring-1 focus:ring-violet-100" />
        )}
      </div>

      <div className="px-3 pb-3 space-y-2 border-t border-gray-100 pt-2">
        <label className="block text-xs font-medium text-gray-700">Feedback for re-generating POM &amp; Test (uses current Feature file as context)</label>
        <textarea value={feedback} onChange={e => setFeedback(e.target.value)}
          placeholder="E.g. Use more specific locators, fix assertion for empty fields…"
          rows={2}
          className="w-full resize-none rounded-lg border border-gray-300 focus:border-violet-400 focus:ring-1 focus:ring-violet-200 px-3 py-2 text-xs text-gray-900 placeholder-gray-400 bg-gray-50 outline-none" />

        {error && (
          <div className="flex items-center gap-2 text-red-600 text-xs bg-red-50 px-3 py-2 rounded-lg border border-red-200">
            <AlertCircle className="w-3.5 h-3.5 flex-shrink-0" /> {error}
          </div>
        )}

        <div className="flex items-center gap-2">
          <button onClick={handleRegen} disabled={regenerating || saving}
            className="flex items-center gap-1.5 px-3 py-1.5 border border-violet-400 text-violet-700 hover:bg-violet-50 disabled:opacity-50 rounded-lg text-xs font-medium transition-colors">
            {regenerating ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <RefreshCw className="w-3.5 h-3.5" />}
            Re-generate POM &amp; Test
          </button>
          <button onClick={handleSave} disabled={saving || regenerating}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ml-auto ${
              savedOk
                ? "bg-green-600 text-white"
                : "bg-violet-600 hover:bg-violet-700 disabled:opacity-50 text-white"
            }`}>
            {saving
              ? <><Loader2 className="w-3.5 h-3.5 animate-spin" /> Saving…</>
              : savedOk
                ? <><CheckCircle2 className="w-3.5 h-3.5" /> Saved — re-run to apply</>
                : <><Save className="w-3.5 h-3.5" /> Save Changes</>
            }
          </button>
        </div>
        {savedOk && (
          <p className="text-xs text-green-600">Scripts updated on disk. Run the suite again to test the new version.</p>
        )}
      </div>
    </div>
  );
}

function SuiteCard({
  suite,
  onRun,
  onDelete,
  running,
  runResult,
}: {
  suite: TestSuite;
  onRun: () => void;
  onDelete: () => void;
  running: boolean;
  runResult: RerunResponse | null;
}) {
  const [expanded, setExpanded]         = useState(false);
  const [editMode, setEditMode]         = useState(false);
  const [files, setFiles]               = useState<SuiteFilesResponse | null>(null);
  const [loadingFiles, setLoadingFiles] = useState(false);
  const [filesError, setFilesError]     = useState<string | null>(null);
  const [fileTab, setFileTab]           = useState<"feature" | "pom" | "code">("feature");
  const [confirmDelete, setConfirmDelete] = useState(false);
  const confirmTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const loadFiles = async () => {
    if (files || loadingFiles) return;
    setLoadingFiles(true);
    setFilesError(null);
    try {
      const f = await getSuiteFiles(suite.id);
      setFiles(f);
    } catch (e: unknown) {
      setFilesError(e instanceof Error ? e.message : "Failed to load files");
    } finally {
      setLoadingFiles(false);
    }
  };

  const handleExpand = async () => {
    const next = !expanded;
    setExpanded(next);
    if (next) await loadFiles();
  };

  const handleEditScripts = async () => {
    await loadFiles();
    setExpanded(true);
    setEditMode(true);
  };

  const handleDeleteClick = () => {
    if (confirmDelete) {
      if (confirmTimerRef.current) clearTimeout(confirmTimerRef.current);
      setConfirmDelete(false);
      onDelete();
    } else {
      setConfirmDelete(true);
      confirmTimerRef.current = setTimeout(() => setConfirmDelete(false), 5000);
    }
  };

  useEffect(() => () => { if (confirmTimerRef.current) clearTimeout(confirmTimerRef.current); }, []);

  const last = suite.last_results;

  return (
    <div className="border border-gray-200 rounded-xl overflow-hidden">
      {/* Suite header */}
      <div className="flex items-center justify-between px-4 py-3 bg-gray-50">
        <button onClick={handleExpand} className="flex-1 min-w-0 text-left flex items-center gap-2">
          <ChevronDown className={`w-4 h-4 text-gray-400 flex-shrink-0 transition-transform ${expanded ? "rotate-180" : ""}`} />
          <div className="min-w-0">
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
        </button>

        <div className="flex items-center gap-2 ml-3 flex-shrink-0">
          {last ? (
            <div className="flex flex-col items-end gap-1 min-w-[72px]">
              <span className="text-xs text-gray-600 font-medium">
                {last.passed}/{last.total} passed
              </span>
              <div className="w-full h-1.5 rounded-full bg-gray-200 overflow-hidden flex">
                {last.total > 0 && (
                  <>
                    <div className="h-full bg-green-500 transition-all" style={{ width: `${(last.passed / last.total) * 100}%` }} />
                    <div className="h-full bg-red-400 transition-all" style={{ width: `${(last.failed / last.total) * 100}%` }} />
                  </>
                )}
              </div>
            </div>
          ) : (
            <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-gray-100 text-gray-500 border border-gray-200 whitespace-nowrap">
              Never run
            </span>
          )}
          <button
            onClick={onRun}
            disabled={running}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-violet-600 hover:bg-violet-700 disabled:bg-violet-300 text-white text-xs font-medium rounded-lg transition-colors"
          >
            {running
              ? <><Loader2 className="w-3 h-3 animate-spin" /> Running…</>
              : <><RefreshCw className="w-3 h-3" /> Run</>
            }
          </button>
          <button
            onClick={handleEditScripts}
            title="Edit scripts"
            className={`flex items-center gap-1 px-2.5 py-1.5 text-xs font-medium rounded-lg border transition-colors ${
              editMode
                ? "bg-violet-600 text-white border-violet-600"
                : "border-violet-300 text-violet-600 hover:bg-violet-50"
            }`}
          >
            <Pencil className="w-3 h-3" />
          </button>
          <button
            onClick={handleDeleteClick}
            className={`flex items-center gap-1 px-2.5 py-1.5 text-xs font-medium rounded-lg border transition-colors ${
              confirmDelete
                ? "bg-red-600 text-white border-red-600 hover:bg-red-700"
                : "border-red-300 text-red-600 hover:bg-red-50"
            }`}
            title={confirmDelete ? "Click again to confirm delete" : "Delete suite"}
          >
            <Trash2 className="w-3 h-3" />
            {confirmDelete ? "Confirm?" : ""}
          </button>
        </div>
      </div>

      {/* Expanded: file paths + file viewer or script editor */}
      {expanded && (
        <div className="border-t border-gray-100">
          <div className="px-4 py-2 bg-white text-xs text-gray-400 font-mono space-y-0.5">
            <p>📄 tests/{suite.feature_file}</p>
            <p>🏗 tests/{suite.page_file}</p>
            <p>🧪 tests/{suite.test_file}</p>
          </div>

          {loadingFiles && (
            <div className="flex items-center gap-2 px-4 py-3 text-xs text-gray-500">
              <Loader2 className="w-3.5 h-3.5 animate-spin" /> Loading files…
            </div>
          )}
          {filesError && (
            <div className="px-4 py-2 text-xs text-red-600 bg-red-50">{filesError}</div>
          )}

          {/* Edit mode: inline script editor */}
          {files && editMode && (
            <SuiteScriptEditor
              suiteId={suite.id}
              initialFiles={files}
              onSaved={(updated) => { setFiles(updated); setEditMode(false); }}
              onClose={() => setEditMode(false)}
            />
          )}

          {/* View mode: read-only file viewer */}
          {files && !editMode && (
            <div className="border-t border-gray-100">
              <div className="flex border-b border-gray-200 bg-white overflow-x-auto">
                {(["feature", "pom", "code"] as const).map(k => (
                  <button key={k} onClick={() => setFileTab(k)}
                    className={`px-3 py-1.5 text-xs whitespace-nowrap font-medium transition-colors ${fileTab === k ? "border-b-2 border-violet-500 text-violet-700" : "text-gray-500 hover:text-gray-700"}`}>
                    {k === "feature" ? "Feature" : k === "pom" ? "Page Object" : "Test Code"}
                  </button>
                ))}
              </div>
              <div className="p-3 max-h-64 overflow-y-auto bg-white">
                <pre className="font-mono text-xs text-gray-700 whitespace-pre-wrap break-all">
                  {fileTab === "feature" ? files.feature_content : fileTab === "pom" ? files.page_content : files.test_content}
                </pre>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Inline results after rerun */}
      {runResult && (
        <div className="border-t border-gray-200">
          <PlaywrightResultsPanel data={runResult} />
        </div>
      )}
    </div>
  );
}

function SavedSuitesPanel({ onClose }: { onClose: () => void }) {
  const [suites, setSuites]   = useState<TestSuite[]>([]);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState<string | null>(null);
  const [results, setResults] = useState<Record<string, RerunResponse>>({});
  const [error, setError]     = useState<string | null>(null);

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

  const handleDelete = async (suiteId: string) => {
    try {
      await deleteSuite(suiteId);
      setSuites(prev => prev.filter(s => s.id !== suiteId));
      setResults(prev => { const n = { ...prev }; delete n[suiteId]; return n; });
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : "Delete failed");
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex">
      <div className="absolute inset-0 bg-black/30" onClick={onClose} />
      <div className="relative ml-auto h-full w-full max-w-2xl bg-white shadow-2xl flex flex-col">
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-200 bg-white flex-shrink-0">
          <div className="flex items-center gap-2">
            <FlaskConical className="w-5 h-5 text-violet-600" />
            <h2 className="font-semibold text-gray-900">Saved Test Suites</h2>
          </div>
          <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-gray-100 transition-colors">
            <X className="w-4 h-4 text-gray-500" />
          </button>
        </div>

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
              No test suites yet. Generate tests from a chat response, then run them here.
            </div>
          )}
          {!loading && suites.length > 0 && (
            <div className="space-y-3">
              {suites.map(suite => (
                <SuiteCard
                  key={suite.id}
                  suite={suite}
                  onRun={() => handleRun(suite)}
                  onDelete={() => handleDelete(suite.id)}
                  running={running === suite.id}
                  runResult={results[suite.id] ?? null}
                />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ─── Suite Saved Panel ────────────────────────────────────────────────────────

function SuiteSavedPanel({ suiteId, useCase, onViewSuites }: { suiteId: string; useCase: string; onViewSuites: () => void }) {
  return (
    <div className="mt-4 border border-green-200 rounded-xl overflow-hidden text-xs bg-green-50">
      <div className="flex items-center justify-between px-3 py-2.5 bg-green-100 border-b border-green-200">
        <span className="font-semibold text-green-700 flex items-center gap-1.5">
          <CheckCircle2 className="w-3.5 h-3.5" /> Suite saved — {useCase}
        </span>
        <button
          onClick={onViewSuites}
          className="flex items-center gap-1 text-violet-600 hover:text-violet-800 font-semibold text-xs transition-colors"
        >
          View &amp; Run in Saved Test Suites <ChevronRight className="w-3 h-3" />
        </button>
      </div>
      <div className="px-3 py-2 text-gray-600">
        Suite ID: <span className="font-mono text-gray-800">{suiteId}</span>. Open Saved Test Suites to run or review the files.
      </div>
    </div>
  );
}

// ─── Assistant Card ───────────────────────────────────────────────────────────

function AssistantCard({
  message,
  onDownload,
  onDownloadZip,
  onOpenSuites,
}: {
  message: Message;
  onDownload: (data: GenerateResponse) => Promise<void>;
  onDownloadZip: (data: GenerateResponse) => Promise<void>;
  onOpenSuites: () => void;
}) {
  const [downloading, setDownloading]       = useState(false);
  const [downloadingZip, setDownloadingZip] = useState(false);
  const [stage, setStage]                   = useState<WorkflowStage>("scenario_review");
  const [localFinalOutput, setLocalFinalOutput] = useState(message.data?.final_output ?? "");
  const [previewData, setPreviewData]       = useState<SuitePreviewResponse | null>(null);
  const [savedSuiteId, setSavedSuiteId]     = useState<string | null>(null);
  const [savedUseCase, setSavedUseCase]     = useState<string>("");
  const [stageError, setStageError]         = useState<string | null>(null);

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

  const handleRegenScenarios = async (feedback: string) => {
    if (!message.data) return;
    setStageError(null);
    setStage("regenerating_scenarios");
    try {
      const result = await regenerateScenarios(message.data.question, feedback);
      setLocalFinalOutput(result.final_output);
      setStage("scenario_review");
    } catch (err: unknown) {
      setStageError(err instanceof Error ? err.message : "Re-generation failed");
      setStage("scenario_review");
    }
  };

  const handleApproveScenarios = async () => {
    setStageError(null);
    setStage("generating_scripts");
    try {
      const result = await generatePlaywrightTests(localFinalOutput);
      setPreviewData(result);
      setStage("script_review");
    } catch (err: unknown) {
      setStageError(err instanceof Error ? err.message : "Script generation failed");
      setStage("scenario_review");
    }
  };

  const handleRegenScripts = async (feedback: string) => {
    setStageError(null);
    setStage("regenerating_scripts");
    try {
      const result = await regenerateScripts(localFinalOutput, feedback);
      setPreviewData(prev => prev ? { ...prev, page_content: result.page_content, test_content: result.test_content } : prev);
      setStage("script_review");
    } catch (err: unknown) {
      setStageError(err instanceof Error ? err.message : "Script re-generation failed");
      setStage("script_review");
    }
  };

  const handleApproveScripts = async (editedData: SuitePreviewResponse) => {
    setStageError(null);
    try {
      const saved = await saveSuite(editedData);
      setSavedSuiteId(saved.suite_id);
      setSavedUseCase(saved.use_case);
      setStage("suite_saved");
    } catch (err: unknown) {
      setStageError(err instanceof Error ? err.message : "Save failed");
    }
  };

  const isGeneratingScripts   = stage === "generating_scripts";
  const isRegeneratingScripts = stage === "regenerating_scripts";
  const isRegeneratingScenarios = stage === "regenerating_scenarios";

  // Phase tracker state
  const scenariosDone = true;
  const testsDone     = stage === "suite_saved";
  const testsActive   = isGeneratingScripts || isRegeneratingScripts || stage === "script_review";

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

                {/* Phase tracker */}
                <div className="mt-3 flex items-center gap-2 text-xs">
                  <div className="flex items-center gap-1 text-green-700 font-medium">
                    <CheckCircle2 className="w-3.5 h-3.5" /><span>Scenarios</span>
                  </div>
                  <ChevronRight className="w-3 h-3 text-gray-300" />
                  <div className={`flex items-center gap-1 font-medium ${testsDone ? "text-green-700" : testsActive ? "text-violet-600" : "text-gray-400"}`}>
                    {testsDone
                      ? <CheckCircle2 className="w-3.5 h-3.5" />
                      : testsActive
                        ? <Loader2 className="w-3.5 h-3.5 animate-spin" />
                        : <div className="w-3.5 h-3.5 rounded-full border-2 border-gray-300" />
                    }
                    <span>Tests</span>
                  </div>
                  <ChevronRight className="w-3 h-3 text-gray-300" />
                  <div
                    className={`flex items-center gap-1 font-medium ${testsDone ? "text-violet-700 cursor-pointer hover:text-violet-900" : "text-gray-400"}`}
                    onClick={testsDone ? onOpenSuites : undefined}
                  >
                    <div className={`w-3.5 h-3.5 rounded-full border-2 ${testsDone ? "border-violet-500" : "border-gray-300"}`} />
                    <span>Run</span>
                    {testsDone && <ChevronRight className="w-3 h-3" />}
                  </div>
                </div>

                {stageError && (
                  <div className="mt-3 flex items-center gap-2 text-red-600 text-xs bg-red-50 px-3 py-2 rounded-lg border border-red-200">
                    <AlertCircle className="w-3.5 h-3.5 flex-shrink-0" /> {stageError}
                  </div>
                )}

                {/* Generating scripts spinner */}
                {(isGeneratingScripts || isRegeneratingScripts) && (
                  <div className="mt-4 flex items-center gap-2 text-xs text-violet-600 bg-violet-50 px-3 py-2.5 rounded-lg border border-violet-200">
                    <Loader2 className="w-3.5 h-3.5 animate-spin flex-shrink-0" />
                    {isRegeneratingScripts ? "Re-generating scripts with your feedback…" : "Generating Playwright scripts (Feature · POM · Tests)…"}
                  </div>
                )}

                {/* Scenario review gate */}
                {(stage === "scenario_review" || isRegeneratingScenarios) && (
                  <ScenarioReviewGate
                    finalOutput={localFinalOutput}
                    onFinalOutputChange={setLocalFinalOutput}
                    onApprove={handleApproveScenarios}
                    onRegenerate={handleRegenScenarios}
                    regenerating={isRegeneratingScenarios}
                  />
                )}

                {/* Script review gate */}
                {(stage === "script_review") && previewData && (
                  <ScriptReviewGate
                    previewData={previewData}
                    finalOutput={localFinalOutput}
                    onApprove={handleApproveScripts}
                    onRegenerate={handleRegenScripts}
                    regenerating={false}
                  />
                )}

                {/* Saved */}
                {stage === "suite_saved" && savedSuiteId && (
                  <SuiteSavedPanel suiteId={savedSuiteId} useCase={savedUseCase} onViewSuites={onOpenSuites} />
                )}
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
  const [activeStep, setActiveStep] = useState(0);

  useEffect(() => {
    if (activeStep >= PIPELINE_STEPS.length - 1) return;
    const t = setTimeout(() => setActiveStep(s => s + 1), 900);
    return () => clearTimeout(t);
  }, [activeStep]);

  return (
    <div className="flex gap-3 items-start">
      <Avatar />
      <div className="bg-white border border-gray-200 rounded-2xl rounded-tl-none px-5 py-4 shadow-sm">
        <div className="flex items-center gap-2.5 text-gray-500 text-sm">
          <Loader2 className="w-4 h-4 text-blue-600 animate-spin flex-shrink-0" />
          <span>Running agentic pipeline… this may take a minute</span>
        </div>
        <div className="mt-3 flex flex-wrap gap-1.5">
          {PIPELINE_STEPS.map((step, i) => (
            <span key={step} className={`text-xs px-2.5 py-0.5 rounded-full transition-all duration-500 ${
              i < activeStep
                ? "bg-green-100 text-green-700 font-medium"
                : i === activeStep
                  ? "bg-blue-100 text-blue-700 font-semibold ring-1 ring-blue-300"
                  : "bg-gray-100 text-gray-400"
            }`}>
              {i < activeStep ? "✓ " : ""}{step}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}

// ─── Main Component ───────────────────────────────────────────────────────────

export default function ChatInterface() {
  const [messages, setMessages]     = useState<Message[]>([]);
  const [input, setInput]           = useState("");
  const [loading, setLoading]       = useState(false);
  const [suitesOpen, setSuitesOpen] = useState(false);
  const bottomRef                   = useRef<HTMLDivElement>(null);
  const textareaRef                 = useRef<HTMLTextAreaElement>(null);

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
        content: `Generated ${data.scenario_count} BDD scenarios for "${data.use_case || q}". Review them below and approve to generate Playwright tests.`,
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
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-blue-600 to-violet-600 flex items-center justify-center shadow-sm">
            <Bot className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="font-semibold text-gray-900 text-base leading-tight">AgenticQAEngine</h1>
            <p className="text-xs text-gray-400">Agentic Pipeline · Graph RAG · BDD Gherkin · Playwright Automation</p>
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
            <div className="text-center pt-10 pb-4">
              <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-600 to-violet-600 flex items-center justify-center mx-auto mb-4 shadow-lg">
                <Bot className="w-8 h-8 text-white" />
              </div>
              <h2 className="text-xl font-semibold text-gray-800 mb-1">AgenticQAEngine</h2>
              <p className="text-sm text-gray-500 max-w-md mx-auto mb-8">
                Describe a feature to generate BDD scenarios. Two human review gates let you inspect, edit, and approve before anything is saved or run.
              </p>

              {/* 5-step workflow diagram */}
              <div className="flex items-start justify-center gap-1.5 mb-8 px-2 flex-wrap">
                {/* Step 1 */}
                <div className="flex flex-col items-center gap-1.5 w-24">
                  <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 font-bold text-sm shadow-sm">①</div>
                  <span className="text-xs font-semibold text-gray-700 text-center leading-tight">Generate Scenarios</span>
                  <span className="text-xs text-gray-400 text-center leading-tight">Gherkin via RAG</span>
                </div>
                <div className="mt-3 text-gray-300"><ChevronRight className="w-4 h-4" /></div>
                {/* Step 2 — Gate 1 */}
                <div className="flex flex-col items-center gap-1.5 w-24">
                  <div className="w-10 h-10 rounded-full bg-amber-100 flex items-center justify-center text-amber-600 font-bold text-sm shadow-sm ring-2 ring-amber-300 ring-offset-1">②</div>
                  <span className="text-xs font-semibold text-gray-700 text-center leading-tight">Review Scenarios</span>
                  <span className="text-xs text-amber-500 text-center leading-tight font-medium">Human Gate 1</span>
                </div>
                <div className="mt-3 text-gray-300"><ChevronRight className="w-4 h-4" /></div>
                {/* Step 3 */}
                <div className="flex flex-col items-center gap-1.5 w-24">
                  <div className="w-10 h-10 rounded-full bg-violet-100 flex items-center justify-center text-violet-600 font-bold text-sm shadow-sm">③</div>
                  <span className="text-xs font-semibold text-gray-700 text-center leading-tight">Generate Scripts</span>
                  <span className="text-xs text-gray-400 text-center leading-tight">Playwright POM</span>
                </div>
                <div className="mt-3 text-gray-300"><ChevronRight className="w-4 h-4" /></div>
                {/* Step 4 — Gate 2 */}
                <div className="flex flex-col items-center gap-1.5 w-24">
                  <div className="w-10 h-10 rounded-full bg-violet-100 flex items-center justify-center text-violet-600 font-bold text-sm shadow-sm ring-2 ring-violet-400 ring-offset-1">④</div>
                  <span className="text-xs font-semibold text-gray-700 text-center leading-tight">Review Scripts</span>
                  <span className="text-xs text-violet-500 text-center leading-tight font-medium">Human Gate 2</span>
                </div>
                <div className="mt-3 text-gray-300"><ChevronRight className="w-4 h-4" /></div>
                {/* Step 5 */}
                <div className="flex flex-col items-center gap-1.5 w-24">
                  <div className="w-10 h-10 rounded-full bg-green-100 flex items-center justify-center text-green-600 font-bold text-sm shadow-sm">⑤</div>
                  <span className="text-xs font-semibold text-gray-700 text-center leading-tight">Run Tests</span>
                  <span className="text-xs text-gray-400 text-center leading-tight">Saved Test Suites</span>
                </div>
              </div>
              {/* Gate legend */}
              <div className="flex items-center justify-center gap-6 mb-6 text-xs text-gray-500">
                <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-amber-400 inline-block" /> Review &amp; approve / re-generate / upload JSON</span>
                <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-violet-400 inline-block" /> Edit scripts inline / re-generate / save</span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 max-w-xl mx-auto">
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
                onOpenSuites={() => setSuitesOpen(true)}
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
