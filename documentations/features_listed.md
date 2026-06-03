# 📋 Feature Specification — AI-Powered PDF Compliance Scanner
> **Purpose:** A complete, technically precise blueprint to rebuild this app from scratch in any language/framework.  
> **Format:** Each feature is written as an implementable prompt.

---

## SECTION 1: Core Architecture

**F-ARCH-01:** Implement a Client-Server Architecture where a Python Streamlit frontend (port 8501) serves all UI, and a LangGraph-based pipeline processes PDFs in the same Python process synchronously (no separate backend service).

**F-ARCH-02:** Implement a Directed Acyclic Graph (DAG) pipeline using LangGraph's `StateGraph`. The graph must: (a) accept a `TypedDict` as shared state, (b) support parallel fan-out from a single ingestion node to 4 compliance check nodes, (c) merge results in an aggregation node, (d) then generate a report, and (e) terminate.

**F-ARCH-03:** Implement a typed shared state schema (`PipelineState` TypedDict) with the following required keys: `pdf_path`, `pdf_name`, `upload_id`, `total_pages`, `pages_text`, `pii_results`, `confidential_results`, `encoding_results`, `abuse_results`, `page_results`, `summary`, `compliance_rules`, `report_path`, `processing_complete`, `errors`. Every pipeline node receives the full state and returns a partial dict of only the keys it modifies.

**F-ARCH-04:** Implement `.env`-based secret management using `python-dotenv`. The app must read `GROQ_API_KEY`, `AI_PROVIDER`, `GROQ_MODEL`, `MAX_FILE_SIZE_MB`, `MAX_PAGES`, and `DEBUG` from environment variables. Provide an `.env.example` template. The `.env` file must be gitignored.

---

## SECTION 2: User Interface (UI)

**F-UI-01: Home Page** — Implement a Streamlit home page (`app/main.py`) that: (a) sets `page_title="PDF Compliance Scanner"`, `layout="wide"`, (b) renders a gradient header banner using `st.markdown(unsafe_allow_html=True)` with inline CSS, (c) shows 4 feature cards in a 4-column layout using `st.info/warning/success/error` for PII/Confidentiality/Encoding/Abuse respectively, (d) shows a sidebar with branding and tech stack listing.

**F-UI-02: Upload & Scan Page** — Implement a Streamlit page (`app/pages/01_upload.py`) with: (a) `st.file_uploader(type=["pdf"])` accepting PDFs up to 50MB, (b) 3 metadata metric cards showing filename, file size in KB, and file type, (c) a "Run Compliance Scan" primary button, (d) a `st.progress()` bar updating through stages: 10% (extracting text) → 20% (running AI checks) → 90% (saving results) → 100% (complete), (e) a timer showing elapsed seconds, (f) a unique 8-char scan ID (uuid4[:8]) displayed on completion.

**F-UI-03: Results Display** — After a scan completes and results are stored in `st.session_state`, render: (a) 5 metric cards: Pages Scanned, Total Flags, Highest Risk, PII Issues, Confidential Issues, (b) 4 issue-type breakdown cards (PII, Confidential, Encoding, Abuse flag counts), (c) a page-by-page heatmap table with columns: Page, PII, Confidential, Encoding, Abuse, Total Flags, Risk.

**F-UI-04: Redaction View** — Render a filterable `st.dataframe()` showing all detected entities with masked/anonymized values. Columns: Page, Type, Category, Matched Value, Masked Value (🔒), Confidence, Severity, Method, Context Snippet. Provide `st.multiselect` filters for Type (PII/CONFIDENTIAL/ENCODING/ABUSE) and Severity (CRITICAL/HIGH/MEDIUM/LOW). Show a count like "Showing N of M total findings".

**F-UI-05: PDF Download Button** — If `result["report_path"]` exists as a file, render `st.download_button` with label "📥 Download Full Compliance Report (PDF)", MIME type `application/pdf`, and a filename like `compliance_report_{upload_id}.pdf`.

**F-UI-06: Warnings Expander** — If `result["errors"]` is non-empty, render a `st.expander("⚠️ Scan Warnings")` showing each error as `st.warning()`.

**F-UI-07: Rules Editor Page** — Implement `app/pages/02_rules.py` with: (a) `st.checkbox` for enabling/disabling each detection category (PII, Confidentiality, Encoding, Abuse), (b) `st.slider(0.5, 1.0)` for confidence thresholds per category, (c) `st.text_area` for custom keywords (one per line), (d) `st.multiselect` for `allowed_languages`, (e) `st.number_input` for `non_ascii_threshold`, (f) a "Save Rules" button that writes the updated dict to `config/rules.json`.

**F-UI-08: Reports Browser Page** — Implement `app/pages/03_reports.py` that: (a) calls `get_all_scans()` to list the last 50 scans, (b) shows per-scan metadata as metrics (filename, date, pages, flags, risk), (c) provides a download button for each PDF report if the file exists, (d) provides a `st.expander("View JSON")` toggle for the full result JSON, (e) provides a "Delete" button that calls `delete_scan(upload_id)` and refreshes the list.

---

## SECTION 3: Business Logic & Functional Requirements

**F-BL-01: PDF Ingestion** — Implement a LangGraph node (`ingest_node`) that: (a) opens the PDF with `fitz.open(pdf_path)` (PyMuPDF), (b) for each page, calls `page.get_text("text", flags=fitz.TEXT_PRESERVE_WHITESPACE | fitz.TEXT_PRESERVE_LIGATURES)`, (c) if text is empty but `page.get_images()` is non-empty, sets text to `[IMAGE_ONLY_PAGE — N images]`, (d) calls `chardet.detect(text.encode())` to get `detected_encoding` and `encoding_confidence`, (e) returns `total_pages` (int) and `pages_text` (list of `PageText` dicts).

**F-BL-02: PII Detection — Regex Engine** — Implement regex detection for 12 PII categories: EMAIL (97% conf), PHONE_INDIA (+91 format, 92%), PHONE_US (US format, 88%), SSN (NNN-NN-NNNN, 95% critical), AADHAAR (4-4-4 digit, 95% critical), PAN_CARD (AAAAA9999A, 95%), PASSPORT (letter + 7 digits, 82% critical), CREDIT_CARD (Visa/MC/Amex, 93% critical), BANK_ACCOUNT (9-18 digits after "account no", 80%), IBAN (country code + checksum, 92%), IP_ADDRESS (IPv4, 90% medium), DATE_OF_BIRTH (DOB: MM/DD/YYYY, 88%). Each finding must include: `category`, `value` (truncated to 80 chars), `context` (60-char window around match), `confidence`, `risk_level`, `detection_method: "regex"`.

**F-BL-03: PII Detection — AI Enhancement** — After regex detection, send the first 4,000 chars of each page to the LLM with the system prompt from `config/prompts/pii_prompt.txt`. Parse the JSON response and extract `findings[]`. Filter findings below `min_confidence` threshold. Merge AI findings with regex findings by deduplicating on value substring: if an AI finding's value is a substring of any regex finding's value (or vice versa), drop the AI finding. AI failures must be non-fatal — wrap in bare `except Exception: pass`.

**F-BL-04: Confidentiality Detection — Regex Engine** — Implement regex detection for 14 credential categories: API_KEY_OPENAI (`sk-[a-zA-Z0-9]{32,}`, 98% critical), API_KEY_ANTHROPIC (`sk-ant-...`, 98%), API_KEY_GROQ (`gsk_...`, 98%), AWS_ACCESS_KEY (`AKIA[A-Z0-9]{16}`, 99%), AWS_SECRET_KEY (inline assignment pattern, 97%), GITHUB_TOKEN (`gh[pousr]_...`, 98%), GOOGLE_API_KEY (`AIza...`, 97%), STRIPE_KEY (`sk/pk_live/test_...`, 98%), JWT_TOKEN (`eyJ...eyJ...sig`, 95%), PASSWORD_INLINE (password= or passwd=, 91%), SECRET_INLINE (secret= or client_secret=, 89%), DB_CONNECTION_STRING (mongodb/postgresql/mysql URI, 95%), PRIVATE_KEY_BLOCK (BEGIN RSA PRIVATE KEY block, 99%), SALARY_DATA (salary: $NN,NNN format, 82%). Auto-mask values longer than 12 chars as `value[:6] + "…" + value[-4:]`.

**F-BL-05: Confidentiality Detection — AI Semantic** — Send page text to LLM with `confidential_prompt.txt`. If `custom_keywords` are configured in rules, append them to the system prompt as additional detection targets. From AI response, keep only findings with category in: `TRADE_SECRET`, `MERGER_ACQUISITION`, `FINANCIAL_FORECAST`, `CUSTOMER_LIST`, `SOURCE_CODE`, `INTERNAL_CODENAME`, `CUSTOM_KEYWORD`.

**F-BL-06: Encoding Guard** — Implement 6 rule-based checks (no AI): (1) NON_ASCII_CHARS: count chars > 127 not in configured allowed set; flag if count > `non_ascii_threshold` (default 5); (2) MULTILINGUAL_CONTENT: detect Devanagari (U+0900–U+097F), Arabic (U+0600–U+06FF), CJK (U+4E00–U+9FFF), Cyrillic (U+0400–U+04FF) via Unicode range checks; (3) OCR_CORRUPTION: check for null bytes, U+FFFD replacement char, slash in mid-word pattern; (4) LOW_ENCODING_CONFIDENCE: flag if chardet confidence < `min_encoding_confidence` (0.85); (5) NON_UTF8_ENCODING: flag if detected encoding is not "utf-8" or "ascii"; (6) NON_ALLOWED_LANGUAGE: run `langdetect.detect()` and flag if result not in `allowed_languages` list. Each finding must include `type`, `severity`, `confidence`, `note`, `recommendation`.

**F-BL-07: Abuse Detection** — Implement 3-layer detection: Layer 1 — compile phrase patterns for 6 categories (THREAT, HATE_SPEECH, HARASSMENT, VIOLENCE_INCITEMENT, ILLEGAL_CONTENT, SLUR); flag case-insensitive matches. Layer 2 — compile keyword signals for 12 patterns (threatening, blackmail, extort, intimidat*, harassment, bully*, cyberstalk*, violence against, physical harm, sexual harassment, quid pro quo, retaliat*). Layer 3 — AI call with `abuse_prompt.txt`; if `category` in AI response is in `zero_tolerance_categories` (child_safety, terrorism), force `risk_level: "critical"`. Store ALL abuse values as `[REDACTED — abuse content]`.

**F-BL-08: Risk Aggregation** — Implement an aggregator that for each page: (a) looks up pii_page, conf_page, enc_page, abuse_page by `page_num`, (b) collects all flags, (c) computes `severity_risk = MAX(pii_risk, conf_risk, enc_risk, abuse_risk)`, (d) computes `count_risk` based on total flags (≥10→critical, ≥5→high, ≥2→medium, ≥1→low), (e) sets `overall_risk = MAX(severity_risk, count_risk)`, (f) normalizes all risk labels through `_normalize_risk()` that maps unrecognized values to "low". Document-level `highest_risk` = MAX of all page overall_risks. Set `processing_complete: True`.

**F-BL-09: PDF Report Generation** — Generate an A4 PDF using ReportLab with: (1) Title block (document name, Scan ID, timestamp), (2) Executive Summary table (10 rows, 2 columns; Highest Risk row background colored by risk level), (3) Page-by-Page Risk Heatmap table (7 columns: Page, PII, Confid., Encoding, Abuse, Total, Risk; Risk column cells color-coded), (4) Detailed Findings section with per-page KeepTogether blocks, each containing a 7-column table (Type, Entity, Matched Value, Conf., Method, Severity, Context). Color palette: critical=#C0392B, high=#E67E22, medium=#F39C12, low=#27AE60. Save to `reports/{pdf_name}_{upload_id}_{timestamp}_compliance.pdf`.

**F-BL-10: Custom Rules Configuration** — Implement `load_rules()` that reads `config/rules.json` and returns a dict. Implement `save_rules(rules)` that JSON-dumps to the same file. The rules dict structure must match exactly: version, sensitivity, pii{enabled, detect_email, detect_phone, detect_ssn_aadhaar, detect_credit_card, detect_address, detect_dob, min_confidence, risk_threshold}, confidentiality{enabled, detect_api_keys, detect_passwords, detect_trade_secrets, detect_financial_data, detect_merger_acquisition, custom_keywords[], min_confidence}, encoding{enabled, require_utf8, allowed_languages[], min_encoding_confidence, flag_non_ascii, non_ascii_threshold}, abuse{enabled, detect_hate_speech, detect_sexual_content, detect_violence_incitement, detect_illegal_content, detect_harassment, sensitivity_level, zero_tolerance_categories[]}, reporting{include_text_context, context_window_chars, generate_pdf_report, generate_json_report}.

---

## SECTION 4: Data Persistence

**F-DB-01:** Implement SQLite persistence using Python's built-in `sqlite3`. Store the database at `storage/compliance.db`. Enable WAL mode with `PRAGMA journal_mode=WAL`. Use `conn.row_factory = sqlite3.Row` for named column access.

**F-DB-02:** Create a `scans` table on first use with columns: id (PK auto), upload_id (TEXT UNIQUE), pdf_name (TEXT), scanned_at (TEXT ISO timestamp), total_pages (INTEGER), total_flags (INTEGER), highest_risk (TEXT), status (TEXT default 'completed'), result_json (TEXT), report_path (TEXT). Create index on `upload_id`.

**F-DB-03:** Implement `save_result(upload_id, pdf_name, result)` using `INSERT OR REPLACE` to upsert a scan record. Extract `summary.total_flags` and `summary.highest_risk` from the result dict. Store the full result dict as `json.dumps(result)`.

**F-DB-04:** Implement `get_result(upload_id)` that returns the full scan dict with an additional `data` key containing the parsed `result_json`.

**F-DB-05:** Implement `get_all_scans()` that returns the last 50 scans ordered by `scanned_at DESC`, returning only metadata columns (not `result_json`).

**F-DB-06:** Implement `delete_scan(upload_id)` that deletes the record and returns `True` if a row was deleted.

---

## SECTION 5: API & Integration

**F-API-01: AI Provider Factory** — Implement `get_ai_client()` that reads `AI_PROVIDER` env var and returns: (a) `Groq(api_key=GROQ_API_KEY)` for "groq", (b) `anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)` for "anthropic", (c) `google.generativeai` configured with `GOOGLE_API_KEY` for "gemini", (d) `OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")` for "ollama".

**F-API-02: Unified AI Call** — Implement `call_ai(system_prompt, user_message, max_tokens=1024)` with `@retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=2, max=60), reraise=True)` from tenacity. For groq/ollama: use `chat.completions.create()` with `temperature=0.1` and `messages=[{role:system, ...}, {role:user, ...}]`. For anthropic: use `messages.create()`. For gemini: use `GenerativeModel("gemini-1.5-flash").generate_content()`.

**F-API-03: JSON Response Parser** — Implement `parse_json_response(raw_text)` that: (a) strips leading ` ```json ``` ` or ` ``` ``` ` markdown fences, (b) attempts `json.loads()`, (c) on failure, uses regex `\{.*\}` with DOTALL to extract embedded JSON, (d) on total failure, returns `{"error": "Failed to parse AI response", "raw": text}` — never raises an exception.

**F-API-04: PII Redaction Utility** — Implement `mask_value(category, value)` with category-specific masking: EMAIL → `j***@e***.com` (mask local part after first char, mask domain before TLD), SSN → `***-**-NNNN` (show last 4 only), AADHAAR → `XXXX XXXX NNNN` (show last 4), CREDIT_CARD → `XXXX-XXXX-XXXX-NNNN` (show last 4), PHONE_INDIA → `**********NN` (show last 2), PASSPORT → `AXXXXXX` (show first char), IP_ADDRESS → `X.X.XXX.XXX` (show first 2 octets), all others → `val[:3] + "***"`.

**F-API-05: Redaction Table Builder** — Implement `build_redaction_table(page_results)` that flattens all flags from all pages into a list of dicts with keys: Page, Type, Category, Matched Value, Masked Value, Confidence, Severity, Method, Context. For encoding flags, format confidence from severity string (critical→"95%+", high→"90%+", etc.).

---

## SECTION 6: DevOps & Deployment

**F-OPS-01: Dockerfile** — Build from `python:3.11-slim`. Install system deps: `gcc`, `libfreetype6-dev` (for ReportLab). Copy `requirements.txt` first, then `pip install --no-cache-dir`. Copy app code. Create `reports/` and `storage/` directories. Expose port 8501. Add `HEALTHCHECK` via `curl -f http://localhost:8501/_stcore/health`. CMD: `streamlit run app/main.py --server.port=8501 --server.address=0.0.0.0 --server.headless=true --browser.gatherUsageStats=false`.

**F-OPS-02: Docker Compose** — Define a single `compliance-scanner` service. Mount volumes: `./reports:/app/reports`, `./storage:/app/storage`, `./config/rules.json:/app/config/rules.json`. Pass `GROQ_API_KEY` from host environment. Map port 8501:8501.

**F-OPS-03: GitHub Actions CI** — Define a workflow triggered on push to `main` and `develop`. Three jobs: (1) `test`: Python 3.11, pip with cache, install requirements + pytest-cov, run `pytest tests/ --cov=pipeline --cov=config`, upload coverage to Codecov. (2) `security-scan`: run `bandit -r pipeline/ config/ app/` and `safety check`. (3) `docker-build` (main only): `docker build -t pdf-compliance-scanner .`.

**F-OPS-04: Streamlit Config** — Create `.streamlit/config.toml` with theme settings (dark mode preferred), server maxUploadSize, and runner settings.

---

## SECTION 7: Testing

**F-TEST-01: Fixtures** — Create `tests/conftest.py` with: (a) `sample_state` fixture returning a valid 2-page `PipelineState` dict with realistic page text containing email and phone patterns, encoding_confidence=0.99, enabled compliance_rules; (b) `mock_ai_pii_response` fixture returning a JSON string with `{"findings": [{"category": "EMAIL", ...}, {"category": "PHONE", ...}]}`; (c) `mock_ai_clean_response` fixture returning `{"findings": []}`.

**F-TEST-02: Encoding Tests** — Implement `TestEncodingNode` class testing: (1) clean English text returns 2 results with no flags (low risk), (2) Japanese characters in text produce NON_ASCII_CHARS flag, (3) encoding_confidence=0.5 produces LOW_ENCODING_CONFIDENCE flag, (4) `encoding.enabled=False` in rules returns `encoding_results=[]`.

**F-TEST-03: Aggregator Tests** — Implement `TestAggregatorNode` testing: (1) page 1 with high PII risk + page 2 with critical API key → page1.overall_risk="high", page2.overall_risk="critical", total_flags=2, highest_risk="critical", (2) all empty results → total_flags=0, highest_risk="low".

**F-TEST-04: PII Node Tests** — Implement `TestPIINodeWithMockedAI` using `unittest.mock.patch("pipeline.nodes.pii_detector.call_ai")`: (1) test EMAIL and PHONE categories appear in flags, (2) empty page text → no AI call, empty flags, (3) `pii.enabled=False` → `pii_results=[]`.

**F-TEST-05: Integration Test** — Implement `test_pipeline.py` with a test that mocks all AI calls and runs the full `run_pipeline()` function, asserting: `processing_complete=True`, `page_results` has correct page count, `highest_risk` is a known value, no errors in `errors[]`.

---

## SECTION 8: Test Utilities

**F-UTIL-01: Test PDF Generator** — Implement `create_test_pdf.py` that creates a multi-page PDF (`tests/fixtures/demo_violations.pdf`) containing: (a) page 1 with email, phone, Aadhaar, PAN card samples, (b) page 2 with API key, password, AWS key samples, (c) page 3 with multilingual text and non-ASCII chars, (d) page 4 with threat/harassment phrases.

---

*"If I gave this file to a stranger, could they build the exact same app without seeing the code?" — Yes.*
