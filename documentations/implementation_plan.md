# Implementation Plan: PDF Compliance Scanner Upgrades

**STATUS: COMPLETED**

This document outlines the approach for implementing the five requested features.

## Proposed Changes

---
### 1. Dynamic UI API Key Configuration
**Concept:** Allow users to set their API keys directly via the Streamlit UI, bypassing the need for a `.env` file.
**Implementation:**
- Add an `st.sidebar` section in `app/main.py` (or a dedicated settings modal) for users to input their Groq, Gemini, and Anthropic keys using `st.text_input(type="password")`.
- When a user inputs a key, it will instantly update `os.environ["GROQ_API_KEY"]` (and others). Since `config/ai_provider.py` already checks `os.getenv()`, this completely avoids massive refactoring while achieving the exact goal.

#### [MODIFY] [main.py](file:///Users/as-mac-1320/Downloads/genai-capstone/pdf-compliance-scanner/app/main.py)
Add sidebar inputs and update `os.environ` dynamically.

---
### 2. Native UI Streaming (Iterative Execution)
**Concept:** Prevent the UI from "freezing" with a single loading bar during a long scan. Instead, stream real-time updates (e.g., "PII check finished... Confidentiality check finished...").
**Implementation:**
- LangGraph supports `.stream()` execution out-of-the-box. Instead of rewriting the entire pipeline to `async` (which requires massive rewrites of all `call_ai` logic), we can simply change `run_pipeline` to act as a generator using `pipeline.stream()`.
- It will `yield` the node name that just finished (e.g., `pii_check`, `abuse_check`).
- In `app/pages/01_upload.py`, we loop over this generator and update a beautiful `st.status()` container in real-time.

#### [MODIFY] [graph.py](file:///Users/as-mac-1320/Downloads/genai-capstone/pdf-compliance-scanner/pipeline/graph.py)
Change `run_pipeline` to `run_pipeline_stream` yielding iterative state updates.
#### [MODIFY] [01_upload.py](file:///Users/as-mac-1320/Downloads/genai-capstone/pdf-compliance-scanner/app/pages/01_upload.py)
Consume the generator and update the UI dynamically.

---
### 3. Global Analytics Dashboard
**Concept:** Add charts to the Reports page to visualize historical scan data.
**Implementation:**
- In `app/pages/03_reports.py`, aggregate the data from `get_all_scans()`.
- Use `st.bar_chart` and `st.line_chart` to show "Scans Over Time" and "Risk Distribution".

#### [MODIFY] [03_reports.py](file:///Users/as-mac-1320/Downloads/genai-capstone/pdf-compliance-scanner/app/pages/03_reports.py)
Add charting logic above the historical tables.

---
### 4. CSV Data Export
**Concept:** Allow users to download the raw redaction table as a CSV file.
**Implementation:**
- In `app/pages/01_upload.py`, convert the filtered `redaction_records` dict to a Pandas DataFrame.
- Add a `st.download_button("Download CSV", data=df.to_csv())` next to the PDF download button.

#### [MODIFY] [01_upload.py](file:///Users/as-mac-1320/Downloads/genai-capstone/pdf-compliance-scanner/app/pages/01_upload.py)
Add the CSV download button logic.

---
### 5. Rule Tester / Sandbox
**Concept:** Allow users to test custom regex or keywords before saving them.
**Implementation:**
- In `app/pages/02_rules.py`, add a "Test Environment" expander.
- Include a text input for test strings and instantly evaluate them against the current custom keywords/regex, returning a success/fail UI alert.

#### [MODIFY] [02_rules.py](file:///Users/as-mac-1320/Downloads/genai-capstone/pdf-compliance-scanner/app/pages/02_rules.py)
Add the sandbox logic.

## Verification Plan

### Manual Verification
- **API Keys:** Type a fake API key in the UI, verify that the scan fails citing the invalid key (proving the UI overrides `.env`).
- **Streaming:** Run a scan on the demo PDF and observe the UI updating step-by-step (`ingest` -> `pii_check` -> `aggregate`, etc.).
- **Analytics:** Navigate to the Reports tab and verify the bar charts render correctly based on past SQLite scans.
- **CSV:** Click the "Download CSV" button and open the file to verify redaction columns match the UI.
- **Rule Sandbox:** Type a custom keyword (e.g. "Project Titan"), type it into the test box, and verify it says "Match Found!".
