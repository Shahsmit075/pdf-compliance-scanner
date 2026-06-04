# LLM Prompts — Architecture Diagram & PPT Generation
**PDF Compliance Scanner | Sigmoid Bangalore | May–Jun 2026**

---

## PROMPT 1 — Architecture Diagram (Gemini / Any Image-Gen or Diagram-Gen LLM)

> **Usage**: Paste this into Gemini (gemini.google.com), Claude, or any diagram-generation tool (Eraser.io, Mermaid Live, diagrams.net AI, etc.)
> If using a text-only LLM, ask it to generate a Mermaid diagram code block, then render at https://mermaid.live

---

```
You are an expert technical diagram designer. Create a detailed, visually rich system architecture diagram for the following software project.

────────────────────────────────────────────────────────────────
PROJECT: PDF Compliance Scanner
TEAM: Shahsmit075 × ArpitMishra2 | Sigmoid Bangalore | May–Jun 2026
CAPSTONE: Option A — Intelligent Document Compliance Pipeline (Enterprise-Enhanced)
────────────────────────────────────────────────────────────────

DIAGRAM REQUIREMENTS:
- Style: Dark-mode, tech/cyberpunk aesthetic. Background: near-black (#0D0D0D).
  Primary accent colour: amber/gold (#E8A838). Secondary: ice blue (#38C8E8).
  Risk colours: green (low), yellow (medium), orange (high), red (critical).
- Layout: Top-to-bottom flow with clearly separated horizontal layers/swim lanes.
- Include ALL components listed below. Do NOT omit any.
- Each component should be a labelled box/node with its technology name.
- Show directional arrows between components indicating data flow.
- Group related components inside labelled swim lanes or bounding boxes.
- Use icons where possible (PDF icon, database cylinder, cloud icon, etc.).
- Make it presentation-quality — suitable for a Demo Day slide.

────────────────────────────────────────────────────────────────
ARCHITECTURE LAYERS (top to bottom):
────────────────────────────────────────────────────────────────

LAYER 1 — USER INTERFACE (Streamlit Web App — port 8501)
  - Module 01: Upload & Scan (PDF input, AI provider selector, live progress)
  - Module 02: Rules Configuration (JSON rules editor)
  - Module 03: PDF Scan Reports (history, download)
  - Module 04: Data Source Registry (10 connector types, alert config)
  - Module 05: Data Source Scan (trigger agent pipeline)
  - Module 06: DS Scan Reports (risk trends, compliance %)
  - Module 07: AI Copilot (RAG chat interface)
  - Module 08: Telemetry & Analytics (Plotly charts, KPI cards)
  UI Design: "Noir Amber" dark theme — Space Mono + JetBrains Mono fonts

LAYER 2 — PDF COMPLIANCE PIPELINE (LangGraph DAG)
  Entry: PDF Upload
  Node 1: INGEST (PyMuPDF — text extraction, encoding detection via chardet)
  Fan-out (parallel): 4 nodes run simultaneously:
    Node 2a: PII DETECTOR (12 pattern types — regex + AI verify)
              Detects: Email, Phone, Aadhaar, SSN, Credit Card, Passport, PAN,
              DOB, IP, Address, Name, GPS
    Node 2b: CONFIDENTIALITY CHECK (15 credential patterns — regex + AI semantic)
              Detects: AWS keys, GitHub tokens, Passwords, PEM keys, JWT,
              Salary, Financial data, Trade secrets, Custom keywords
    Node 2c: ENCODING GUARD (6 check types — rule-based, no AI)
              Checks: UTF-8 validation, Non-ASCII density, Language compliance,
              OCR corruption, Encoding confidence, Multi-script detection
    Node 2d: ABUSE DETECTOR (3-layer detection)
              Detects: Hate speech, Threats, Sexual content, Harassment,
              Illegal content, Terrorism (zero-tolerance)
  Fan-in:
    Node 3: AGGREGATOR (merge results → PageResult per page → document summary)
    Node 4: REPORT BUILDER (ReportLab → PDF report + JSON report)
  Observability: @observe decorator → Langfuse trace per pipeline run

LAYER 3 — DATA SOURCE AGENT PIPELINE (3 LangGraph Agents)
  Agent 1: METADATA AGENT
    → Connect to data source
    → Extract schema (tables, columns, data types, row counts)
    → Hash schema (SHA-256)
    → Compare to previous snapshot in SQLite
    → Run CHANGE ENGINE if schema changed
    Change Engine detects: new_table, dropped_table, new_column, dropped_column,
    type_change, row_count_spike (>300%), row_count_drop (>80%)

  Agent 2: COMPLIANCE AGENT
    Node A: CLASSIFY COLUMNS (Rules Engine — 25+ regex patterns)
             Covers: PII_EMAIL, PII_PHONE, PII_SSN, PII_PASSPORT, PCI_CARD_NUMBER,
             PCI_CVV, PHI_DIAGNOSIS, PHI_MRN, CONFIDENTIAL_SALARY,
             CONFIDENTIAL_API_KEY, CONFIDENTIAL_PASSWORD, and 15+ more
    Node B: AI ENHANCE (AI classifies ambiguous/unclassified columns, confidence ≥ 0.70)
    Node C: COMPUTE RISK SUMMARY (numeric score 0–100, compliance %)
    Node D: SAVE RESULTS (persist to SQLite)

  Agent 3: ALERT AGENT
    → Check scan risk level vs. configured thresholds
    → Dispatch to: Slack Webhook | Email SMTP | Generic Webhook
    → Log to alert_history table

LAYER 4 — INTELLIGENCE LAYER
  - Rules Engine: 25+ regex column classifiers (PII / PCI / PHI / Confidential / Internal)
  - Change Engine: structural + statistical schema diff
  - Risk Scorer: severity-weighted score (critical=25, high=10, medium=3, low=1 per violation)

LAYER 5 — RAG LAYER (ChromaDB — Persistent Local Vector Store)
  - Indexed after every data source scan
  - Document format: source name + entity + risk type + evidence + recommendation
  - Metadata filters: source_id, scan_id, check_type, risk_level
  - Used by: AI Copilot (Module 07) — cosine similarity search, top-5 results

LAYER 6 — AI PROVIDER LAYER (Runtime-Switchable via env var AI_PROVIDER)
  - Groq Llama 3.3-70B (default, free, fast — ~400-800ms)
  - Google Gemini 1.5 Flash (free tier)
  - Anthropic Claude Sonnet (paid)
  - Ollama (local, air-gapped)
  Universal call_ai() function with: Tenacity retry (5 attempts, exponential backoff 2s→60s)

LAYER 7 — STORAGE LAYER
  SQLite (WAL mode — compliance.db) — 12 tables:
    PDF tables: scans
    DS tables: data_sources, metadata_snapshots, column_metadata,
               detected_changes, ds_scan_runs, ds_scan_results,
               risk_trends, compliance_drift, alert_configs, alert_history
  ChromaDB: compliance_knowledge collection (persistent)
  File system: reports/ (PDF + JSON per scan)

LAYER 8 — CONNECTOR LAYER (Lazy-Loaded, 10 connectors)
  Databases:      PostgreSQL, MySQL, MongoDB, SQL Server
  Cloud Storage:  AWS S3, Azure ADLS Gen2, Google Cloud Storage
  Data Warehouses: Snowflake, BigQuery, Databricks
  All implement: BaseConnector (connect, disconnect, test_connection, get_metadata)

LAYER 9 — OBSERVABILITY
  Langfuse Cloud:
    - Full trace per PDF scan (session_id = upload_id)
    - Each call_ai() → Langfuse Generation (tokens in/out, model, latency)
    - Content redacted in traces (<redacted>) — privacy-first
    - get_client().flush() after pipeline completes

LAYER 10 — DEPLOYMENT
  Local: python .venv + streamlit run app/main.py
  Docker: python:3.11-slim + gcc + libfreetype6-dev, EXPOSE 8501, HEALTHCHECK
  Production (AWS): ECS Fargate → ECR image → EFS (SQLite + ChromaDB persist)
                    S3 → Lambda → SQS → ECS Fargate pipeline
                    Secrets: AWS Secrets Manager | Logs: CloudWatch

────────────────────────────────────────────────────────────────
KEY DATA FLOWS TO SHOW WITH ARROWS:
────────────────────────────────────────────────────────────────
1. User → Streamlit UI → Pipeline → SQLite → Report → User (download)
2. PDF → ingest → [pii ‖ confidentiality ‖ encoding ‖ abuse] → aggregate → report
3. Streamlit UI → Metadata Agent → Compliance Agent → ChromaDB → Alert Agent → Slack
4. User question → AI Copilot → ChromaDB (RAG) + SQLite (context) → AI Provider → Answer
5. Every AI call → Langfuse trace (bidirectional with dashed line)
6. Data source → Connector → Schema → Change Engine → SQLite snapshots

────────────────────────────────────────────────────────────────
BADGES / ANNOTATIONS TO ADD:
────────────────────────────────────────────────────────────────
- "4 PARALLEL CHECKS" annotation on the fan-out section
- "ZERO-TOLERANCE" badge on terrorism/CSAM in abuse detector
- "RUNTIME-SWITCHABLE" badge on AI Provider layer
- "PERSISTENT" badge on ChromaDB and EFS
- "LANGFUSE TRACED" badge/overlay on AI Provider layer
- Risk level colour legend: GREEN=low, YELLOW=medium, ORANGE=high, RED=critical
- Token count flow annotation between AI Provider and Langfuse

OUTPUT: A single, full-width architecture diagram in landscape orientation.
Make it detailed enough that a technical interviewer can ask about any component
and find it in the diagram. Presentation-quality, dark background, amber+blue accents.
```

---

## PROMPT 2 — PowerPoint Presentation (PPT Generator LLM)

> **Usage**: Paste this into any PPT-generation LLM (Gamma.app, Beautiful.ai AI, Tome, Slidesgo AI, or a direct ChatGPT/Claude prompt for slide-by-slide content).
> The user will apply their own professional template. This prompt generates the CONTENT and STRUCTURE only.
> Tell the LLM: "Generate slide-by-slide content. For each slide: give the TITLE, SUBTITLE (optional), KEY POINTS (bullets), and any SPEAKER NOTES."

---

```
You are an expert technical presentation writer specialising in AI/ML engineering showcases for academic Demo Days.

Generate a complete, slide-by-slide PowerPoint presentation for the project described below.
The user will apply their own professional visual template — do NOT describe colours, fonts, or layouts.
Focus entirely on CONTENT: titles, subtitles, bullet points, data, and speaker notes.

────────────────────────────────────────────────────────────────
PROJECT CONTEXT
────────────────────────────────────────────────────────────────
Project Name: PDF Compliance Scanner
Team: Shahsmit075 × ArpitMishra2
Programme: Sigmoid Bangalore | GenAI for Data Engineering | Batch May–Jun 2026
Capstone Track: Option A — Intelligent Document Compliance Pipeline (Enterprise-Enhanced)
Audience: Technical assessors, data engineering practitioners, programme faculty
Demo Day Format: 10 minutes total — 7 min live demo + 3 min Q&A
Assessment Criteria (weighted):
  - Innovation & Creativity: 30%
  - Technical Execution: 30%
  - GenAI Application Depth: 20%
  - Business Value Articulation: 10%
  - Presentation Quality: 10%

────────────────────────────────────────────────────────────────
FULL PROJECT SPECIFICATION (use this as your ONLY source of truth)
────────────────────────────────────────────────────────────────

WHAT THE SYSTEM DOES:
An AI-powered compliance scanner with two modes:
1. PDF Document Scanner: Uploads any PDF → runs 4 parallel AI+regex checks → scores risk per page → generates downloadable audit report in <30 seconds.
2. Data Source Scanner: Connects to any of 10 database/cloud/warehouse types → classifies every column for PII/PHI/PCI violations → detects schema changes → tracks compliance drift over time.

Both modes share: an AI Copilot (RAG-powered chat), a Telemetry & Analytics dashboard, an Alert System (Slack/Email/Webhook), and LLM observability via Langfuse.

PROBLEM STATEMENT:
Enterprise organisations handle thousands of PDFs and data schemas containing sensitive data: Aadhaar numbers, AWS credentials, salary figures, hate speech. Manual review takes hours per document, misses patterns, and cannot scale. Compliance auditors need instant, evidence-backed, risk-rated answers.

TECH STACK:
- UI: Streamlit (Noir Amber dark theme) — 8 modules/pages
- Orchestration: LangGraph (DAG-based pipeline)
- PDF Parsing: PyMuPDF (fitz)
- Report Generation: ReportLab
- AI Providers (runtime-switchable): Groq Llama 3.3-70B (default), Google Gemini 1.5 Flash, Anthropic Claude Sonnet, Ollama (local/air-gapped)
- Vector Store: ChromaDB (persistent, cosine similarity)
- Database: SQLite (WAL mode) — 12 tables
- Observability: Langfuse (full LLM tracing, token counts)
- Retry: Tenacity (5 attempts, exponential backoff 2s→60s)
- Encoding: chardet + langdetect
- Charts: Plotly
- Containerization: Docker (python:3.11-slim)
- Data Source Connectors: PostgreSQL, MySQL, MongoDB, SQL Server, AWS S3, Azure ADLS Gen2, GCS, Snowflake, BigQuery, Databricks

PDF PIPELINE (LangGraph DAG):
ingest → [pii_check ‖ confidentiality ‖ encoding_check ‖ abuse_check] → aggregate → build_report
(4 compliance nodes run in TRUE PARALLEL — key performance feature)

DETECTION CAPABILITIES:
- PII Detector: 12 pattern types (Email, Phone, Aadhaar, SSN, Credit Card, Passport, PAN, DOB, IP, Address, Name, GPS) — dual-engine: regex speed + AI semantic verification
- Confidentiality: 15 credential patterns (AWS keys, GitHub tokens, Passwords, PEM keys, JWT, Salary, Financial data, Trade secrets, Custom keywords)
- Encoding Guard: 6 rule-based checks (UTF-8 validation, Non-ASCII density, Language compliance, OCR corruption, Encoding confidence, Multi-script detection) — no AI, deterministic
- Abuse Detector: 3-layer detection across 6 categories — hate speech, threats, sexual content, harassment, illegal content, terrorism (zero-tolerance for terrorism/CSAM)

CONFIDENCE SCORING:
Every flag carries a confidence score 0.0–1.0. Risk levels: CRITICAL / HIGH / MEDIUM / LOW.
AI findings below 0.70 confidence are automatically rejected.

DATA SOURCE AGENTS (3 LangGraph Agents):
1. Metadata Agent: Connects → extracts schema → SHA-256 hash → compares to previous snapshot → runs Change Engine on diff
2. Compliance Agent: classify_columns (25+ regex rules) → ai_enhance (AI for ambiguous) → compute_risk_summary → save_results
3. Alert Agent: checks thresholds → dispatches Slack/Email/Webhook → logs to alert_history

RULES ENGINE (25+ named column classifiers):
PII: PII_EMAIL (0.96), PII_PHONE (0.93), PII_SSN (0.98 — critical), PII_PASSPORT (0.97 — critical), PII_DOB (0.95), PII_NAME (0.85), PII_ADDRESS (0.88), PII_IP (0.90), PII_GENDER (0.80), PII_RACE (0.82)
PCI: PCI_CARD_NUMBER (0.99 — critical), PCI_CVV (0.99 — critical), PCI_EXPIRY (0.90)
PHI: PHI_DIAGNOSIS (0.88 — critical), PHI_MEDICATION (0.87 — critical), PHI_LAB_RESULT (0.85 — critical), PHI_MRN (0.94 — critical)
Confidential: CONFIDENTIAL_PASSWORD (0.99 — critical), CONFIDENTIAL_API_KEY (0.99 — critical), CONFIDENTIAL_SALARY (0.92), CONFIDENTIAL_FINANCIAL (0.82), CONFIDENTIAL_CREDENTIALS (0.97)
Internal: INTERNAL_EMPLOYEE_ID (0.90), INTERNAL_USER_ID (0.70)

CHANGE ENGINE detects: new_table (high), dropped_table (critical), new_column (high), dropped_column (high), type_change (medium), row_count_spike >300% (medium), row_count_drop >80% with >1k rows (high)

RISK SCORE FORMULA:
risk_score = min(100, Σ severity_weights)
critical=25, high=10, medium=3, low=1 per violation
compliance_pct = (1 - flagged_columns / total_columns) × 100

AI COPILOT (Module 07):
RAG pipeline: User question → ChromaDB similarity search (top-5) + SQLite live context (sources, recent scans, risk trends, schema changes) → AI generation → markdown answer
Source scoping: filter by registered data source or ask about all sources

TELEMETRY (Module 08):
Tracks per scan: total_tokens, execution_time_sec, total_flags, highest_risk, ai_provider, scanned_at
4 Plotly charts: Scans over time, Token consumption by date, Risk profile frequency, AI provider distribution
3 KPIs: Total scans, Avg latency, Total tokens

ALERT SYSTEM:
Channels: Slack (Incoming Webhook), Email (SMTP+STARTTLS), Generic Webhook
Config: trigger_risk_levels (multi-select), cooldown_minutes (suppress duplicates)
Audit trail: every alert logged to alert_history table

LANGFUSE OBSERVABILITY:
@observe decorator wraps the entire pipeline run as a Langfuse Trace (session_id = upload_id)
Every call_ai() → Langfuse Generation (model name, token in/out, latency, status)
Content is <redacted> in traces — privacy-first. Only token counts and model metadata logged.

SECURITY TRADEOFFS:
- API keys in .env (git-ignored); never hardcoded
- AI provider option: Ollama = fully local, zero data leaves machine
- Connector credentials stored as plain JSON in SQLite (prototype; production → AWS Secrets Manager)
- No auth layer (local tool; add streamlit-authenticator for multi-user)
- Langfuse tracing enabled (content redacted)

DEPLOYMENT:
Local: streamlit run app/main.py
Docker: python:3.11-slim, EXPOSE 8501, HEALTHCHECK on /_stcore/health
Production AWS: ECS Fargate + ECR + EFS (SQLite+ChromaDB persistence) + S3+Lambda+SQS trigger

ENHANCEMENT LAYERS IMPLEMENTED:
A1 — Document Lineage: UUID per scan, timestamp, provider, full JSON stored ✅
A2 — Confidence Scoring: every flag has confidence 0.0–1.0; AI below 0.70 rejected ✅
A4 — Remediation Suggestions: every flagged column has specific remediation text ✅
A5 — Operations Dashboard: Module 08 with 4 charts + KPIs ✅
B1 — LLM Observability: Langfuse tracing on every AI call ✅
B3 — Alert Dispatch: Slack/Email/Webhook with threshold + cooldown config ✅
B5 — Pattern Memory: ChromaDB indexes all findings; RAG Copilot retrieves them ✅
C6 — Source Attribution: ChromaDB metadata tags (source_id, scan_id, risk_level) ✅

KEY NUMBERS:
- 12 PII pattern types
- 15 credential patterns
- 25+ column classification rules
- 4 parallel compliance checks per PDF
- 10 data source connectors
- 12 SQLite tables
- 4 AI providers (runtime-switchable)
- 0 hardcoded API keys
- <30 seconds for a typical PDF scan

────────────────────────────────────────────────────────────────
SLIDE STRUCTURE — Generate all slides below
────────────────────────────────────────────────────────────────

Generate the following slides in order. For each slide provide:
  SLIDE N: [TITLE]
  Subtitle: (optional short subtitle)
  Content: (bullet points, tables, or structured text)
  Speaker Notes: (what to say out loud — 2–4 sentences)

─────────
SLIDE 1: TITLE SLIDE
─────────
Project name, team names, programme, batch, date.
Speaker note: Quick intro of team and what you built.

─────────
SLIDE 2: THE PROBLEM — "Data Doesn't Stay Clean"
─────────
Make this emotionally resonant and business-relevant.
Cover: scale of problem (PDFs + databases in enterprise), cost of non-compliance, manual review failures.
Include 2–3 concrete examples of what slips through: Aadhaar in contracts, AWS keys in shared docs, hate speech in policy documents.
Speaker note: Set the stakes — why this matters to a real enterprise.

─────────
SLIDE 3: OUR SOLUTION — "30 Seconds to Compliant"
─────────
One-liner solution statement.
Two operating modes (PDF Scanner + Data Source Scanner).
Shared infrastructure: AI Copilot, Telemetry, Alerts.
Emphasis: end-to-end, production-grade, not a toy.
Speaker note: Position as a "detective + advisor" — finds AND fixes.

─────────
SLIDE 4: SYSTEM ARCHITECTURE — HIGH LEVEL
─────────
Describe the architecture diagram as a structured list of layers (since template handles visuals, describe it textually as content for an architecture diagram slide).
Layers: UI → Pipeline → Agents → Intelligence → RAG → AI Providers → Storage → Connectors → Observability → Deployment.
Key message: Every layer is production-grade, not a prototype workaround.
Speaker note: Walk through the flow top-to-bottom in 45 seconds.

─────────
SLIDE 5: PDF COMPLIANCE PIPELINE — LangGraph DAG
─────────
Show the pipeline: ingest → [4 parallel nodes] → aggregate → report
For each of the 4 parallel nodes, list what it detects (brief).
Key technical highlight: TRUE PARALLELISM via LangGraph — 4 checks simultaneously.
Performance: <30 seconds for a typical multi-page PDF.
Speaker note: Emphasise the parallel execution — this is the core performance win.

─────────
SLIDE 6: DETECTION CAPABILITIES
─────────
Four-quadrant layout (or four sections):
  PII (12 types): Email, Phone, Aadhaar, SSN, Credit Card, Passport, PAN, DOB, IP, Address, Name, GPS
  CONFIDENTIALITY (15 types): AWS keys, GitHub tokens, Passwords, PEM keys, JWT, Salary, Financial, Trade secrets
  ENCODING (6 checks): UTF-8, Non-ASCII density, Language compliance, OCR corruption, Encoding confidence, Multi-script
  ABUSE (6 categories + 3 layers): Hate speech, Threats, Sexual content, Harassment, Illegal, Terrorism (zero-tolerance)
Key message: "No missed detection — dual engine (regex speed + AI semantic verification)"
Speaker note: Dual-engine is the differentiator — regex catches obvious, AI catches nuanced.

─────────
SLIDE 7: CONFIDENCE SCORING & RISK LEVELS
─────────
Confidence: every flag gets 0.0–1.0 score. AI findings < 0.70 are auto-rejected.
Risk levels: CRITICAL / HIGH / MEDIUM / LOW with examples for each.
Risk score formula: severity-weighted sum (critical=25, high=10, medium=3, low=1), capped at 100.
Compliance %: (1 - flagged/total) × 100.
Redaction preview: show before/after masking examples (Email masked, PAN masked, AWS key masked).
Speaker note: Confidence scoring is what makes this enterprise-ready — no "AI said so" without evidence.

─────────
SLIDE 8: DATA SOURCE SCANNER — 10 CONNECTORS
─────────
Show the 3 categories of connectors with logos/names:
  Databases: PostgreSQL, MySQL, MongoDB, SQL Server
  Cloud Storage: AWS S3, Azure ADLS Gen2, Google Cloud Storage
  Data Warehouses: Snowflake, BigQuery, Databricks
3-stage agent pipeline: Metadata Agent → Compliance Agent → Alert Agent.
Change Engine: 7 types of schema changes detected.
Speaker note: This is beyond the core requirement — live database scanning, not just PDFs.

─────────
SLIDE 9: RULES ENGINE — 25+ COLUMN CLASSIFIERS
─────────
Table or grouped list of classification categories:
  PII: SSN (0.98 critical), Passport (0.97 critical), Email (0.96), DOB (0.95)...
  PCI: Card Number (0.99 critical), CVV (0.99 critical)
  PHI: Diagnosis (0.88 critical), MRN (0.94 critical)
  Confidential: Password (0.99 critical), API Key (0.99 critical), Salary (0.92)
Key message: Pattern confidence built-in. AI enhances only what rules miss.
Speaker note: This is a production-grade rules engine, not hardcoded strings.

─────────
SLIDE 10: AI COPILOT — RAG-POWERED COMPLIANCE CHAT
─────────
3-layer query pipeline: ChromaDB RAG (top-5 similar findings) → SQLite live context → AI generation.
Source scoping: ask about one DB or all.
Example Q&A pairs:
  Q: "What PII columns need immediate encryption?" → A: lists specific columns with risk + recommendation
  Q: "What changed in our schema this week?" → A: lists new/dropped columns with severity
  Q: "Show compliance score for Production Postgres" → A: gives score + trend
Speaker note: This transforms from a scan tool to a compliance advisor — the difference between $50K and $500K.

─────────
SLIDE 11: ALERT SYSTEM & MONITORING
─────────
Alert channels: Slack Webhook, Email (SMTP), Generic Webhook.
Config: choose risk threshold (critical/high/medium), cooldown minutes.
Sample alert message format (Slack).
Audit trail: all alerts logged to alert_history table.
Module 08 Telemetry: 4 Plotly charts + 3 KPI cards (total scans, avg latency, total tokens).
Speaker note: Enterprises don't watch dashboards — alerts come to Slack. No alert = no trust.

─────────
SLIDE 12: LLM OBSERVABILITY — LANGFUSE INTEGRATION
─────────
What is traced: every pipeline run → Langfuse Trace (session_id = upload_id).
Every AI call → Langfuse Generation (model, tokens in/out, latency, error status).
Privacy: content is <redacted> in traces — only token counts and model name logged.
Supported models: Groq Llama 3.3-70B (default), Gemini 1.5 Flash, Claude Sonnet, Ollama.
Runtime switching: AI_PROVIDER env var, changeable from UI dropdown per scan.
Key message: "No autonomous AI without observability."
Speaker note: Most prototypes have zero observability. We traced every token.

─────────
SLIDE 13: ENTERPRISE ENHANCEMENT LAYERS DELIVERED
─────────
Table format:
  A1 — Document Lineage: UUID + timestamp + full JSON per scan ✅
  A2 — Confidence Scoring: 0.0–1.0 per flag; AI < 0.70 auto-rejected ✅
  A4 — Remediation Suggestions: specific fix text per flagged column ✅
  A5 — Operations Dashboard: 4 Plotly charts + 3 KPIs ✅
  B1 — LLM Observability: Langfuse tracing on every AI call ✅
  B3 — Alert Dispatch: Slack/Email/Webhook with threshold + cooldown ✅
  B5 — Pattern Memory: ChromaDB indexes all findings for RAG retrieval ✅
  C6 — Source Attribution: ChromaDB metadata tags on every indexed document ✅
Speaker note: We targeted 8 enhancement layers across A, B, and C tracks — not just the minimum.

─────────
SLIDE 14: SECURITY & PRODUCTION TRADEOFFS
─────────
Two columns: "What We Did" vs "What Production Would Add"
  API keys in .env (git-ignored) → AWS Secrets Manager / Vault
  SQLite (plain JSON for credentials) → Encrypted RDS + Secrets Manager
  No auth layer → streamlit-authenticator + RBAC (admin/auditor/viewer)
  Langfuse cloud tracing (content redacted) → Self-hosted Langfuse
  Local ChromaDB → Pinecone / Weaviate for distributed search
  Ollama option: fully local, zero data leaves machine ✅ (already production-ready)
Key message: "We made honest tradeoffs — and we know exactly what to swap for production."
Speaker note: Showing you understand the tradeoffs is as important as the implementation.

─────────
SLIDE 15: DEPLOYMENT ARCHITECTURE
─────────
Three tiers:
  Local: streamlit run app/main.py (Python venv)
  Docker: python:3.11-slim + HEALTHCHECK, EXPOSE 8501
  AWS Production:
    ECS Fargate (Streamlit UI + LangGraph Pipeline)
    ECR (Docker image registry)
    EFS (persistent SQLite + ChromaDB across restarts — critical!)
    S3 → Lambda → SQS → ECS (event-driven batch trigger)
    Secrets Manager + CloudWatch
Key message: "Dockerized today. ECS-ready tomorrow. Zero architectural debt."
Speaker note: The EFS detail is important — without it, every Fargate restart wipes the database.

─────────
SLIDE 16: LIVE DEMO — WHAT YOU WILL SEE
─────────
Demo script structure:
  Step 1 (30s): Upload a PDF containing Aadhaar, AWS key, salary figure
  Step 2 (30s): Watch 4 parallel agents run — live progress bar
  Step 3 (30s): Show scan result: CRITICAL risk, 47 flags, masked entity table
  Step 4 (30s): Download PDF compliance report
  Step 5 (30s): Switch to Data Source Scanner — show Snowflake column classification
  Step 6 (30s): Ask AI Copilot: "Which columns need immediate encryption?"
  Step 7 (30s): Show Telemetry dashboard — token usage, latency, risk trends
Speaker note: Keep the demo focused — one PDF, one data source, one Copilot question. Show confidence scores.

─────────
SLIDE 17: KEY NUMBERS AT A GLANCE
─────────
Large-number grid:
  12 — PII pattern types
  15 — Credential patterns
  25+ — Column classification rules
  4 — Parallel compliance checks per PDF
  10 — Data source connectors
  12 — SQLite tables
  4 — AI providers (runtime-switchable)
  0 — Hardcoded API keys
  <30s — Typical PDF scan time
  8 — Enterprise enhancement layers delivered
Speaker note: These numbers tell the story of depth — not a weekend project.

─────────
SLIDE 18: WHAT WE'D BUILD WITH 2 MORE WEEKS
─────────
1. OCR Integration — Tesseract for scanned image PDFs (currently flagged, not parsed)
2. Batch Processing UI — queue 50+ PDFs, track per-file progress, batch summary report
3. Encrypted Credential Storage — AWS Secrets Manager for connector credentials
4. Auto-Monitor Scheduler — APScheduler for data sources with auto_monitor=True
5. Remediation Workflow — acknowledge findings, assign owners, track resolution
6. Multi-Tenant Auth — streamlit-authenticator with role-based access
7. S3-Triggered Automation — boto3 event polling → auto-trigger pipeline on PDF arrival
Speaker note: This slide shows production maturity — we know exactly what's left and why.

─────────
SLIDE 19: PANEL Q&A PREPARATION
─────────
Table of likely questions + our answers:
  Q: "How do you know the AI didn't hallucinate a violation?"
  A: Confidence scoring — AI below 0.70 auto-rejected. Every flag shows match_method (regex/ai). Regex = deterministic.

  Q: "This works on 50 rows. What at 50 million?"
  A: Swap SQLite → RDS. Add SQS queue. Run pipeline as ECS task per PDF. Architecture already supports it.

  Q: "Bedrock/Groq is down. What does your system do?"
  A: Switch AI_PROVIDER via UI dropdown. Tenacity retries 5× with backoff. Ollama = fully local fallback.

  Q: "How do you handle a PDF with scanned images instead of text?"
  A: PyMuPDF reports image_count per page. Encoding guard flags it. Next step: Tesseract OCR integration.

  Q: "Show me the audit trail."
  A: Every scan has UUID, timestamp, provider, full JSON result, token count in SQLite. Langfuse trace links every AI call.

  Q: "Is document content sent to third parties?"
  A: Only to the chosen AI provider. Langfuse traces have content redacted. Ollama option = nothing leaves the machine.

Speaker note: The panel respects candour. If you don't know, say what you'd do to find out.

─────────
SLIDE 20: THANK YOU / CLOSE
─────────
GitHub repo: github.com/Shahsmit075/pdf-compliance-scanner
Stack summary: Streamlit + LangGraph + ChromaDB + SQLite + Langfuse + Groq/Gemini/Claude/Ollama + Docker
Team: Shahsmit075 × ArpitMishra2
Tagline: "From document chaos to compliance clarity — in 30 seconds."
Speaker note: Leave the GitHub URL up. Invite the panel to clone and run it.

────────────────────────────────────────────────────────────────
FORMATTING INSTRUCTIONS FOR THE PPT GENERATOR:
────────────────────────────────────────────────────────────────
- Every slide: max 6 bullet points. Short, punchy. No full sentences in bullets.
- Speaker notes: 2–4 sentences. Conversational. What the presenter says OUT LOUD.
- Slide 4 (Architecture): describe as a labelled flow diagram — do NOT use a static bullet list.
- Slides 6, 9, 13, 14: use TWO-COLUMN or TABLE layouts for comparison/grouping.
- Slide 17: use LARGE NUMBERS layout (the number dominates, label beneath).
- Slide 19: use TABLE layout (Question | Answer).
- Total slides: 20.
- Tone: confident, technical, honest. Not sales-y. Not vague.
- Avoid: "leverages", "utilises", "cutting-edge", "state-of-the-art", "revolutionary".
- Use: specific numbers, method names, library names, tradeoff acknowledgements.
```

---

*Prompts generated: 2026-06-03 | For: PDF Compliance Scanner Demo Day*
