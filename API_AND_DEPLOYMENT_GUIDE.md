# 🔑 API Keys & Deployment Guide
## AI-Powered PDF Compliance Scanner

---

## PART 1 — All APIs You Need

### ✅ REQUIRED (Mandatory to run the app)

| API | Service | Where to Get | Cost |
|-----|---------|-------------|------|
| `GROQ_API_KEY` | Groq (LLM inference) | https://console.groq.com → API Keys → Create | **FREE** — 14,400 req/day |

> [!IMPORTANT]
> **The app will NOT work without `GROQ_API_KEY`.** This is the only mandatory key.
> Sign up at https://console.groq.com with Google/GitHub, click **API Keys → Create API Key**, copy it once.

---

### 🔵 OPTIONAL (Only if you switch AI providers)

| API | Service | Where to Get | Cost |
|-----|---------|-------------|------|
| `GOOGLE_API_KEY` | Google Gemini Flash | https://aistudio.google.com → Get API Key | **FREE** — 1,500 req/day |
| `ANTHROPIC_API_KEY` | Claude (Sonnet/Haiku) | https://console.anthropic.com → API Keys | **PAID** — ~$3/M tokens |

> [!NOTE]
> You only need ONE provider. The default is Groq (free). To switch, change `AI_PROVIDER` in your `.env`.

---

## PART 2 — Where to Put Each API Key

### 2.1 Local Development (`.env` file)

```bash
# Step 1: Copy the example file
cp .env.example .env

# Step 2: Open .env and fill in your values
```

**Edit `.env`:**
```bash
# === REQUIRED ===
GROQ_API_KEY=gsk_YOUR_ACTUAL_GROQ_KEY_HERE

# === OPTIONAL — only if switching providers ===
GOOGLE_API_KEY=AIzaYOUR_GEMINI_KEY_HERE
ANTHROPIC_API_KEY=sk-ant-YOUR_CLAUDE_KEY_HERE

# === Provider Selection ===
AI_PROVIDER=groq                    # Options: groq | gemini | anthropic | ollama
GROQ_MODEL=llama3-70b-8192          # Options: llama3-70b-8192 | llama3-8b-8192 | mixtral-8x7b-32768

# === App Settings ===
MAX_FILE_SIZE_MB=50
MAX_PAGES=500
DEBUG=false
```

> [!CAUTION]
> Never commit `.env` to Git. It's already in `.gitignore`. Only `.env.example` should be committed.

---

### 2.2 Streamlit Community Cloud (Free Deployment)

**Location:** Streamlit Cloud dashboard → Your App → **Settings → Secrets**

Paste this into the Secrets text box:
```toml
GROQ_API_KEY = "gsk_YOUR_ACTUAL_GROQ_KEY_HERE"
AI_PROVIDER = "groq"
GROQ_MODEL = "llama3-70b-8192"

# Optional — only if using Gemini
# GOOGLE_API_KEY = "AIzaYOUR_GEMINI_KEY_HERE"
```

> [!IMPORTANT]
> Do NOT create `.streamlit/secrets.toml` in your repo — add secrets ONLY through the Streamlit Cloud dashboard UI.

---

### 2.3 GitHub Actions (CI/CD Secrets)

**Location:** GitHub repo → **Settings → Secrets and variables → Actions → New repository secret**

| Secret Name | Value | Used By |
|------------|-------|---------|
| `GROQ_API_KEY` | Your Groq key | `ci.yml` test job |

These are already referenced in `.github/workflows/ci.yml`:
```yaml
env:
  GROQ_API_KEY: ${{ secrets.GROQ_API_KEY }}
```

---

### 2.4 Docker / Docker Compose

**Option A — `.env` file (default)**
```bash
# Ensure .env exists with your GROQ_API_KEY, then:
docker-compose up --build
```

**Option B — Pass env var inline**
```bash
GROQ_API_KEY=gsk_your_key docker-compose up --build
```

---

### 2.5 Hugging Face Spaces

**Location:** Your HF Space → **Settings → Repository secrets → New secret**

| Secret Name | Value |
|------------|-------|
| `GROQ_API_KEY` | Your Groq API key |

---

## PART 3 — How to Start the Project Locally

### Step 1: Clone & Setup

```bash
git clone https://github.com/YOUR_USERNAME/pdf-compliance-scanner.git
cd pdf-compliance-scanner

python -m venv .venv
source .venv/bin/activate          # Mac/Linux
# .venv\Scripts\activate           # Windows

pip install -r requirements.txt
```

### Step 2: Configure API Keys

```bash
cp .env.example .env
# Open .env and paste your GROQ_API_KEY from https://console.groq.com
```

### Step 3: Run the App

```bash
streamlit run app/main.py
# Opens at http://localhost:8501
```

### Step 4: Generate a Test PDF (Optional)

```bash
python create_test_pdf.py
# Creates tests/fixtures/demo_violations.pdf
```

### Step 5: Run Tests

```bash
pytest tests/ -v

# Fast tests (no AI calls needed)
pytest tests/test_nodes.py -v -k "Encoding or Aggregator"
```

---

## PART 4 — Deploy to Streamlit Cloud (Free)

```bash
# 1. Push to GitHub
git add .
git commit -m "feat: complete PDF compliance scanner"
git push origin main

# 2. Go to https://share.streamlit.io
# 3. New app → select repo → branch: main → main file: app/main.py
# 4. Advanced settings → paste Secrets (see Section 2.2)
# 5. Click Deploy!
```

App live at: `https://your-app-name.streamlit.app`

---

## PART 5 — Deploy with Docker

```bash
docker-compose up --build        # Build and run
docker-compose up -d             # Run in background
docker-compose logs -f           # View logs
docker-compose down              # Stop
```

App at: `http://localhost:8501`

---

## PART 6 — Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GROQ_API_KEY` | ✅ **YES** | — | Groq free AI API key |
| `AI_PROVIDER` | No | `groq` | `groq`, `gemini`, `anthropic`, `ollama` |
| `GROQ_MODEL` | No | `llama3-70b-8192` | Groq model |
| `GOOGLE_API_KEY` | Only if Gemini | — | Google Gemini key |
| `ANTHROPIC_API_KEY` | Only if Claude | — | Anthropic key |
| `OLLAMA_MODEL` | Only if Ollama | `llama3` | Local model name |
| `MAX_FILE_SIZE_MB` | No | `50` | Max PDF size |
| `MAX_PAGES` | No | `500` | Max pages per scan |
| `DEBUG` | No | `false` | Debug logging |

---

## PART 7 — Troubleshooting

| Error | Fix |
|-------|-----|
| `No module named 'fitz'` | `pip install PyMuPDF==1.24.5` |
| `Groq 429 rate limit` | Switch to `llama3-8b-8192` or add `time.sleep(2)` |
| `JSON decode error` | Handled by `parse_json_response()` — check AI_PROVIDER |
| `ModuleNotFoundError` on Streamlit Cloud | `requirements.txt` must be in repo root |
| App can't find `GROQ_API_KEY` | Check `.env` locally or Streamlit Cloud secrets |

---

## PART 8 — Pre-Deployment Checklist

- [ ] `.env` created with real `GROQ_API_KEY`
- [ ] `.env` is NOT committed (check `.gitignore`)
- [ ] `requirements.txt` is in the repo root
- [ ] `app/main.py` is the Streamlit entry point
- [ ] `config/rules.json` is committed
- [ ] `reports/` is gitignored (auto-created at runtime)
- [ ] GitHub Actions secret `GROQ_API_KEY` is set
- [ ] Streamlit Cloud secrets are configured

---

*Stack: Groq (Free) + LangGraph + PyMuPDF + Streamlit + ReportLab + SQLite*
