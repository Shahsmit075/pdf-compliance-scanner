# 📚 Code Documentation
## AI-Powered PDF Compliance Scanner

> **Focus:** Code structure, data flow, and implementation details. For product context, see `PRD.md`. For setup, see `README.md`.

---

## 1. Module Map

```
pdf-compliance-scanner/
│
├── app/                        ← Streamlit UI Layer
│   ├── main.py                 ← Entry point, home page, sidebar
│   ├── pages/
│   │   ├── 01_upload.py        ← Upload & Scan workflow
│   │   ├── 02_rules.py         ← Rules editor (reads/writes rules.json)
│   │   └── 03_reports.py       ← Past scans browser (SQLite)
│   ├── components/
│   │   ├── uploader.py         ← Reusable file uploader widget
│   │   └── report_card.py      ← Scan summary card widget
│   └── utils/
│       └── redaction.py        ← PII masking utility
│
├── pipeline/                   ← LangGraph Pipeline Layer
│   ├── state.py                ← TypedDict schema (PipelineState)
│   ├── graph.py                ← DAG builder + run_pipeline()
│   └── nodes/
│       ├── ingest.py           ← PDF text extraction (PyMuPDF)
│       ├── pii_detector.py     ← PII: regex + AI (12 patterns)
│       ├── confidentiality.py  ← Credentials: regex + AI (14 patterns)
│       ├── encoding_guard.py   ← Encoding: 6 rule-based checks
│       ├── abuse_detector.py   ← Abuse: phrases + keywords + AI
│       ├── aggregator.py       ← Merge all results, compute risk
│       └── report_builder.py   ← ReportLab PDF generation
│
├── config/
│   ├── ai_provider.py          ← AI factory (Groq/Gemini/Anthropic/Ollama)
│   ├── rules.py                ← Load/save compliance rules
│   ├── rules.json              ← Default rule configuration (editable via UI)
│   └── prompts/
│       ├── pii_prompt.txt      ← System prompt for PII AI node
│       ├── confidential_prompt.txt
│       ├── encoding_prompt.txt
│       └── abuse_prompt.txt
│
├── storage/
│   └── database.py             ← SQLite CRUD (scans table)
│
├── tests/
│   ├── conftest.py             ← Shared fixtures and mock responses
│   ├── test_nodes.py           ← Unit tests (Encoding, Aggregator, PII)
│   └── test_pipeline.py        ← Integration tests (full pipeline)
│
├── .github/workflows/ci.yml   ← GitHub Actions (test + security + docker)
├── Dockerfile                  ← python:3.11-slim image
├── docker-compose.yml          ← Volume mounts for reports/ & storage/
└── requirements.txt            ← All Python dependencies
```

---

## 2. Pipeline State (`pipeline/state.py`)

The `PipelineState` TypedDict is the **single shared data contract** that flows through every LangGraph node. Each node receives the full state and returns only the **keys it modifies**.

```python
class PipelineState(TypedDict):
    # ─── INPUT ────────────────────────────────────────────────────────────────
    pdf_path: str             # Temp file path of uploaded PDF
    pdf_name: str             # Original filename for display/report
    upload_id: str            # Unique 8-char scan identifier (uuid4[:8])

    # ─── AFTER ingest_node ────────────────────────────────────────────────────
    total_pages: int
    pages_text: List[PageText]   # See PageText TypedDict below

    # ─── AFTER compliance nodes (set in parallel) ─────────────────────────────
    pii_results: List[Dict]
    confidential_results: List[Dict]
    encoding_results: List[Dict]
    abuse_results: List[Dict]

    # ─── AFTER aggregator_node ────────────────────────────────────────────────
    page_results: List[PageResult]
    summary: Dict[str, Any]

    # ─── CONFIG ───────────────────────────────────────────────────────────────
    compliance_rules: Dict[str, Any]   # Loaded from config/rules.json

    # ─── OUTPUT ───────────────────────────────────────────────────────────────
    report_path: Optional[str]
    processing_complete: bool
    errors: List[str]
```

### Supporting TypedDicts

```python
class PageText(TypedDict):
    page_num: int
    text: str
    char_count: int
    detected_encoding: str
    encoding_confidence: float
    image_count: int

class Flag(TypedDict):
    type: str           # e.g., "EMAIL", "API_KEY", "HATE_SPEECH"
    value: str          # Flagged content (truncated/masked for privacy)
    context: str        # Surrounding 60-char text window
    confidence: float   # 0.0 – 1.0
    risk_level: str     # "low" | "medium" | "high" | "critical"
    position: Optional[str]

class PageResult(TypedDict):
    page_num: int
    text_preview: str
    char_count: int
    pii_flags: List[Flag]
    confidential_flags: List[Flag]
    encoding_flags: List[Flag]
    abuse_flags: List[Flag]
    pii_risk: str           # "low" | "medium" | "high" | "critical"
    confidential_risk: str
    encoding_risk: str
    abuse_risk: str
    overall_risk: str       # MAX of all per-check risks
```

---

## 3. DAG Builder (`pipeline/graph.py`)

### Graph Structure

```
START → ingest → [pii_check, confidentiality, encoding_check, abuse_check] → aggregate → build_report → END
                       ↑──────────── parallel fan-out ───────────────────↑
```

### `build_pipeline()` — compiles the LangGraph StateGraph
- Adds 7 nodes: `ingest`, `pii_check`, `confidentiality`, `encoding_check`, `abuse_check`, `aggregate`, `build_report`
- `set_entry_point("ingest")`
- 4 parallel edges: `ingest → {pii_check, confidentiality, encoding_check, abuse_check}`
- Conditional edge from `aggregate`: if `processing_complete` → `build_report`, else loop `aggregate`
- Linear edge: `build_report → END`

### `run_pipeline(pdf_path, pdf_name, upload_id, compliance_rules) → dict`
- Initializes state with all empty fields
- Invokes compiled pipeline synchronously
- Returns final `PipelineState` dict

---

## 4. Pipeline Nodes

### 4.1 `ingest_node` — `pipeline/nodes/ingest.py`

**Input:** `pdf_path`, `pdf_name`  
**Output:** `total_pages`, `pages_text[]`

**Algorithm:**
1. `fitz.open(pdf_path)` — load PDF
2. For each page: `page.get_text("text", flags=fitz.TEXT_PRESERVE_WHITESPACE | fitz.TEXT_PRESERVE_LIGATURES)`
3. If no text + has images → mark as `[IMAGE_ONLY_PAGE — n images]`
4. `chardet.detect(text.encode())` → `detected_encoding`, `encoding_confidence`
5. Append `PageText` dict to `pages_text`

---

### 4.2 `pii_node` — `pipeline/nodes/pii_detector.py`

**Input:** `pages_text[]`, `compliance_rules.pii`  
**Output:** `pii_results[]`

**Dual-Engine Architecture:**

**Layer 1 — Regex (always runs, never fails):**

| Category | Pattern | Risk | Confidence |
|----------|---------|------|-----------|
| EMAIL | `[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}` | high | 97% |
| PHONE_INDIA | `(?:\+91[\s\-]?)?[6-9]\d{9}` | high | 92% |
| PHONE_US | `(?:\+?1[\s\-]?)?\(?\d{3}\)?[\s\-.]\d{3}[\s\-.]\d{4}` | high | 88% |
| SSN | `\d{3}[-\s]\d{2}[-\s]\d{4}` | critical | 95% |
| AADHAAR | `\d{4}[\s\-]\d{4}[\s\-]\d{4}` | critical | 95% |
| PAN_CARD | `[A-Z]{5}[0-9]{4}[A-Z]` | high | 95% |
| PASSPORT | `[A-Z][0-9]{7}` or `[A-Z]{2}[0-9]{6,7}` | critical | 82% |
| CREDIT_CARD | Visa/MC/Amex/Discover | critical | 93% |
| BANK_ACCOUNT | `account\s*(?:no.?\|number\|#)?\s*[:\-]?\s*[\d\s]{9,18}` | high | 80% |
| IBAN | `[A-Z]{2}\d{2}[A-Z0-9]{4}\d{7}...` | high | 92% |
| IP_ADDRESS | `(\d{1,3}\.){3}\d{1,3}` | medium | 90% |
| DATE_OF_BIRTH | `(?:DOB\|Date of Birth)[:\s]+\d{1,2}/\d{1,2}/\d{2,4}` | high | 88% |

**Layer 2 — AI (Groq Llama3, best-effort):**
- Sends first 4,000 chars of page to LLM with `pii_prompt.txt` system prompt
- Parses JSON response with `parse_json_response()`
- AI findings below `min_confidence` are discarded

**Layer 3 — Merge:**
- `_merge_findings()`: AI findings that overlap any regex finding by substring are dropped
- Novel AI findings (new values) are appended with `detection_method: "ai"`

**Risk Derivation:** `_risk_from_flags()` → highest `risk_level` across all findings

---

### 4.3 `confidentiality_node` — `pipeline/nodes/confidentiality.py`

**Input:** `pages_text[]`, `compliance_rules.confidentiality`  
**Output:** `confidential_results[]`

**Layer 1 — Credential Regex (14 patterns):**

| Category | Pattern | Risk | Confidence |
|----------|---------|------|-----------|
| API_KEY_OPENAI | `sk-[a-zA-Z0-9]{32,}` | critical | 98% |
| API_KEY_ANTHROPIC | `sk-ant-[a-zA-Z0-9\-]{32,}` | critical | 98% |
| API_KEY_GROQ | `gsk_[a-zA-Z0-9]{32,}` | critical | 98% |
| AWS_ACCESS_KEY | `AKIA[A-Z0-9]{16}` | critical | 99% |
| AWS_SECRET_KEY | `aws_secret_access_key = [a-zA-Z0-9/+]{40}` | critical | 97% |
| GITHUB_TOKEN | `gh[pousr]_[a-zA-Z0-9]{36}` | critical | 98% |
| GOOGLE_API_KEY | `AIza[a-zA-Z0-9\-_]{35}` | critical | 97% |
| STRIPE_KEY | `(?:sk\|pk)_(?:live\|test)_[a-zA-Z0-9]{24,}` | critical | 98% |
| JWT_TOKEN | `eyJ[...].eyJ[...].sig` | critical | 95% |
| PASSWORD_INLINE | `password\s*[=:]\s*[^\s]{6,}` | critical | 91% |
| SECRET_INLINE | `secret\|client_secret\s*[=:]\s*[^\s]{6,}` | high | 89% |
| DB_CONNECTION_STRING | `mongodb\|postgresql\|mysql://...` | critical | 95% |
| PRIVATE_KEY_BLOCK | `-----BEGIN RSA PRIVATE KEY-----` | critical | 99% |
| SALARY_DATA | `salary\|compensation\s*[:\-]?\s*[₹$€]\s*[\d,]{4,}` | high | 82% |

**Security:** Values auto-masked → `value[:6] + "…" + value[-4:]`

**Layer 2 — AI Semantic Detection:**
- Catches: `TRADE_SECRET`, `MERGER_ACQUISITION`, `FINANCIAL_FORECAST`, `CUSTOMER_LIST`, `SOURCE_CODE`, `INTERNAL_CODENAME`, `CUSTOM_KEYWORD`
- Custom keywords from `rules.json` are injected into the system prompt

**Merge Strategy:** AI findings are kept only for semantic-only categories not detectable by regex.

---

### 4.4 `encoding_node` — `pipeline/nodes/encoding_guard.py`

**Input:** `pages_text[]`, `compliance_rules.encoding`  
**Output:** `encoding_results[]`

**6 Rule-Based Checks (no AI):**

| Check Type | Condition | Severity |
|-----------|-----------|---------|
| NON_ASCII_CHARS | > `non_ascii_threshold` non-ASCII chars | medium |
| MULTILINGUAL_CONTENT | Devanagari/Arabic/CJK/Cyrillic script detected | high |
| OCR_CORRUPTION | Garbled chars, null bytes, U+FFFD, slash mid-word | high |
| LOW_ENCODING_CONFIDENCE | chardet confidence < `min_encoding_confidence` (0.85) | high |
| NON_UTF8_ENCODING | Detected encoding ≠ UTF-8 or ASCII | medium |
| NON_ALLOWED_LANGUAGE | langdetect finds language not in `allowed_languages` | medium |

Each finding includes: `type`, `severity`, `confidence`, `note`, `recommendation`

---

### 4.5 `abuse_node` — `pipeline/nodes/abuse_detector.py`

**Input:** `pages_text[]`, `compliance_rules.abuse`  
**Output:** `abuse_results[]`

**Three-Layer Architecture:**

**Layer 1 — Phrase Patterns (6 categories, high precision):**
- `THREAT`: "i will kill", "you will die", "bomb threat"
- `HATE_SPEECH`: "go back to your country", "inferior race"
- `HARASSMENT`: "i know where you live", "ruin your career"
- `VIOLENCE_INCITEMENT`: "incite violence", "burn it down"
- `ILLEGAL_CONTENT`: "how to make a bomb", "drug trafficking"
- `SLUR`: Common slur patterns in obfuscated regex

**Layer 2 — Keyword Signals (12 patterns, broader catch):**
- `threatening`, `blackmail`, `extort`, `intimidat*`
- `harassment`, `bully*`, `cyberstalk*`
- `violence against`, `physical harm`
- `sexual harassment`, `quid pro quo`

**Layer 3 — AI (Groq, best-effort):**
- `zero_tolerance_categories`: Always `critical` risk — overrides everything
- Categories: `child_safety`, `terrorism` → immediate critical flag

**Privacy:** All abuse `value` fields stored as `[REDACTED — abuse content]`

---

### 4.6 `aggregator_node` — `pipeline/nodes/aggregator.py`

**Input:** `pii_results`, `confidential_results`, `encoding_results`, `abuse_results`, `pages_text`  
**Output:** `page_results[]`, `summary{}`, `processing_complete: True`

**Dual Risk Scoring (takes MAX):**

```python
# Risk from severity labels
severity_risk = _highest_risk(pii_risk, conf_risk, enc_risk, abuse_risk)

# Risk from flag count
count_risk = _flags_to_risk(total_flags_on_page)
# ≥10 flags → critical; ≥5 → high; ≥2 → medium; ≥1 → low

overall_risk = _highest_risk(severity_risk, count_risk)
```

**Risk Normalization:** `_normalize_risk()` maps any unrecognized value → `"low"`. `"unknown"` is never output.

**Summary dict keys:**
- `total_pages`, `total_flags`, `pages_with_issues`, `clean_pages`
- `highest_risk`, `total_issues: {pii, confidential, encoding, abuse}`
- `risk_counts: {low, medium, high, critical}`

---

### 4.7 `report_node` — `pipeline/nodes/report_builder.py`

**Input:** Full `PipelineState` after aggregation  
**Output:** `report_path: str`

**Report Sections (ReportLab SimpleDocTemplate, A4):**

1. **Title Block** — document name, Scan ID, timestamp
2. **Executive Summary** — 10-row colored metrics table
   - Highest Risk row background color = risk-coded (red/orange/yellow/green)
3. **Risk Heatmap** — 7-column table (page, PII, Confid., Encoding, Abuse, Total, Risk)
   - Risk column cells color-coded per level
4. **Detailed Findings** — per-page KeepTogether blocks
   - 7 columns: Type | Entity | Matched Value | Conf. | Method | Severity | Context
   - Severity column color-coded; abuse values shown as `[redacted]`

**File naming:** `reports/{pdf_name}_{upload_id}_{timestamp}_compliance.pdf`

**Helper functions:**
- `_fmt_confidence(flag)` — always returns real percentage, never "N/A"
- `_fmt_value(flag)` — returns masked value or `[redacted]` for abuse
- `_fmt_context(flag)` — 70-char truncated context/note
- `_fmt_method(flag)` — "Regex" or "AI"

---

## 5. AI Provider (`config/ai_provider.py`)

### `call_ai(system_prompt, user_message, max_tokens=1024) → str`

Unified interface across 4 providers, with retry:

```python
@retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=2, max=60))
def call_ai(...):
    client = get_ai_client()  # reads AI_PROVIDER env var
    if AI_PROVIDER in ["groq", "ollama"]:
        # OpenAI-compatible chat completions API, temperature=0.1
    elif AI_PROVIDER == "anthropic":
        # messages.create(), claude-sonnet-4-5
    elif AI_PROVIDER == "gemini":
        # GenerativeModel("gemini-1.5-flash"), system_instruction
```

### `parse_json_response(raw_text) → dict`

Handles:
1. Plain JSON string
2. JSON wrapped in ` ```json ``` ` markdown blocks
3. JSON embedded anywhere in freetext (regex fallback `\{.*\}`)
4. Returns `{"error": ..., "raw": ...}` on total failure — never raises

---

## 6. Database (`storage/database.py`)

### Schema

```sql
CREATE TABLE scans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    upload_id TEXT UNIQUE NOT NULL,
    pdf_name TEXT NOT NULL,
    scanned_at TEXT NOT NULL,
    total_pages INTEGER DEFAULT 0,
    total_flags INTEGER DEFAULT 0,
    highest_risk TEXT DEFAULT 'low',
    status TEXT DEFAULT 'completed',
    result_json TEXT,
    report_path TEXT
);
CREATE INDEX idx_upload_id ON scans(upload_id);
```

### API

| Function | Description |
|----------|-------------|
| `init_db()` | Create table if not exists (called on every op) |
| `save_result(upload_id, pdf_name, result)` | INSERT OR REPLACE |
| `get_result(upload_id)` | SELECT single scan, parses `result_json` |
| `get_all_scans()` | SELECT last 50 (metadata only, no JSON) |
| `delete_scan(upload_id)` | DELETE by upload_id, returns bool |

**WAL mode:** `PRAGMA journal_mode=WAL` — safe for concurrent reads.  
**Row factory:** `conn.row_factory = sqlite3.Row` — named column access.

---

## 7. Redaction Utility (`app/utils/redaction.py`)

### `build_redaction_table(page_results) → List[dict]`

Flattens all flags from `page_results` into a list of dicts for `st.dataframe()`:

```python
{
    "Page": 1,
    "Type": "PII",           # PII / CONFIDENTIAL / ENCODING / ABUSE
    "Category": "EMAIL",
    "Matched Value": "john@example.com",
    "Masked Value": "j***@e***.com",
    "Confidence": "97%",
    "Severity": "HIGH",
    "Method": "Regex",
    "Context": "…sent to john@example.com for…"
}
```

### `mask_value(category, value) → str`

Category-specific masking rules:

| Category | Original | Masked |
|----------|---------|--------|
| EMAIL | john.doe@example.com | j***@e***.com |
| SSN | 123-45-6789 | ***-**-6789 |
| AADHAAR | 1234 5678 9012 | XXXX XXXX 9012 |
| CREDIT_CARD | 4111-1111-1111-1111 | XXXX-XXXX-XXXX-1111 |
| PHONE_INDIA | +91-9876543210 | **********10 |
| PASSPORT | A1234567 | AXXXXXX |
| IP_ADDRESS | 192.168.1.100 | 192.168.XXX.XXX |
| others | any value | first 3 chars + `***` |

---

## 8. Compliance Rules (`config/rules.py`)

### `load_rules() → dict`
- Reads `config/rules.json`
- Returns parsed dict; caller receives defaults if file missing

### `save_rules(rules: dict)`
- JSON-dumps rules dict to `config/rules.json` with indent=2
- Called by the Rules Editor page on save

---

## 9. UI Pages

### `app/main.py` — Home
- Streamlit entry point: `set_page_config()`, custom CSS
- Sidebar: branding + tech stack listing
- Main: header + 4 feature cards + navigation instructions

### `app/pages/01_upload.py` — Upload & Scan
1. `st.file_uploader(type=["pdf"])` — accept PDF
2. Show file metadata (name, size, type)
3. "Run Compliance Scan" button
4. On click: write to temp file → `run_pipeline()` → `save_result()` → store in `st.session_state`
5. Progress bar: 10% → 20% → 90% → 100%
6. Results display: metrics, issue breakdown, heatmap table
7. Redaction view: filterable `st.dataframe()` with masked values
8. Download button for PDF report
9. Warnings expander for `errors[]`

### `app/pages/02_rules.py` — Rules Editor
- Loads `rules.json` via `load_rules()`
- st.checkbox for each category toggle
- st.slider for confidence thresholds
- st.text_area for custom keywords
- st.multiselect for allowed_languages
- st.number_input for non_ascii_threshold
- "Save Rules" button → `save_rules()`

### `app/pages/03_reports.py` — Reports Browser
- `get_all_scans()` from SQLite
- For each scan: metadata metrics, download button, JSON expander, delete button
- `delete_scan()` on delete click

---

## 10. Testing

### Fixture: `tests/conftest.py`

```python
@pytest.fixture
def sample_state():
    return {
        "pdf_path": "/tmp/test.pdf",
        "pdf_name": "test_document.pdf",
        "upload_id": "abc12345",
        "total_pages": 2,
        "pages_text": [
            {"page_num": 1, "text": "Contact john@example.com or call 9876543210",
             "char_count": 500, "detected_encoding": "utf-8", "encoding_confidence": 0.99, "image_count": 0},
            {"page_num": 2, "text": "Account: 123456789012, DOB: 01/01/1990",
             "char_count": 400, "detected_encoding": "utf-8", "encoding_confidence": 0.98, "image_count": 0},
        ],
        "pii_results": [], "confidential_results": [], "encoding_results": [], "abuse_results": [],
        "page_results": [], "summary": {},
        "compliance_rules": {"pii": {"enabled": True, "min_confidence": 0.75}, ...},
        "report_path": None, "processing_complete": False, "errors": [],
    }
```

### CI Pipeline (`.github/workflows/ci.yml`)

**Job 1: test** (Python 3.11)
- `pip install -r requirements.txt pytest-cov`
- `pytest tests/ --cov=pipeline --cov=config`
- Upload coverage to Codecov

**Job 2: security-scan**
- `bandit -r pipeline/ config/ app/ -ll` — detect high-severity issues
- `safety check` — scan for CVEs in requirements

**Job 3: docker-build** (main branch only)
- `docker build -t pdf-compliance-scanner .`

---

## 11. Code Quality Notes

### Risk That "unknown" Never Appears
The `_normalize_risk()` function in `aggregator.py` explicitly maps any unrecognized string to `"low"`. All consumers of `overall_risk` can safely assume one of 4 known values.

### AI Failure is Non-Fatal
Every node that calls `call_ai()` wraps it in a bare `except Exception: pass`. The `pii_results`, `confidential_results`, and `abuse_results` will still contain regex findings even if the AI call fails due to network issues or rate limits.

### Temp File Cleanup
The upload page uses a `try/finally` block to call `os.unlink(tmp_path)` — the temp PDF is always deleted after the scan, regardless of success or failure.

### Secret Masking at Detection Time
Credential values in `confidentiality.py` are masked **before** being stored in the `Flag` object — they never appear as plaintext in the database or PDF report.

---

*Last Updated: May 2026*
