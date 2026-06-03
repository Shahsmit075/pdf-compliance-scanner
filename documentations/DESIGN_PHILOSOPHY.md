# 🧭 Design Philosophy
## AI-Powered PDF Compliance Scanner

> **Focus:** The *why* behind architectural decisions. For *what it does*, see `PRD.md`. For *how it's built*, see `CODE_DOCUMENTATION.md`.

---

## 1. Core Philosophy: Determinism First, AI Second

### The Problem with "AI-Only" Systems

A compliance scanner that relies solely on AI is dangerous:
- AI can hallucinate, producing false negatives on critical PII
- AI can fail at runtime (rate limits, network errors)
- AI is a black box — hard to audit for regulatory compliance
- AI adds latency that compounds with document size

### Our Solution: Regex as the Foundation

Every detection node that uses AI **always runs regex first**. The regex engine:
- ✅ Never fails (no network, no API key needed)
- ✅ Is 100% deterministic — auditable, reproducible
- ✅ Has explicitly defined confidence per pattern
- ✅ Produces results in milliseconds

AI is layered *on top* — as an enhancement, not a replacement. If AI fails, the user still gets a complete compliance report from regex alone.

> **Principle:** AI failure is a degradation, not a failure. The system never returns zero findings because of a network error.

---

## 2. Typed State as the Single Source of Truth

### Why TypedDict

LangGraph works with any mutable dict, but we chose to define `PipelineState` as a strict `TypedDict`. This forces:
- **Explicit contracts** between nodes — every output key is documented
- **IDE type-checking** — mistakes caught before runtime
- **Self-documenting code** — the state schema is the architecture diagram

### Why Partial Updates (not full state replacement)

Each node returns only the keys it modifies. This matches LangGraph's merging model and prevents accidental data loss from one node overwriting another's output.

---

## 3. Fan-Out Parallelism for Speed

After ingestion, the 4 compliance nodes run in **parallel**. This is a deliberate design choice:

- **Sequential alternative:** 4 nodes × 3s per AI call = 12s per page
- **Parallel execution:** All 4 nodes run simultaneously = ~3s per page

LangGraph's DAG model makes this possible without threading code — just multiple edges from one node to multiple nodes.

The aggregator node then waits for all 4 upstream nodes to complete before merging. The `processing_complete: True` flag signals the report builder.

---

## 4. Risk Scoring: The MAX Rule

Risk is always computed as `MAX(severity-based risk, count-based risk)`. This prevents two failure modes:

**Failure Mode 1 — Under-reporting by severity:**
A page with 15 "low" severity flags should not be labeled "low" overall. The count-based scoring catches this (≥10 flags → critical).

**Failure Mode 2 — Over-reporting by count:**
A page with 1 "critical" credential is critical regardless of how many other low-level issues exist.

> **Invariant:** Risk always resolves to one of `{low, medium, high, critical}`. The value `"unknown"` is explicitly mapped to `"low"` by `_normalize_risk()`. No consumer needs to handle unknown states.

---

## 5. Privacy by Design

Compliance scanners handle the most sensitive data imaginable — credentials, medical IDs, financial records. The system is designed to **never expose what it detects**:

### Credential Masking at Detection Time
Secret values (API keys, passwords) are masked **immediately in the detection node** — before they enter `PipelineState`, before they are stored in SQLite, before they appear in any report. The actual key value never travels through the system.

```python
# In confidentiality.py — masking happens at flag creation time
if len(value) > 12:
    masked = value[:6] + "…" + value[-4:]
```

### Abuse Content Redaction
Abusive content (threats, slurs, hate speech) is stored as `[REDACTED — abuse content]` in the flag. No one accessing the SQLite database or PDF report can extract the original content.

### Temp File Cleanup
The uploaded PDF is written to a temp file, scanned, and then **deleted unconditionally** in a `finally` block. The file never persists on the server after the scan.

---

## 6. Free-First AI Strategy

The default AI provider is Groq — which offers 14,400 free API requests per day. This was a deliberate choice to make the tool **accessible without financial barrier**:

- A 10-page document uses ~30 AI calls (3 AI nodes × 10 pages)
- The free tier supports ~480 document scans per day
- For teams exceeding this, Gemini Flash (1,500 req/day free) is the next option
- For air-gapped / zero-internet deployments, Ollama runs 100% locally

The `AI_PROVIDER` environment variable makes switching providers a one-line config change — no code changes needed.

---

## 7. Configuration Over Code

Compliance requirements change. A healthcare org needs HIPAA rules; a fintech needs PCI-DSS; a government body needs ITAR. Rather than hardcoding rules, the system externalizes them:

- `config/rules.json` is the single source of truth for detection behavior
- **The UI edits this file live** — no restart required
- `custom_keywords` allow teams to add their own detection terms (e.g., project codenames, internal classification phrases)
- Every rule check respects its `enabled: false` flag — turning off a category costs zero performance

> **Principle:** The tool should adapt to compliance requirements, not the other way around.

---

## 8. Report as a Compliance Artifact

The PDF report is not a debug log — it's a **formal compliance artifact** that needs to stand on its own in an audit:

- **Executive Summary** with metrics for management
- **Risk Heatmap** for triage — which pages need immediate attention?
- **Detailed Findings** with real confidence percentages and detection method (Regex vs AI) — auditors need to know *why* something was flagged
- **Masked values** — the report can be shared without exposing the underlying sensitive data
- **Scan ID** — every report is uniquely identified and stored in SQLite for recall

ReportLab was chosen over markdown-to-PDF conversion because it gives pixel-precise control over the table layout, color coding, and enterprise appearance that an audit-grade document requires.

---

## 9. Fail-Graceful, Not Fail-Silent

Every node that can fail (AI calls, file I/O) has explicit error handling:
- Errors are collected into `state["errors"]` — not silently swallowed
- The UI shows an "⚠️ Scan Warnings" expander for non-fatal errors
- The scan is marked as `completed` even if some AI nodes failed — because regex results are still valid

The alternative — failing the entire scan when one AI call rate-limits — would make the tool unreliable in exactly the conditions (high load) when compliance scanning matters most.

---

## 10. Testing Philosophy: Mock AI, Test Logic

AI calls are expensive, slow, and non-deterministic. Our test suite **never makes real AI calls**:

- `conftest.py` provides `mock_ai_pii_response` and `mock_ai_clean_response` fixtures
- All tests use `unittest.mock.patch` to replace `call_ai`
- The encoding and aggregator nodes don't use AI at all — their tests run in milliseconds

This means the test suite is:
- ✅ Fast (< 5 seconds total)
- ✅ Reproducible (same mock → same output always)
- ✅ Free (no API credits consumed)
- ✅ CI-safe (no GROQ_API_KEY needed for unit tests)

---

*"A compliance tool that itself violates privacy, leaks secrets, or silently fails on errors is not a compliance tool — it's a liability."*

*Last Updated: May 2026*
