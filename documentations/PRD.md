# 🛡️ Product Requirements Document (PRD)
## AI-Powered PDF Compliance Scanner

**Version:** 1.0  
**Last Updated:** May 2026  
**Status:** Production-Ready  

---

## 1. Executive Summary

### 1.1 Product Overview

The **AI-Powered PDF Compliance Scanner** is a production-ready, open-source tool that automatically audits PDF documents for compliance violations. It combines deterministic regex engines with LLM-powered contextual analysis to flag PII, credentials, encoding issues, and abusive content — delivering a downloadable compliance report in seconds.

### 1.2 Problem Statement

Organizations handling PDFs (HR contracts, financial reports, client emails, legal documents) face growing compliance risks under **GDPR, HIPAA, and internal data governance policies**. Manual review is:
- ❌ Slow (hours per document)
- ❌ Error-prone (humans miss patterns)
- ❌ Expensive (requires legal/compliance staff)
- ❌ Inconsistent (subjective judgment)

### 1.3 Solution

Upload → Scan → Report. In under 30 seconds.

| Without This Tool | With This Tool |
|---|---|
| Manual page-by-page review | Automated full document scan |
| Days to audit 100 docs | Minutes |
| Inconsistent detection | 26+ regex patterns + AI |
| No audit trail | SQLite scan history + PDF report |
| Expensive compliance tools | **Free** (Groq API) |

---

## 2. Goals & Success Metrics

### 2.1 Primary Goals

1. **Detect compliance violations** with high precision (regex) + high recall (AI)
2. **Generate downloadable PDF reports** suitable for compliance audits
3. **Zero-dependency AI** — works free with Groq, or locally with Ollama
4. **Configurable** — rules editable via UI without code changes

### 2.2 Success Metrics

| Metric | Target |
|--------|--------|
| Scan time for 5-page doc | < 30 seconds |
| PII detection precision | > 90% (regex baseline) |
| UI page count | 3 (Upload, Rules, Reports) |
| Test coverage | Unit + integration tests |
| Zero secrets in git | ✅ enforced by .gitignore + CI |
| Free to run | ✅ Groq free tier: 14,400 req/day |

---

## 3. Target Users & Use Cases

### 3.1 Target Users

| User | Description |
|------|-------------|
| **Compliance Officers** | Need to audit documents for GDPR/HIPAA violations |
| **HR Teams** | Verifying employee documents don't contain exposed credentials |
| **Developers / DevSecOps** | Checking code exports or deployment docs for leaked API keys |
| **Legal Teams** | Reviewing contracts before sharing externally |
| **Researchers** | Dataset scrubbing before publishing |

### 3.2 Primary Use Cases

1. **PII Scrubbing** — Scan a PDF before emailing it; ensure no SSNs, Aadhaar IDs, or credit cards are present
2. **Credential Leak Check** — Verify exported configs/logs don't contain AWS keys or DB connection strings
3. **HR Document Review** — Check employment contracts for salary data or unlawful clauses
4. **Regulatory Audit** — Produce a documented PDF audit report for compliance review boards
5. **Document Trust Verification** — Incoming vendor docs checked before ingestion into internal systems

---

## 4. Functional Requirements

### 4.1 Core Features (MVP — v1.0 ✅ Implemented)

#### F1: PDF Ingestion
- Accept PDF uploads up to 50MB
- Extract text from every page using PyMuPDF
- Detect encoding per page using chardet
- Mark image-only pages without failing

#### F2: PII Detection
- Run 12 regex patterns (EMAIL, PHONE_INDIA, PHONE_US, SSN, AADHAAR, PAN_CARD, PASSPORT, CREDIT_CARD, BANK_ACCOUNT, IBAN, IP_ADDRESS, DATE_OF_BIRTH)
- Run Groq LLM for contextual PII not caught by regex
- Merge and deduplicate regex + AI findings
- Configurable confidence threshold (default 0.75)

#### F3: Confidentiality Detection
- Run 14 credential regex patterns (OpenAI/Groq/Anthropic/AWS/GitHub/Google/Stripe keys, JWTs, passwords, DB URIs, private key blocks, salary data)
- Auto-mask credential values in output (e.g., `sk-pro…r678`)
- Run AI for semantic detection: trade secrets, M&A data, financial forecasts, custom keywords
- Support user-defined custom keywords

#### F4: Encoding Guard
- 6 rule-based checks: NON_ASCII_CHARS, MULTILINGUAL_CONTENT, OCR_CORRUPTION, LOW_ENCODING_CONFIDENCE, NON_UTF8_ENCODING, NON_ALLOWED_LANGUAGE
- No AI required — pure deterministic checks
- Configurable language allowlist and thresholds

#### F5: Abuse Detection
- 6 phrase pattern categories: THREAT, HATE_SPEECH, HARASSMENT, VIOLENCE_INCITEMENT, ILLEGAL_CONTENT, SLUR
- 12 keyword signal patterns
- AI for nuanced/implied abuse
- Zero-tolerance override for `child_safety` and `terrorism`
- Abuse values stored as `[REDACTED]` — never verbatim

#### F6: Risk Aggregation
- Merge all 4 detection modules per page
- Dual-scoring: MAX(severity-based risk, flag-count-based risk)
- Document-level risk = MAX of all page risks
- 4 risk levels: `low | medium | high | critical` — never `unknown`

#### F7: PDF Report Generation
- ReportLab-generated compliance report
- Sections: Title block, Executive Summary, Risk Heatmap, Detailed Findings
- Color-coded severity rows; real confidence percentages
- Saved to `reports/` directory; downloadable from UI

#### F8: Compliance Rules Editor (UI)
- Toggle each detection category on/off
- Adjust confidence thresholds via sliders
- Add custom keywords
- Configure language allowlist
- Saves to `config/rules.json` — effective on next scan

#### F9: Scan History Browser (UI)
- List all past scans from SQLite
- Per-scan: metrics, download PDF report, view JSON summary, delete record

#### F10: Multi-Provider AI Support
- Groq (default, free — Llama 3)
- Google Gemini (free tier)
- Anthropic Claude (paid)
- Ollama (100% local, no key)
- Switchable via `AI_PROVIDER` env variable

### 4.2 Non-Functional Requirements

| Category | Requirement |
|----------|-------------|
| **Performance** | < 30s for 5-page PDF including AI calls |
| **Reliability** | AI failure is non-fatal; regex results always returned |
| **Security** | No plaintext secrets in DB or logs; credentials auto-masked |
| **Portability** | Docker-compose single-command deployment |
| **Testability** | pytest unit + integration suite with mocked AI |
| **CI/CD** | GitHub Actions: test + bandit security scan + docker build |

### 4.3 Out of Scope (v1.0)

- OCR for image-only PDF pages (no Tesseract)
- Async background scanning (large PDFs block UI)
- Batch upload (one PDF at a time)
- Physical PDF text redaction (UI masking only)
- API endpoint (no FastAPI wrapper)
- Compliance mode presets (GDPR / HIPAA / ISO27001)

---

## 5. System Architecture

### 5.1 High-Level Flow

```
User Browser
    │
    ▼
Streamlit UI (app/)
    │ run_pipeline()
    ▼
LangGraph DAG (pipeline/)
    │
    ├── ingest_node ──────────────────────────────────────────────────┐
    │   PyMuPDF → pages_text[]                                        │
    │                                                                 │
    ├──[PARALLEL]──────────────────────────────────────────────────── │
    │   ├── pii_node      (regex + Groq AI)                           │
    │   ├── confidentiality_node (regex + Groq AI)                    │
    │   ├── encoding_node (pure rules, no AI)                         │
    │   └── abuse_node    (phrases + keywords + Groq AI)              │
    │                                                                 │
    ├── aggregator_node                                               │
    │   Merge all → per-page risk scores → document summary           │
    │                                                                 │
    └── report_node                                                   │
        ReportLab → PDF saved to reports/                             │
    │
    ▼
SQLite (storage/compliance.db)
    │
    ▼
Streamlit Results UI
    Metrics + Redaction Table + Download Button
```

### 5.2 Technology Stack

| Layer | Technology | Reason |
|-------|-----------|--------|
| UI | Streamlit 1.35 | Python-native, rapid prototyping |
| AI Orchestration | LangGraph 0.2.14 | Typed DAG state, parallel node execution |
| LLM | Groq / Gemini / Anthropic / Ollama | Free tier available; pluggable |
| PDF Parsing | PyMuPDF (fitz) 1.24.5 | Fast, accurate, handles complex layouts |
| Report Generation | ReportLab 4.2 | Programmatic, color-coded PDF output |
| Database | SQLite (WAL mode) | Zero-config embedded persistence |
| Encoding Detection | chardet 5.2 + langdetect 1.0.9 | Reliable charset/language detection |
| Retry Logic | tenacity 8.3 | Exponential backoff on AI rate limits |
| Config | python-dotenv 1.0.1 | .env-based secret management |
| Security Scan | bandit 1.7.9 | Static OWASP analysis in CI |
| Testing | pytest 8.2 + pytest-mock | Unit + integration with mocked AI |

---

## 6. Data Model

### 6.1 Pipeline State (`PipelineState` TypedDict)

```
PipelineState
├── pdf_path: str             ← temp file path
├── pdf_name: str             ← original filename
├── upload_id: str            ← 8-char unique ID
├── total_pages: int
├── pages_text: List[PageText]
│   └── { page_num, text, char_count, detected_encoding, encoding_confidence, image_count }
├── pii_results: List[Dict]   ← from pii_node
├── confidential_results: List[Dict]  ← from confidentiality_node
├── encoding_results: List[Dict]      ← from encoding_node
├── abuse_results: List[Dict]         ← from abuse_node
├── page_results: List[PageResult]    ← from aggregator_node
│   └── { page_num, pii_flags, confidential_flags, encoding_flags, abuse_flags,
│          pii_risk, confidential_risk, encoding_risk, abuse_risk, overall_risk, total_flags }
├── summary: Dict             ← document-level statistics
├── compliance_rules: Dict    ← from config/rules.json
├── report_path: str | None   ← path to generated PDF
├── processing_complete: bool
└── errors: List[str]
```

### 6.2 SQLite Schema (`scans` table)

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | Auto-increment |
| upload_id | TEXT UNIQUE | 8-char scan identifier |
| pdf_name | TEXT | Original filename |
| scanned_at | TEXT | ISO timestamp |
| total_pages | INTEGER | Page count |
| total_flags | INTEGER | Total violations |
| highest_risk | TEXT | low/medium/high/critical |
| status | TEXT | completed / failed |
| result_json | TEXT | Full JSON result blob |
| report_path | TEXT | Path to generated PDF |

### 6.3 Flag Schema (per detection)

```json
{
  "category": "EMAIL",
  "value": "john@example.com",
  "context": "…sent to john@example.com for review…",
  "confidence": 0.97,
  "risk_level": "high",
  "detection_method": "regex"
}
```

---

## 7. API & Configuration

### 7.1 Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GROQ_API_KEY` | ✅ YES | — | Groq free API key from console.groq.com |
| `AI_PROVIDER` | No | `groq` | `groq` / `gemini` / `anthropic` / `ollama` |
| `GROQ_MODEL` | No | `llama3-70b-8192` | Groq model name |
| `GOOGLE_API_KEY` | If Gemini | — | From aistudio.google.com |
| `ANTHROPIC_API_KEY` | If Claude | — | From console.anthropic.com |
| `OLLAMA_MODEL` | If Ollama | `llama3` | Local model name |
| `MAX_FILE_SIZE_MB` | No | `50` | Upload limit |
| `MAX_PAGES` | No | `500` | Max pages per scan |
| `DEBUG` | No | `false` | Verbose logging |

### 7.2 Compliance Rules Config (`config/rules.json`)

All rules are editable via the UI Rules Editor page. Changes are written to disk and applied on the next scan.

```json
{
  "version": "1.0",
  "sensitivity": "high",
  "pii": { "enabled": true, "min_confidence": 0.75, ... },
  "confidentiality": { "enabled": true, "custom_keywords": [...], "min_confidence": 0.70 },
  "encoding": { "enabled": true, "allowed_languages": ["en"], "non_ascii_threshold": 5, ... },
  "abuse": { "enabled": true, "zero_tolerance_categories": ["child_safety", "terrorism"], ... },
  "reporting": { "generate_pdf_report": true, "context_window_chars": 150, ... }
}
```

---

## 8. Security & Privacy Design

| Concern | Mitigation |
|---------|-----------|
| API key exposure | `.env` gitignored; only `.env.example` committed |
| Credential leaks in logs | Secrets masked to `sk-pro…r678` before storage |
| Abuse content storage | Stored as `[REDACTED]` — never verbatim |
| Temp file cleanup | `try/finally` block deletes temp PDF after scan |
| SQLite integrity | WAL mode prevents corruption on concurrent access |
| Static security analysis | `bandit` runs in CI on every push |
| Dependency CVEs | `safety` check runs in CI |

---

## 9. Deployment Targets

| Target | Command | URL |
|--------|---------|-----|
| Local dev | `streamlit run app/main.py` | http://localhost:8501 |
| Docker | `docker-compose up --build` | http://localhost:8501 |
| Streamlit Cloud | Push to GitHub → deploy via share.streamlit.io | `*.streamlit.app` |
| Hugging Face Spaces | Push to HF Space repository | `huggingface.co/spaces/...` |

---

## 10. Testing Strategy

### 10.1 Test Layers

| Layer | File | Coverage |
|-------|------|---------|
| Unit: Encoding | `tests/test_nodes.py::TestEncodingNode` | 4 scenarios, no AI needed |
| Unit: Aggregator | `tests/test_nodes.py::TestAggregatorNode` | Risk scoring, flag counting |
| Unit: PII | `tests/test_nodes.py::TestPIINodeWithMockedAI` | Mocked AI + regex |
| Integration | `tests/test_pipeline.py` | Full pipeline with mocked AI |
| Fixtures | `tests/conftest.py` | Shared state + mock responses |

### 10.2 Run Commands

```bash
pytest tests/ -v                            # Full suite
pytest tests/test_nodes.py -k "Encoding"   # Fast, no AI
pytest tests/ --cov=pipeline --cov=config  # With coverage
```

---

## 11. Roadmap

### v1.1 (Near-term)
- [ ] OCR support (Tesseract integration for image-only pages)
- [ ] Async pipeline (background scan, non-blocking UI)
- [ ] JSON/CSV export of findings

### v1.2 (Medium-term)
- [ ] Redacted PDF export (physical text overlay via ReportLab)
- [ ] Batch upload (multiple PDFs per session)
- [ ] Compliance mode presets (GDPR / HIPAA / ISO27001)

### v2.0 (Future)
- [ ] FastAPI REST endpoint for programmatic scanning
- [ ] Dashboard analytics (trend charts across scans)
- [ ] Multi-user auth (streamlit-authenticator integration)
- [ ] Webhook notifications on critical findings

---

*Stack: Groq (Free) + LangGraph + PyMuPDF + Streamlit + ReportLab + SQLite*  
*Maintained by: Shahsmit075 · GitHub: github.com/Shahsmit075/pdf-compliance-scanner*
