# 🛡️ AI-Powered PDF Compliance Scanner

An AI-powered PDF compliance scanning pipeline using **LangGraph + Groq (Free AI) + Streamlit**.

## Features
- 🔴 **PII Detection** — Emails, phones, Aadhaar, credit cards, addresses
- 🔐 **Confidentiality** — API keys, passwords, trade secrets, M&A data
- 🔤 **Encoding Check** — UTF-8 validation, language detection
- ⚠️ **Abuse Detection** — Hate speech, harassment, unlawful content

## Quick Start

```bash
# 1. Clone and enter the project
git clone https://github.com/YOUR_USERNAME/pdf-compliance-scanner.git
cd pdf-compliance-scanner

# 2. Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Mac/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment
cp .env.example .env
# Edit .env and add your GROQ_API_KEY

# 5. Run the app
streamlit run app/main.py
```

## Project Structure

```
pdf-compliance-scanner/
├── app/                    # Streamlit UI
│   ├── main.py             # Entry point
│   ├── pages/
│   │   ├── 01_upload.py    # Upload & Scan page
│   │   ├── 02_rules.py     # Rules editor
│   │   └── 03_reports.py   # Reports browser
│   └── components/
├── pipeline/               # LangGraph pipeline
│   ├── state.py            # Typed state schema
│   ├── graph.py            # DAG builder & runner
│   └── nodes/
│       ├── ingest.py       # PDF text extraction
│       ├── pii_detector.py # PII detection
│       ├── confidentiality.py
│       ├── encoding_guard.py
│       ├── abuse_detector.py
│       ├── aggregator.py   # Result merger
│       └── report_builder.py
├── config/
│   ├── ai_provider.py      # AI factory (Groq/Gemini/Anthropic/Ollama)
│   ├── rules.py            # Rules loader/saver
│   ├── rules.json          # Default compliance rules
│   └── prompts/            # AI system prompts
├── storage/
│   └── database.py         # SQLite persistence
├── tests/                  # pytest suite
├── reports/                # Generated PDF reports (gitignored)
├── .github/workflows/ci.yml
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GROQ_API_KEY` | ✅ Yes | Groq free API key from console.groq.com |
| `AI_PROVIDER` | No | `groq` (default) / `gemini` / `anthropic` / `ollama` |
| `GROQ_MODEL` | No | `llama3-70b-8192` (default) |
| `GOOGLE_API_KEY` | Only if using Gemini | From aistudio.google.com |
| `ANTHROPIC_API_KEY` | Only if using Claude | From console.anthropic.com |

## Run Tests

```bash
pytest tests/ -v
```

## Docker

```bash
docker-compose up --build
# App available at http://localhost:8501
```

## Free AI Stack

| Service | API | Free Tier |
|---------|-----|-----------|
| Groq | `GROQ_API_KEY` | 14,400 req/day |
| Google Gemini | `GOOGLE_API_KEY` | 1,500 req/day (Flash) |
| Ollama | No key needed | 100% local |
