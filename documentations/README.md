# 🛡️ AI-Powered PDF Compliance Scanner

> Upload any PDF → get a structured compliance report in seconds.  
> Detects PII, credentials, encoding issues, and abusive content using **regex + AI**.

[![CI](https://github.com/Shahsmit075/pdf-compliance-scanner/actions/workflows/ci.yml/badge.svg)](https://github.com/Shahsmit075/pdf-compliance-scanner/actions)
![Python](https://img.shields.io/badge/python-3.11-blue)
![License](https://img.shields.io/badge/license-MIT-green)

---

## What It Does

| Check | What Gets Flagged |
|-------|-------------------|
| 🔴 **PII Detection** | Emails, phones, Aadhaar, SSN, PAN card, passport, credit cards, bank accounts, IBAN, IP addresses, date of birth |
| 🔐 **Confidentiality** | API keys (OpenAI/Groq/Anthropic/AWS/GitHub/Google/Stripe), JWTs, passwords, DB URIs, private keys, salary data, trade secrets |
| 🔤 **Encoding Check** | Non-ASCII content, multilingual scripts, OCR corruption, non-UTF-8 encoding, disallowed languages |
| ⚠️ **Abuse Detection** | Threats, hate speech, harassment, violence incitement, illegal content, slurs |

**Output:** A downloadable PDF compliance report with an executive summary, page-by-page risk heatmap, and detailed findings table — with masked values for safe sharing.

---

## Quick Start

```bash
# 1. Clone
git clone https://github.com/Shahsmit075/pdf-compliance-scanner.git
cd pdf-compliance-scanner

# 2. Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Mac/Linux
# .venv\Scripts\activate   # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure API key (free)
cp .env.example .env
# Edit .env → set GROQ_API_KEY=gsk_your_key_from_console.groq.com

# 5. Run
streamlit run app/main.py
# Opens at http://localhost:8501
```

---

## Documentation

| Document | Purpose |
|----------|---------|
| [README.md](README.md) | ← You are here — setup & overview |
| [PRD.md](PRD.md) | Product Requirements Document — what, why, goals |
| [CODE_DOCUMENTATION.md](CODE_DOCUMENTATION.md) | Architecture, module map, data flow, APIs |
| [DESIGN_PHILOSOPHY.md](DESIGN_PHILOSOPHY.md) | Why decisions were made — the reasoning |
| [features_listed.md](features_listed.md) | Complete rebuild spec in prompt format |
| [API_AND_DEPLOYMENT_GUIDE.md](API_AND_DEPLOYMENT_GUIDE.md) | API keys setup + all deployment targets |
| [PROJECT_EXPLANATION.md](PROJECT_EXPLANATION.md) | Detailed technical deep-dive |

---

## Project Structure

```
pdf-compliance-scanner/
├── app/                        ← Streamlit UI
│   ├── main.py                 ← Entry point (home page)
│   ├── pages/
│   │   ├── 01_upload.py        ← Upload & Scan
│   │   ├── 02_rules.py         ← Rules Editor
│   │   └── 03_reports.py       ← Scan History
│   ├── components/             ← Reusable widgets
│   └── utils/redaction.py      ← PII masking
│
├── pipeline/                   ← LangGraph pipeline
│   ├── state.py                ← Typed state schema
│   ├── graph.py                ← DAG builder
│   └── nodes/
│       ├── ingest.py           ← PDF text extraction
│       ├── pii_detector.py     ← PII (regex + AI)
│       ├── confidentiality.py  ← Credentials (regex + AI)
│       ├── encoding_guard.py   ← Encoding (rules only)
│       ├── abuse_detector.py   ← Abuse (phrases + AI)
│       ├── aggregator.py       ← Risk scoring
│       └── report_builder.py   ← PDF generation
│
├── config/
│   ├── ai_provider.py          ← AI factory (Groq/Gemini/Anthropic/Ollama)
│   ├── rules.py                ← Rules loader/saver
│   ├── rules.json              ← Default compliance rules
│   └── prompts/                ← AI system prompts
│
├── storage/database.py         ← SQLite (scan history)
├── tests/                      ← pytest suite
├── .github/workflows/ci.yml    ← CI: test + security + docker
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GROQ_API_KEY` | ✅ **YES** | — | Free key from [console.groq.com](https://console.groq.com) |
| `AI_PROVIDER` | No | `groq` | `groq` / `gemini` / `anthropic` / `ollama` |
| `GROQ_MODEL` | No | `llama3-70b-8192` | Groq model name |
| `GOOGLE_API_KEY` | If Gemini | — | From [aistudio.google.com](https://aistudio.google.com) |
| `ANTHROPIC_API_KEY` | If Claude | — | From [console.anthropic.com](https://console.anthropic.com) |
| `MAX_FILE_SIZE_MB` | No | `50` | PDF upload limit |
| `MAX_PAGES` | No | `500` | Max pages per scan |
| `DEBUG` | No | `false` | Verbose logging |

---

## Free AI Options

| Provider | Env Key | Free Tier | Speed |
|----------|---------|-----------|-------|
| **Groq** (default) | `GROQ_API_KEY` | 14,400 req/day | ~1s/call |
| Google Gemini | `GOOGLE_API_KEY` | 1,500 req/day | ~2s/call |
| Ollama (local) | None needed | Unlimited | Varies |

A 10-page document uses ~30 AI calls (3 AI nodes × 10 pages).

---

## Run Tests

```bash
# Full suite
pytest tests/ -v

# Fast tests (no AI calls needed)
pytest tests/test_nodes.py -k "Encoding or Aggregator" -v

# With coverage
pytest tests/ --cov=pipeline --cov=config
```

---

## Docker

```bash
# Start
docker-compose up --build

# Background
docker-compose up -d

# Stop
docker-compose down
```

App at: **http://localhost:8501**

---

## Deploy to Streamlit Cloud (Free)

1. Push repo to GitHub (no `GROQ_API_KEY` in any committed file)
2. Go to [share.streamlit.io](https://share.streamlit.io) → New app
3. Select repo → branch: `main` → main file: `app/main.py`
4. Advanced Settings → Secrets → paste:
   ```toml
   GROQ_API_KEY = "gsk_your_actual_key"
   AI_PROVIDER = "groq"
   ```
5. Click **Deploy**

---

## How It Works (30-second version)

```
PDF uploaded
    │
    ▼
ingest_node ──────────────────────────────────────────────────────┐
PyMuPDF extracts text from each page                              │
    │                                                             │
    ├─── pii_node (regex + AI) ──────────────────────────────┐   │
    ├─── confidentiality_node (regex + AI) ──────────────────┤   │
    ├─── encoding_node (pure rules) ─────────────────────────┤   │
    └─── abuse_node (phrases + AI) ──────────────────────────┘   │
                         │                                        │
                   aggregator_node                                │
          Merge all results; score risk per page                  │
                         │                                        │
                   report_node                                    │
          ReportLab → PDF saved to reports/                       │
                         │                                        │
                   SQLite DB + Streamlit UI                       │
         Show metrics, redaction table, download button           │
```

**Detection is always Regex-first, AI-second.** If AI fails (rate limits, network), regex results are returned — the scan never fails silently.

---

## Troubleshooting

| Error | Fix |
|-------|-----|
| `No module named 'fitz'` | `pip install PyMuPDF==1.24.5` |
| `Groq 429 rate limit` | Switch `GROQ_MODEL=llama3-8b-8192` or wait |
| `JSON decode error` | Handled automatically by `parse_json_response()` |
| `ModuleNotFoundError` on Streamlit Cloud | Ensure `requirements.txt` is in repo root |
| `App can't find GROQ_API_KEY` | Check `.env` locally or Streamlit Cloud Secrets |

---

## Tech Stack

| Layer | Tech |
|-------|------|
| UI | Streamlit 1.35 |
| AI Orchestration | LangGraph 0.2.14 |
| LLM (default) | Groq Llama3-70B (free) |
| PDF Parsing | PyMuPDF 1.24.5 |
| Report Generation | ReportLab 4.2 |
| Database | SQLite (WAL mode) |
| Retry Logic | tenacity (exponential backoff) |
| CI | GitHub Actions |
| Container | Docker + docker-compose |

---

*v1.0 · May 2026 · Stack: Groq + LangGraph + PyMuPDF + Streamlit + ReportLab + SQLite*
