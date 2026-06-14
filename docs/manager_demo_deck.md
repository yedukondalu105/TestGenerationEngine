---
marp: true
theme: default
paginate: true
style: |
  section {
    font-family: 'Segoe UI', Arial, sans-serif;
    background: #ffffff;
    color: #1e293b;
    padding: 48px 64px;
    font-size: 1rem;
  }
  section.title {
    background: linear-gradient(135deg, #0f3460 0%, #1a1a3e 55%, #0d7377 100%);
    color: #ffffff;
    text-align: center;
    justify-content: center;
  }
  section.title h1 { font-size: 2.6rem; margin-bottom: 0.2em; letter-spacing: -1px; }
  section.title h2 { font-size: 1.15rem; opacity: 0.82; font-weight: 400; margin-top: 0; }
  section.title p  { font-size: 0.95rem; opacity: 0.70; margin-top: 2em; }
  section.divider {
    background: linear-gradient(135deg, #0f3460, #0d7377);
    color: #ffffff;
    justify-content: center;
    text-align: center;
  }
  section.divider h1 { color: #fff; border: none; font-size: 2rem; }
  section.divider p  { color: rgba(255,255,255,0.75); font-size: 1rem; }
  section.green {
    background: linear-gradient(135deg, #064e3b, #065f46);
    color: #ffffff;
    justify-content: center;
    text-align: center;
  }
  section.green h1 { color: #6ee7b7; border: none; font-size: 2rem; }
  section.green p  { color: rgba(255,255,255,0.80); font-size: 1rem; }
  h1 { color: #0f3460; font-size: 1.75rem; border-bottom: 3px solid #0d7377; padding-bottom: 8px; margin-bottom: 0.6em; }
  h2 { color: #0f3460; font-size: 1.25rem; margin-top: 0.5em; }
  h3 { color: #0d7377; font-size: 1.05rem; margin-bottom: 0.2em; }
  ul { margin-top: 0.3em; }
  li { margin-bottom: 0.35em; line-height: 1.5; }
  strong { color: #0f3460; }
  em { color: #0d7377; font-style: normal; font-weight: 600; }
  table { width: 100%; border-collapse: collapse; font-size: 0.9rem; margin-top: 0.5em; }
  th { background: #0f3460; color: #fff; padding: 9px 14px; text-align: left; }
  td { padding: 8px 14px; border-bottom: 1px solid #e2e8f0; }
  tr:nth-child(even) td { background: #f8fafc; }
  .big  { font-size: 2.8rem; font-weight: 700; color: #0d7377; display: block; }
  .label { font-size: 0.85rem; color: #64748b; display: block; }
  .box { background: #f0f9ff; border-left: 4px solid #0d7377; padding: 10px 16px; margin: 8px 0; border-radius: 0 6px 6px 0; }
  .highlight { background: #ecfdf5; border-left: 4px solid #059669; padding: 10px 16px; margin: 8px 0; border-radius: 0 6px 6px 0; }
  .warn { background: #fffbeb; border-left: 4px solid #d97706; padding: 10px 16px; margin: 8px 0; border-radius: 0 6px 6px 0; }
  footer { font-size: 0.7rem; color: #94a3b8; }
---

<!-- _class: title -->

# AgenticQAEngine
## AI-Powered Quality Assurance — Automated from Day One

**Manager Overview · June 2026**

---

<!--
SCRIPT — Slide 1 (Title)

"Good [morning/afternoon]. Today I want to walk you through something we've built
that changes how we approach software quality testing — completely. It's called
AgenticQAEngine, and by the end of this demo I think you'll see why it matters
for the team's speed and confidence when we ship new features."
-->

# The Problem We're Solving

> *Every time we build a new software feature, someone has to manually write tests to make sure it works.*

### What that looks like today:
- A QA engineer reads through requirement documents — takes **30–60 minutes** just to understand scope
- Then writes test scripts by hand — another **2–4 hours per feature**
- If requirements change, tests need to be rewritten from scratch
- Results depend heavily on **individual knowledge** — easy to miss edge cases

<br>

<div class="warn">
  <strong>Bottom line:</strong> QA is a bottleneck. It slows down releases and still misses bugs.
</div>

---

<!--
SCRIPT — Slide 2 (The Problem)

"Before I show you the solution, let me set the context. Every time the team builds
a new feature — say, a new user login flow or a new employee onboarding screen —
a QA engineer has to manually figure out all the ways to test it.

That means reading documents, understanding business rules, and then writing dozens
of test cases by hand. It takes hours, it's repetitive, and it still depends on
one person's knowledge. If they miss an edge case, it becomes a bug in production.

This is the bottleneck we set out to fix."
-->

# Our Solution — AgenticQAEngine

*Describe a feature in plain English → AI handles the rest*

<br>

| Step | What Happens | Who Does It |
|------|-------------|-------------|
| 1. Describe | Type what the feature should do | **You (1 sentence)** |
| 2. Generate | AI reads our requirements and writes test scenarios | **AI (2 min)** |
| 3. Review | QA engineer checks and approves the scenarios | **QA (5 min)** |
| 4. Build Tests | AI writes the actual test code | **AI (1 min)** |
| 5. Run | Tests execute automatically against the application | **System (5 min)** |
| 6. Fix | AI analyses failures and suggests fixes | **AI + QA (5 min)** |

<br>

<div class="highlight">
  <strong>Total time:</strong> What used to take a full day now takes under 20 minutes.
</div>

---

<!--
SCRIPT — Slide 3 (Our Solution)

"Here's what AgenticQAEngine does. Instead of a QA engineer spending hours writing
tests manually, they simply type what a feature does in one sentence.

The AI takes over from there. It reads our existing requirement documents, generates
a comprehensive set of test scenarios, and writes the actual test code — all
automatically.

The QA engineer is still in the loop at every step. They review what the AI produced,
make changes if needed, and give the green light before anything runs.

What used to take a full day now takes under 20 minutes — end to end."
-->

# How the AI Knows What to Test

*It doesn't guess — it reads our actual requirements*

<br>

### Knowledge Sources the AI Uses:
<div class="box">
  <strong>Confluence</strong> — Our internal requirement pages and test plans are automatically loaded into the system
</div>
<div class="box">
  <strong>Neo4j Knowledge Graph</strong> — 171 structured requirement nodes across all OrangeHRM modules (Login, Dashboard, Recruitment, Employee Management, Admin)
</div>
<div class="box">
  <strong>Domain Guard</strong> — The AI only works within our defined scope. Off-topic requests are blocked automatically with a clear message
</div>

<br>

> The AI never makes up requirements. Every test scenario it generates is **grounded in our actual documentation**.

---

<!--
SCRIPT — Slide 4 (How the AI Knows)

"One thing managers often ask is — how does the AI know what's correct? Is it just
guessing?

The answer is no. We've connected it to our actual Confluence requirement pages and
built a structured knowledge database with 171 requirement nodes. The AI reads
these sources before generating anything.

We also built a guardrail: if someone asks it to generate tests for something outside
our defined scope — for example, a trading system — it refuses with a clear message.
It only works with what we've told it about."
-->

# Human Control at Every Step

*AI suggests — humans decide*

<br>

```
  [AI Generates Scenarios]
          |
          v
  Gate 1 - QA Reviews Scenarios
  Approve / Give Feedback / Upload Own Version
          |
          v
  [AI Writes Test Code]
          |
          v
  Gate 2 - QA Reviews Code
  Edit Directly / Request Changes / Approve & Save
          |
          v
  [Tests Run Against Application]
          |
          v
  Gate 3 - QA Reviews Failures
  AI Explains Root Cause / One-Click Fix / Mark as Bug
```

<br>

<div class="highlight">
  <strong>Nothing is saved or run without explicit human approval.</strong>
</div>

---

<!--
SCRIPT — Slide 5 (Human Control)

"I want to address something that often comes up: does this mean the AI just runs
loose and generates whatever it wants?

Absolutely not. There are three human approval gates built into the workflow.

First, the QA engineer reviews every scenario the AI generates before any code is
written. They can approve, reject, or give feedback — and the AI re-generates.

Second, once the AI writes the test code, the engineer reviews and edits it directly
before it's saved.

Third, after tests run, if anything fails, the AI analyses the failure and suggests
a fix — but the engineer decides whether to apply it.

Nothing is saved, nothing runs, nothing is changed without a human saying yes."
-->

# What Happens When Tests Fail

*The AI doesn't just report failures — it explains and fixes them*

<br>

### AI Failure Analysis (Gate 3):

| Failure Type | What It Means | AI Action |
|-------------|--------------|-----------|
| **App Bug** | Feature is broken in the application | Flags it — no code change |
| **Locator Drift** | A button or field was renamed in the UI | Proposes updated selector |
| **Wrong Assertion** | AI wrote an incorrect expected value | Proposes corrected check |
| **Timing Issue** | Page loaded too slowly during the test | Proposes a wait adjustment |

<br>

- Engineer clicks **Apply Fix** → code is patched instantly
- Then clicks **Re-run This Test** → confirms the fix worked
- If still failing → AI re-analyses automatically with a new suggestion

---

<!--
SCRIPT — Slide 6 (What Happens When Tests Fail)

"Here's where it gets really powerful. When tests fail — and in any real application,
some will fail — the AI doesn't just say 'test failed, good luck.'

It reads the actual error, looks at a screenshot of what the browser showed during
the test, and classifies the root cause. Is it a real bug in the application? Is it
a UI element that got renamed? Is it a timing issue?

For anything fixable in the test code, it proposes an exact code change — old line
vs new line. The engineer reviews it, clicks Apply Fix, and then re-runs just that
one test to confirm it's resolved.

This alone saves hours of debugging time."
-->

<!-- _class: divider -->

# Live Demo
## Let's see it in action

*Feature: User Login & Authentication — OrangeHRM*

---

<!--
SCRIPT — Slide 7 (Demo Divider)

"Let me show you exactly how this works with a real example. We'll generate test
cases for the user login and authentication feature in OrangeHRM.

I'll type one sentence, and you'll see the AI produce a full test suite in under
two minutes."

[SWITCH TO LIVE DEMO — steps below]

Demo flow:
1. Open http://localhost:3000
2. Type: "Generate test cases for user login and authentication"
3. Watch the 6-step pipeline animate
4. Show the generated Gherkin scenarios — point out variety: valid login, wrong password, empty fields, session expiry
5. Click "Re-generate" with feedback: "add more edge cases for locked accounts"
6. Show the faster HITL re-generation (~20s)
7. Approve scenarios → show test code generation
8. Open Saved Test Suites → show a pre-run suite with results
9. Click Triage Failures → show AI root cause + Apply Fix
-->

# Demo Recap — What You Just Saw

<br>

<div class="box">
  <strong>Step 1 — One sentence in:</strong> "Generate test cases for user login and authentication"
</div>
<div class="box">
  <strong>Step 2 — AI output in ~2 min:</strong> 26 test scenarios covering valid login, invalid password, empty fields, locked accounts, session expiry
</div>
<div class="box">
  <strong>Step 3 — Human feedback:</strong> "Add more edge cases for locked accounts" → AI regenerated in ~20 seconds (resumes from where it left off, skips repeat work)
</div>
<div class="box">
  <strong>Step 4 — Test code generated:</strong> Full Playwright test suite, ready to run
</div>
<div class="box">
  <strong>Step 5 — Failure triage:</strong> AI identified a locator change, proposed a fix, test passed on re-run
</div>

---

<!--
SCRIPT — Slide 8 (Demo Recap)

"So to summarise what we just saw:

With one sentence, the system produced 26 test scenarios — all grounded in our
actual requirements. When I gave feedback asking for more edge cases, it didn't
start over — it resumed from where it had paused and came back with updated
scenarios in about 20 seconds.

The generated test code ran against the application, one test failed due to a
UI change, the AI diagnosed it, proposed a one-line fix, and after applying it
the test passed.

That entire workflow — from typing the feature description to a passing test suite —
took under 15 minutes."
-->

# Impact & Time Savings

<br>

<table>
  <tr>
    <th>Activity</th>
    <th>Before (Manual)</th>
    <th>After (AgenticQAEngine)</th>
    <th>Saved</th>
  </tr>
  <tr>
    <td>Understanding requirements</td>
    <td>30–60 min</td>
    <td>0 min (AI reads docs)</td>
    <td><strong>~45 min</strong></td>
  </tr>
  <tr>
    <td>Writing test scenarios</td>
    <td>2–3 hours</td>
    <td>2 min (AI generates)</td>
    <td><strong>~2.5 hrs</strong></td>
  </tr>
  <tr>
    <td>Writing test code</td>
    <td>3–5 hours</td>
    <td>1 min (AI codes)</td>
    <td><strong>~4 hrs</strong></td>
  </tr>
  <tr>
    <td>Debugging failures</td>
    <td>1–2 hours</td>
    <td>5 min (AI diagnoses)</td>
    <td><strong>~1.5 hrs</strong></td>
  </tr>
</table>

<br>

<div class="highlight">
  <strong>Total per feature:</strong> 6–10 hours → under 20 minutes &nbsp;|&nbsp; Consistency guaranteed &nbsp;|&nbsp; Zero knowledge dependency
</div>

---

<!--
SCRIPT — Slide 9 (Impact)

"Here's what this means in numbers.

For every feature we test, we save roughly 6 to 10 hours of manual QA work.
That's not an estimate — that's based on our current team's actual time spent.

Beyond speed, there's a consistency benefit. A manual QA engineer might miss
edge cases on a Friday afternoon. The AI doesn't. It always checks the same
categories — valid paths, error handling, edge cases, permissions.

And there's no longer a single point of failure where only one person knows
how to test a specific module."
-->

# What We've Built So Far

*Current system covers the OrangeHRM HR platform*

<br>

### Modules with full test coverage:
- **Authentication & Authorization** — login, logout, session, password policies
- **Admin Management** — user creation, role assignment, permissions
- **Recruitment** — candidate pipeline, job postings, interview workflow
- **Employee Management (PIM)** — employee records, personal info, reporting
- **Dashboard** — navigation, access control, role-based views

<br>

### Test Suites Generated & Saved:
- Multiple suites already running in CI
- Failure artifacts (screenshots + DOM snapshots) captured automatically
- AI triage available on any failing test with one click

---

<!--
SCRIPT — Slide 10 (What We've Built)

"In terms of where we are today — we've built out full test coverage for five
modules of our OrangeHRM HR system. Each module has scenarios, test code, and
the ability to run and triage failures.

We have multiple saved test suites that can be re-run at any time — before a
release, after a configuration change, or whenever the team wants confidence
that the system is working correctly."
-->

# What's Next — Roadmap

<br>

| Priority | Initiative | Benefit |
|----------|-----------|---------|
| Short-term | **Expand to more modules** — Payroll, Leave, Time & Attendance | Wider safety net |
| Short-term | **CI/CD integration** — run suites automatically on every code push | Zero manual trigger needed |
| Medium-term | **Cross-domain RAG** — connect to other internal systems beyond OrangeHRM | Reuse across projects |
| Medium-term | **Parallel test execution** — run all test suites simultaneously | 5× faster results |
| Long-term | **Video capture** — record browser session during test runs for debugging | Visual evidence per failure |
| Long-term | **Auto-update tests on requirement change** — AI detects doc changes and flags outdated tests | Always in sync |

---

<!--
SCRIPT — Slide 11 (Roadmap)

"Looking ahead, the immediate next step is expanding coverage to the remaining
OrangeHRM modules — Payroll, Leave, Time & Attendance.

The bigger opportunity is CI/CD integration — connecting the system so tests
run automatically every time a developer pushes code. That turns this from a
QA tool into a continuous safety net.

Longer term, the same architecture can be reused for any other system we bring in —
not just OrangeHRM. The AI pipeline, the human-in-the-loop gates, the test
execution engine — all of that carries over."
-->

<!-- _class: green -->

# Summary

**One sentence in → production-ready tests out**

- AI reads our requirements → generates scenarios → writes code → runs tests → diagnoses failures
- QA engineer stays in control at every gate — approves, edits, or rejects
- 6–10 hours of manual work reduced to under 20 minutes per feature
- No knowledge dependency — any team member can trigger a test suite
- Built on OrangeHRM today — architecture ready to scale

---

<!--
SCRIPT — Slide 12 (Summary)

"To wrap up:

AgenticQAEngine takes what used to be one of the most time-consuming and
knowledge-dependent parts of software delivery — writing and maintaining QA tests —
and automates it end to end.

The AI does the heavy lifting. The human stays in control at every step.
And the result is faster releases, better coverage, and a team that spends its
time on decisions rather than on writing boilerplate test code.

I'm happy to answer any questions, or we can do a deeper dive into any specific
part of the system."
-->

# Thank You — Q&A

<br>

### Key Takeaways:

<div class="box"><strong>Speed:</strong> 6–10 hours of QA work → under 20 minutes per feature</div>
<div class="box"><strong>Quality:</strong> AI covers all edge cases, every time — no Friday-afternoon misses</div>
<div class="box"><strong>Control:</strong> 3 human approval gates — nothing runs without sign-off</div>
<div class="box"><strong>Scale:</strong> Same system, any module, any future platform</div>

<br>

> *"We didn't remove QA engineers from the loop — we removed the repetitive parts of their job."*

---

<!--
SCRIPT — Slide 13 (Q&A)

[Wait for questions. Common ones and suggested answers:]

Q: "What if the AI generates wrong tests?"
A: "That's exactly why the human review gate exists. The QA engineer sees every scenario
before any code is written. They can reject it, give feedback, or upload their own version."

Q: "Does this replace the QA team?"
A: "No. It removes the repetitive, time-consuming parts — reading docs, writing boilerplate
code, debugging obvious failures. The QA engineer focuses on edge cases the AI might miss,
business logic decisions, and interpreting what failures mean for the product."

Q: "What systems can this work with?"
A: "Right now it's connected to OrangeHRM through our Confluence and Neo4j knowledge base.
The architecture is built to be extended — connecting a new system means loading its
requirements into the knowledge graph."

Q: "How accurate is the AI?"
A: "The AI has a built-in review step — it grades its own output and re-runs if quality
isn't met. In our testing, the human reviewer typically approves with minor feedback
on the first or second generation."
-->
