# 🛡️ AI-Powered PDF Compliance Scanner — Full Project Explanation

---

## 1. Project Overview

**What it is:** A production-ready, AI-powered PDF compliance scanning system that automatically detects privacy violations, confidential data, encoding issues, and abusive content in uploaded PDF documents.

**Why it exists:** Organizations handling PDFs (contracts, HR documents, reports, emails) face compliance risks from GDPR, HIPAA, and internal data policies. Manual review is slow and error-prone. This tool automates that process.

**Core value proposition:**
- Upload any PDF → get a structured compliance report in seconds
- Detects PII (emails, phone, Aadhaar, SSN, passport, credit cards)
- Detects credentials (API keys, AWS keys, GitHub tokens, passwords)
- Detects abuse (threats, hate speech, harassment)
- Detects encoding issues (non-UTF8, multilingual, OCR corruption)
- Generates a downloadable PDF report with masked entity values

---

## 2. Technology Stack

| Layer | Technology | Reason |
|-------|-----------|--------|
| UI | Streamlit | Rapid, Python-native web UI |
| AI Orchestration | LangGraph | DAG-based pipeline with typed state |
| LLM Inference | Groq (Llama 3) | Free tier, fast inference |
| PDF Parsing | PyMuPDF (fitz) | Fast, accurate text extraction |
| Report Generation | ReportLab | Programmatic PDF creation |
| Database | SQLite | Zero-config, embedded persistence |
| Encoding Detection | chardet + langdetect | Reliable charset/language detection |
| Retry Logic | tenacity | Exponential backoff on AI failures |
| Config | python-dotenv | .env-based secret management |

---

## 3. Project Directory Structure

```
pdf_scanner/
│
├── app/                          # Streamlit UI layer
│   ├── main.py                   # Entry point — home page
│   ├── pages/
│   │   ├── 01_upload.py          # Upload & scan page
│   │   ├── 02_rules.py           # Compliance rules editor
│   │   └── 03_reports.py         # Past scan browser
│   ├── components/
│   │   ├── uploader.py           # Reusable file uploader
│   │   └── report_card.py        # Scan summary card
│   └── utils/
│       └── redaction.py          # PII masking utility
│
├── pipeline/                     # LangGraph pipeline
│   ├── state.py                  # TypedDict — shared state schema
│   ├── graph.py                  # DAG builder + run_pipeline()
│   └── nodes/
│       ├── __init__.py
│       ├── ingest.py             # PDF text extraction
│       ├── pii_detector.py       # PII detection (regex + AI)
│       ├── confidentiality.py    # Credential detection (regex + AI)
│       ├── encoding_guard.py     # Encoding/language checks
│       ├── abuse_detector.py     # Abuse/threat detection
│       ├── aggregator.py         # Merge all results + risk scoring
│       └── report_builder.py     # PDF report generation
│
├── config/
│   ├── ai_provider.py            # AI factory (Groq/Gemini/Anthropic/Ollama)
│   ├── rules.py                  # Load/save compliance rules
│   ├── rules.json                # Default rule configuration
│   └── prompts/
│       ├── pii_prompt.txt        # AI prompt for PII detection
│       ├── confidential_prompt.txt
│       ├── encoding_prompt.txt
│       └── abuse_prompt.txt
│
├── storage/
│   ├── __init__.py
│   └── database.py               # SQLite CRUD operations
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py               # Fixtures and mock AI responses
│   ├── test_nodes.py             # Unit tests for each node
│   └── test_pipeline.py          # Integration tests
│
├── .github/workflows/ci.yml      # GitHub Actions CI pipeline
├── .streamlit/config.toml        # Streamlit theme/server config
├── .vscode/settings.json         # VS Code interpreter settings
├── .venv/                        # Virtual environment
├── reports/                      # Generated PDF reports (gitignored)
├── Dockerfile                    # Container image definition
├── docker-compose.yml            # Multi-container orchestration
├── requirements.txt              # Python dependencies
├── .env                          # Local secrets (gitignored)
├── .env.example                  # Template for secrets
├── .gitignore
├── README.md
├── API_AND_DEPLOYMENT_GUIDE.md
└── create_test_pdf.py            # Script to generate demo test PDF
```

---

## 4. System Architecture — How Data Flows

```
User uploads PDF
      │
      ▼
┌─────────────┐
│  Streamlit  │  app/pages/01_upload.py
│  Upload UI  │  Saves to /tmp, generates upload_id
└──────┬──────┘
       │  run_pipeline(pdf_path, pdf_name, upload_id, rules)
       ▼
┌─────────────────────────────────────────────────┐
│              LangGraph Pipeline                  │
│                                                  │
│  ┌──────────┐                                    │
│  │  ingest  │  PyMuPDF → pages_text[]            │
│  └────┬─────┘                                    │
│       │ (fan-out — 4 parallel nodes)              │
│  ┌────┴────┐  ┌──────────┐  ┌────────┐  ┌─────┐ │
│  │   PII   │  │ Confid.  │  │Encoding│  │Abuse│ │
│  │ detect  │  │  detect  │  │ guard  │  │ det.│ │
│  └────┬────┘  └────┬─────┘  └───┬────┘  └──┬──┘ │
│       └────────────┴────────────┴───────────┘    │
│                         │                         │
│                  ┌──────┴──────┐                  │
│                  │  aggregator │  risk scoring     │
│                  └──────┬──────┘                  │
│                         │                         │
│                  ┌──────┴──────┐                  │
│                  │report_builder│ ReportLab PDF    │
│                  └─────────────┘                  │
└─────────────────────────────────────────────────┘
       │
       ▼
┌─────────────┐
│   SQLite    │  storage/database.py
│  database   │  Stores result JSON + report path
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Streamlit  │  Shows metrics, redaction table,
│  Results UI │  download button for PDF report
└─────────────┘
```

---

## 5. Pipeline State — Shared Data Contract

File: `pipeline/state.py`

The `PipelineState` TypedDict is passed between every LangGraph node. Each node receives the full state and returns a **partial update dict**:

```python
class PipelineState(TypedDict):
    # Input
    pdf_path: str             # Temp file path of uploaded PDF
    pdf_name: str             # Original filename
    upload_id: str            # Unique 8-char scan identifier
    compliance_rules: dict    # Loaded from config/rules.json

    # After ingest node
    total_pages: int
    pages_text: list[dict]    # [{page_num, text, char_count, ...}]

    # After detection nodes
    pii_results: list[dict]
    confidential_results: list[dict]
    encoding_results: list[dict]
    abuse_results: list[dict]

    # After aggregator
    page_results: list[dict]  # Merged per-page results
    summary: dict             # Document-level statistics

    # After report builder
    report_path: str | None
    processing_complete: bool
    errors: list[str]
```

---

## 6. Node-by-Node Explanation

### 6.1 Ingest Node (`pipeline/nodes/ingest.py`)

**Purpose:** Extract text from every page of the PDF.

**How it works:**
1. Opens PDF with `fitz.open(path)` (PyMuPDF)
2. For each page: calls `page.get_text("text")` with whitespace/bounds flags
3. If page has no text but has images → marks as `[IMAGE_ONLY_PAGE]`
4. Runs `chardet.detect()` on extracted bytes to detect encoding
5. Returns `pages_text` list with per-page metadata

**Output per page:**
```python
{
    "page_num": 1,
    "text": "full extracted text...",
    "char_count": 1432,
    "detected_encoding": "utf-8",
    "encoding_confidence": 0.99,
    "image_count": 0,
}
```

---

### 6.2 PII Detector (`pipeline/nodes/pii_detector.py`)

**Purpose:** Detect Personally Identifiable Information.

**Architecture:** Dual-engine (regex-first + AI enhancement)

**Layer 1 — Regex (always runs, never fails):**

| Pattern | Example | Confidence |
|---------|---------|-----------|
| EMAIL | john@example.com | 97% |
| PHONE_INDIA | +91-9876543210 | 92% |
| PHONE_US | (555) 123-4567 | 88% |
| SSN | 123-45-6789 | 95% |
| AADHAAR | 1234 5678 9012 | 95% |
| PAN_CARD | ABCDE1234F | 95% |
| PASSPORT | A1234567 | 82% |
| CREDIT_CARD | 4111-1111-1111-1111 | 93% |
| BANK_ACCOUNT | Account no: 123456789012 | 80% |
| IBAN | GB29NWBK60161331926819 | 92% |
| IP_ADDRESS | 192.168.1.1 | 90% |
| DATE_OF_BIRTH | DOB: 01/01/1990 | 88% |

**Layer 2 — AI (Groq Llama 3, best-effort):**
- Catches contextual PII regex can't find (e.g. "Mr. John Smith, born in 1985")
- Results merged and deduplicated against regex findings by value substring

**On AI failure:** Only regex results are used — never zero-flag because of network issues.

---

### 6.3 Confidentiality Detector (`pipeline/nodes/confidentiality.py`)

**Purpose:** Detect API credentials, secrets, and sensitive business data.

**Layer 1 — Credential regex (14 patterns):**

| Pattern | Example Match |
|---------|--------------|
| API_KEY_OPENAI | sk-proj-abc123... |
| API_KEY_GROQ | gsk_abc123... |
| API_KEY_ANTHROPIC | sk-ant-abc123... |
| AWS_ACCESS_KEY | AKIAIOSFODNN7EXAMPLE |
| AWS_SECRET_KEY | aws_secret_access_key = abc... |
| GITHUB_TOKEN | ghp_abc123... |
| GOOGLE_API_KEY | AIza... |
| STRIPE_KEY | sk_live_... |
| JWT_TOKEN | eyJ...eyJ...sig |
| PASSWORD_INLINE | password = SuperSecret@123 |
| SECRET_INLINE | client_secret = xyz... |
| DB_CONNECTION_STRING | postgresql://user:pass@host/db |
| PRIVATE_KEY_BLOCK | -----BEGIN RSA PRIVATE KEY----- |
| SALARY_DATA | Salary: ₹85,000 |

**Security:** Matched secret values are **auto-masked** in reports (e.g. `sk-pro…r678`).

**Layer 2 — AI:** Detects semantic categories regex can't: trade secrets, M&A information, financial forecasts, custom keywords configured by user.

---

### 6.4 Encoding Guard (`pipeline/nodes/encoding_guard.py`)

**Purpose:** Ensure document encoding compliance.

**Six detection checks (pure rule-based, no AI):**

| Check | Detects |
|-------|---------|
| NON_ASCII_CHARS | Characters above U+007F not in allowed set |
| MULTILINGUAL_CONTENT | Non-Latin scripts (Devanagari, Arabic, CJK, Cyrillic, etc.) |
| OCR_CORRUPTION | Garbled chars, null bytes, U+FFFD, slash mid-word |
| LOW_ENCODING_CONFIDENCE | chardet score < 85% |
| NON_UTF8_ENCODING | Detected encoding is not UTF-8/ASCII |
| NON_ALLOWED_LANGUAGE | langdetect finds a language not in allowed list |

All findings include `confidence`, `severity`, and a human-readable `note`.

---

### 6.5 Abuse Detector (`pipeline/nodes/abuse_detector.py`)

**Purpose:** Detect threats, hate speech, harassment, and illegal content.

**Three-layer architecture:**

**Layer 1 — Phrase patterns** (6 categories, high precision):
- THREAT: `"i will kill"`, `"you will die"`, `"bomb threat"`
- HATE_SPEECH: `"go back to your country"`, `"inferior race"`
- HARASSMENT: `"i know where you live"`, `"ruin your career"`
- VIOLENCE_INCITEMENT: `"incite violence"`, `"burn it down"`
- ILLEGAL_CONTENT: `"how to make a bomb"`, `"drug trafficking"`
- SLUR: Common slur patterns (stored in obfuscated regex form)

**Layer 2 — Keyword signals** (12 patterns, broader catch):
- `threatening`, `blackmail`, `extort`, `intimidat*`
- `harassment`, `bully*`, `cyberstalk*`
- `violence against`, `physical harm`
- `sexual harassment`, `quid pro quo`
- `you people are all`, `retaliat*`

**Layer 3 — AI** (Groq, best-effort):
- Catches nuanced/implied abuse
- Applies zero-tolerance override for `child_safety` and `terrorism` categories

All abuse values are stored as `[REDACTED]` — never stored verbatim.

---

### 6.6 Aggregator (`pipeline/nodes/aggregator.py`)

**Purpose:** Merge all 4 detection results into unified per-page and document-level summaries.

**Dual risk scoring (takes the MAX):**

Risk from severity labels:
- Per-check risk labels (pii_risk, confidential_risk, etc.) → highest wins

Risk from flag count:
```
≥ 10 flags → CRITICAL
≥  5 flags → HIGH
≥  2 flags → MEDIUM
≥  1 flag  → LOW
```

**"UNKNOWN" is never output** — `_normalize_risk()` maps any unknown to `"low"`.

---

### 6.7 Report Builder (`pipeline/nodes/report_builder.py`)

**Purpose:** Generate a professional PDF compliance report using ReportLab.

**Report sections:**
1. **Title block** — document name, scan ID, timestamp
2. **Executive Summary** — 10-row metrics table, risk highlighted in color
3. **Page-by-Page Risk Heatmap** — 7-column table, risk cells color-coded
4. **Detailed Findings** — per-page finding table with:
   - Check Type (PII/CONFIDENTIAL/ENCODING/ABUSE)
   - Entity category (EMAIL, SSN, AWS_ACCESS_KEY, THREAT, etc.)
   - Matched Value (masked for secrets/abuse)
   - Confidence % (real value, never N/A)
   - Detection Method (Regex / AI)
   - Severity (color-coded: red=critical, orange=high, yellow=medium)
   - Context snippet (surrounding text)

Reports saved to: `reports/{filename}_{upload_id}_{timestamp}_compliance.pdf`

---

## 7. AI Provider System (`config/ai_provider.py`)

Supports 4 backends, switchable via `AI_PROVIDER` env var:

| Provider | Env Var | Free Tier |
|----------|---------|-----------|
| Groq (default) | `GROQ_API_KEY` | 14,400 req/day |
| Google Gemini | `GOOGLE_API_KEY` | 1,500 req/day |
| Anthropic Claude | `ANTHROPIC_API_KEY` | Paid only |
| Ollama (local) | None needed | Unlimited |

**`call_ai(system_prompt, user_message, max_tokens)`** — unified interface with:
- `@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))`
- JSON response parsing with fallback extraction via regex

---

## 8. Compliance Rules System (`config/rules.json`)

Rules are JSON-configurable and editable live via the UI (page 2).

```json
{
  "pii": {
    "enabled": true,
    "detect_email": true,
    "detect_phone": true,
    "detect_ssn_aadhaar": true,
    "detect_credit_card": true,
    "min_confidence": 0.75
  },
  "confidentiality": {
    "enabled": true,
    "detect_api_keys": true,
    "detect_passwords": true,
    "custom_keywords": ["PROJECT PHOENIX", "Operation Atlas"],
    "min_confidence": 0.70
  },
  "encoding": {
    "enabled": true,
    "allowed_languages": ["en"],
    "non_ascii_threshold": 5,
    "min_encoding_confidence": 0.85
  },
  "abuse": {
    "enabled": true,
    "zero_tolerance_categories": ["child_safety", "terrorism"],
    "sensitivity_level": "high"
  }
}
```

Changes save instantly and apply to the next scan.

---

## 9. Database Schema (`storage/database.py`)

**Database:** SQLite at `storage/compliance.db`

**Table: `scans`**

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Auto-increment PK |
| upload_id | TEXT UNIQUE | 8-char scan identifier |
| pdf_name | TEXT | Original filename |
| scanned_at | TEXT | ISO timestamp |
| total_pages | INTEGER | Page count |
| total_flags | INTEGER | Total violations |
| highest_risk | TEXT | low/medium/high/critical |
| status | TEXT | completed/failed |
| result_json | TEXT | Full result as JSON blob |
| report_path | TEXT | Path to generated PDF |

**WAL mode** enabled for concurrent reads. All operations use context managers.

---

## 10. Redaction Utility (`app/utils/redaction.py`)

**Purpose:** Mask detected PII values before displaying in the UI.

**Masking rules by category:**

| Category | Original | Masked |
|----------|---------|--------|
| EMAIL | john.doe@example.com | j***@e***.com |
| SSN | 123-45-6789 | ***-**-6789 |
| AADHAAR | 1234 5678 9012 | XXXX XXXX 9012 |
| CREDIT_CARD | 4111-1111-1111-1111 | XXXX-XXXX-XXXX-1111 |
| PHONE_INDIA | +91-9876543210 | **********10 |
| PASSPORT | A1234567 | AXXXXXX |
| IP_ADDRESS | 192.168.1.100 | 192.168.XXX.XXX |

**`build_redaction_table(page_results)`** returns a flat list of dicts ready for `st.dataframe()`.

---

## 11. Streamlit UI Pages

### Page 1: Home (`app/main.py`)
- Navigation hub with feature cards
- Describes 4 compliance check types
- Links to other pages

### Page 2: Upload & Scan (`app/pages/01_upload.py`)
1. File uploader (PDF only, up to 50MB)
2. File metadata display (name, size)
3. "Run Compliance Scan" button
4. Progress bar with stage descriptions
5. Results: metrics, issue breakdown, page heatmap
6. **Redaction View** — filterable table of findings with masked values
7. Download button for PDF report
8. Scan warnings expander

### Page 3: Rules Editor (`app/pages/02_rules.py`)
- Toggle/checkbox controls for each detection category
- Confidence threshold sliders
- Custom keywords textarea
- Language allowlist
- Non-ASCII threshold
- Saves directly to `config/rules.json`

### Page 4: Reports Browser (`app/pages/03_reports.py`)
- Lists all past scans from SQLite
- Per-scan: metrics, download button, JSON summary toggle, delete button

---

## 12. Testing (`tests/`)

### Unit Tests (`tests/test_nodes.py`)
- `TestEncodingNode` — tests 4 rule-based scenarios (clean, non-ASCII, low confidence, disabled)
- `TestAggregatorNode` — tests risk calculation, flag counting, clean documents
- `TestPIINodeWithMockedAI` — tests PII detection with mocked `call_ai` responses

### Integration Tests (`tests/test_pipeline.py`)
- Full pipeline simulation with mocked AI calls
- Verifies state keys, risk normalization, processing_complete flag

### Test Fixtures (`tests/conftest.py`)
- `sample_state` fixture — realistic 2-page PipelineState
- `mock_ai_pii_response` — pre-built AI response JSON with EMAIL + PHONE findings
- `mock_ai_clean_response` — empty findings JSON

**Run tests:**
```bash
source .venv/bin/activate
pytest tests/ -v
pytest tests/test_nodes.py -k "Encoding" -v   # fast, no AI needed
```

---

## 13. GitHub Actions CI (`.github/workflows/ci.yml`)

Three jobs run on every push to `main` or `develop`:

**Job 1: test**
- Python 3.11, cached pip
- `pip install -r requirements.txt pytest-cov`
- `pytest tests/ --cov=pipeline --cov=config`
- Uploads coverage to Codecov

**Job 2: security-scan**
- `bandit` — static security analysis of Python code
- `safety` — checks dependencies for known CVEs

**Job 3: docker-build** (only on `main`)
- `docker build -t pdf-compliance-scanner .`
- Validates the Docker image builds cleanly

---

## 14. Docker Setup

### `Dockerfile`
```
Base: python:3.11-slim
System deps: gcc, libfreetype6-dev (for ReportLab)
COPY requirements.txt → pip install
COPY . → /app
EXPOSE 8501
CMD: streamlit run app/main.py --server.port=8501 --server.headless=true
```

### `docker-compose.yml`
```yaml
services:
  compliance-scanner:
    build: .
    ports: ["8501:8501"]
    volumes:
      - ./reports:/app/reports      # persist generated reports
      - ./storage:/app/storage      # persist SQLite DB
      - ./config/rules.json:/app/config/rules.json
    environment:
      - GROQ_API_KEY=${GROQ_API_KEY}
```

**Run:** `docker-compose up --build`

---

## 15. Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GROQ_API_KEY` | ✅ YES | — | From console.groq.com |
| `AI_PROVIDER` | No | `groq` | groq/gemini/anthropic/ollama |
| `GROQ_MODEL` | No | `llama3-70b-8192` | Groq model name |
| `GOOGLE_API_KEY` | Only if Gemini | — | From aistudio.google.com |
| `ANTHROPIC_API_KEY` | Only if Claude | — | From console.anthropic.com |
| `MAX_FILE_SIZE_MB` | No | `50` | Upload size limit |
| `MAX_PAGES` | No | `500` | Max pages per scan |
| `DEBUG` | No | `false` | Enable verbose logging |

---

## 16. Local Setup — Step by Step

```bash
# 1. Clone
git clone https://github.com/YOUR_USER/pdf-compliance-scanner.git
cd pdf-compliance-scanner

# 2. Virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Add project root to Python path (one-time)
echo "/Users/YOUR_USER/Desktop/pdf_scanner" > \
  .venv/lib/python3.11/site-packages/pdf_scanner.pth

# 5. Configure API key
cp .env.example .env
# Edit .env: set GROQ_API_KEY=gsk_your_actual_key

# 6. (Optional) Generate test PDF
python create_test_pdf.py

# 7. Run
streamlit run app/main.py
# Opens at http://localhost:8501
```

---

## 17. Streamlit Cloud Deployment

```
1. Push repo to GitHub (GROQ_API_KEY must NOT be in any committed file)
2. Go to share.streamlit.io → New app
3. Repository: your-username/pdf-compliance-scanner
4. Branch: main
5. Main file: app/main.py
6. Advanced settings → Secrets:
   GROQ_API_KEY = "gsk_your_actual_key"
   AI_PROVIDER = "groq"
7. Click Deploy
```

URL format: `https://your-app-name.streamlit.app`

---

## 18. Security Considerations

- **`.env` is gitignored** — secrets never committed
- **API keys masked in logs** — only first 6 chars shown
- **Secret values auto-masked** in reports (`sk-pro…r678`)
- **Abuse content redacted** — `[REDACTED]` stored, not the actual slur/threat
- **Temp files deleted** after scan completes (try/finally block)
- **SQLite WAL mode** prevents corruption on concurrent access
- **bandit** runs in CI to catch security anti-patterns
- **No user data persisted in cloud** — only metadata + result JSON in SQLite

---

## 19. Performance Characteristics

| Metric | Value |
|--------|-------|
| Text extraction | ~0.1s per page (PyMuPDF) |
| Regex detection | ~0.01s per page |
| AI node per page | ~1–3s (Groq free tier) |
| Total for 5-page doc | ~15–25 seconds |
| SQLite write | < 0.1s |
| Report generation | ~0.5s |

**Groq free tier limits:** 14,400 req/day. A 10-page document uses ~30 AI calls (3 AI nodes × 10 pages).

---

## 20. Known Limitations & Future Roadmap

### Current Limitations
- No OCR for image-only pages (requires Tesseract)
- No async scanning (large PDFs block the UI)
- No batch upload (one PDF at a time)
- Abuse detection misses subtle/coded language
- No actual PDF text redaction (only UI masking)

### Planned Enhancements
- **OCR support** — Tesseract integration for scanned PDFs
- **Async pipeline** — background scanning with progress via `st.session_state`
- **Redacted PDF export** — ReportLab overlays to physically redact text
- **Batch upload** — scan multiple PDFs in one session
- **Compliance modes** — GDPR / HIPAA / ISO27001 rule presets
- **API endpoint** — FastAPI wrapper for programmatic scanning
- **JSON/CSV export** — machine-readable findings output
- **Dashboard analytics** — trend charts across scans over time

---

## 21. Detection Quality Summary

| Check | Method | Coverage |
|-------|--------|----------|
| PII | Regex (12 patterns) + AI | Emails, phones, SSN, Aadhaar, PAN, passport, credit card, bank account, IBAN, IP, DOB |
| Confidentiality | Regex (14 patterns) + AI | OpenAI/Groq/Anthropic/AWS/GitHub/Google/Stripe keys, JWTs, passwords, DB URIs, private keys, salary |
| Encoding | Rules (6 checks) | Non-ASCII, multilingual scripts, OCR corruption, encoding confidence, non-UTF8, language |
| Abuse | Phrases (6) + Keywords (12) + AI | Threats, hate speech, harassment, violence incitement, illegal content, slurs, sexual harassment |

---

*Last updated: May 2026 — Stack: Groq (Free) + LangGraph + PyMuPDF + Streamlit + ReportLab + SQLite*
