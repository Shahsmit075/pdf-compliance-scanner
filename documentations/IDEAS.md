# 🧠 PROJECT BRAINSTORM & DECISIONS
> **Purpose:** Single source of truth for all ideas, changes, summarisations, and effort-estimations. Simplified, keyworded, and easily readable.

---

## 🏗️ 1. ARCHITECTURE & DECISIONS
- **Architecture Type:** Local Web App (Streamlit)
- **Database:** Local SQLite (`compliance.db`) — High security, no cloud liability.
- **Processing:** Local Extraction (PyMuPDF) + API-based LLM Analysis.
- **Observability Stack:** **LangSmith** 
  - *Decision:* Approved. Provides out-of-the-box LLM tracing, latency tracking, and token usage without tracking sensitive PDF data.

---

## ⏱️ 2. EFFORT ESTIMATIONS (New Features)

### 💡 Idea 1: Native Async Execution (UI Streaming)
**Concept:** Use `astream_events` to stream node completion status to the UI dynamically instead of a static loading spinner.
- **Effort:** **MEDIUM**
- **Changes Required:** 
  1. Rewrite `pipeline/graph.py` to return an async generator.
  2. Update `app/pages/01_upload.py` to use `st.empty()` or `st.status()` to stream real-time updates (e.g. "Page 1: PII check complete...").
- **Impact:** **HIGH**. Eliminates the "frozen UI" feel. Shows mastery of concurrent Python and LangGraph asynchronous capabilities.

### 💡 Idea 2: Dynamic UI API Key Configuration
**Concept:** Support OpenAI, Groq, and Gemini. Allow users to enter API keys directly in the Streamlit UI rather than hardcoding in `.env`.
- **Effort:** **LOW-MEDIUM**
- **Changes Required:**
  1. Add a sidebar or settings tab in Streamlit with `st.text_input(..., type="password")`.
  2. Save keys securely in `st.session_state`.
  3. Refactor `config/ai_provider.py` to read keys from `session_state` rather than `os.getenv`.
- **Impact:** **HIGH**. Extremely user-friendly for professors/reviewers testing your capstone.

### 💡 Idea 3: Multi-LLM Comparative Scan (The "Arena" Mode)
**Concept:** Run the scan using all 3 LLMs simultaneously. Compare their outputs, token usage, and latency metrics in LangSmith.
- **Effort:** **HIGH**
- **Changes Required:**
  1. Modify LangGraph to branch out and run inference 3 times (once per LLM).
  2. Redesign the Reports UI to show a "Side-by-Side" comparison table (e.g. "Groq found X, Gemini found Y").
  3. Tag runs in LangSmith (`tags=["groq", "gemini"]`) to easily compare latency and token usage in the observability dashboard.
- **Impact:** **VERY HIGH (Capstone Winner)**. This shifts the project from a standard scanner to a *GenAI Evaluation Platform*. It proves you know how to benchmark, evaluate, and monitor different models against each other.

---

## 📝 3. NEXT STEPS / SUMMARY
*To be updated as we build...*
- [x] Setup LangSmith Environment Variables.
- [x] Implement UI API Key Input.
- [x] Transition to Async Streaming UI.
- [ ] Build Multi-LLM Comparison Pipeline.
