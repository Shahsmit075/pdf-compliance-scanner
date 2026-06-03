# GenAI for Data Engineering — Capstone Project Enhancement Specification
**Sigmoid Bangalore | Batch May–Jun 2026 | DevPro Academy**

---

## Context

The three capstone options below retain their core deliverables as originally defined. This document adds **Enterprise Enhancement Layers** — additional requirements that elevate each project from a working prototype to a production-grade system demonstrating large-enterprise thinking.

Teams that deliver the core requirements + 2 or more enhancement layers will score significantly higher on **Innovation & Creativity (30%)** and **Technical Execution (30%)** — the two highest-weighted assessment criteria.

> **All tools listed are free tier / open source. No paid subscriptions required.**

---

## Assessment Criteria (Unchanged)

| Criterion | Weight |
|---|---|
| Innovation & Creativity | 30% |
| Technical Execution | 30% |
| GenAI Application Depth | 20% |
| Business Value Articulation | 10% |
| Presentation Quality | 10% |

**Enhancement layers directly impact the top two criteria (60% combined weight).**

---

## Option A: Intelligent Document Compliance Pipeline

### Core Deliverable (Unchanged)
Parse PDF documents → check for compliance violations → update status → generate compliance report.
- **Tech:** LangGraph + Claude/Bedrock/Gemini + PyPDF
- **Output:** GitHub repo + live demo + pipeline report

### Enterprise Enhancement Layers

| # | Enhancement | What It Adds | Production Relevance |
|---|---|---|---|
| A1 | **Multi-Document Lineage & Versioning** | Process multiple PDFs, track which source document produced which finding. Support document version comparison (v1 vs v2 of same policy — show what changed and new violations introduced). | Regulators and legal teams need full audit trail: "which version of document X was assessed, when, and by what model version?" |
| A2 | **Confidence Scoring & Human Escalation** | Every violation gets a confidence score (0–100%). Scores <80% route to a human review queue. Scores >80% auto-flag with explanation. Configurable threshold per violation type. | No enterprise ships "AI said it's non-compliant" without confidence scoring. Liability requires human oversight for uncertain findings. |
| A3 | **Batch Processing & Job Queue** | Process 50+ PDFs in parallel using a job queue pattern (e.g., asyncio queue or simple file-based queue). Track progress: queued → processing → complete → failed. Support retry on transient failures. | Real compliance teams dump 200 contracts at quarter-end. "One PDF at a time" doesn't survive day one in production. |
| A4 | **Remediation Suggestions** | Don't just flag violations — generate specific, actionable text suggestions to become compliant. Include: original text, violation reason, suggested replacement, confidence level. | Transforms from "detective" (finds problems) to "advisor" (solves problems). This is the difference between a $50K tool and a $500K tool. |
| A5 | **Operations Dashboard & Metrics** | Track and display: documents processed per day, violation rate trends over time, average confidence scores, processing latency (time per document), model cost per run. Streamlit or simple HTML dashboard. | Every VP's first question: "Is this thing working? Is it getting better? What's it costing us?" Without metrics, no one trusts it. |
| A6 *(bonus)* | **S3-Triggered Automation** | Watch an S3 bucket — when a new PDF lands, auto-trigger the pipeline using Lambda or an S3 event poller. Zero manual intervention. | Compliance pipelines in enterprises run on arrival of documents, not on human schedule. Event-driven = production-grade. |

### Recommended Free Tools — Option A

| Enhancement | Tool | Why | Setup Time |
|---|---|---|---|
| A1 — Lineage & Versioning | **SQLite** (built-in Python) | Store document metadata, version history, finding-to-source mapping. Zero config. | 10 min |
| A2 — Confidence + Escalation | **Streamlit** (free) | Show pending human review queue with approve/reject buttons. Runs locally. | 20 min |
| A3 — Batch Queue | **Python asyncio** or **`concurrent.futures`** | Built into Python — no install. Process N PDFs in parallel with progress tracking. | 15 min |
| A4 — Remediation | **Claude Haiku via Bedrock** | Cheapest model for remediation text generation. ~$0.25 per 1M tokens. | 5 min (already configured) |
| A5 — Dashboard | **Streamlit** (free) + **Plotly** (free) | Bar charts, trend lines, latency histograms. One `pip install`. | 20 min |
| A6 — S3 Trigger | **boto3 S3 event polling** or **AWS Lambda** (free tier: 1M calls/month) | Poll S3 prefix every 60s for new PDFs. Lambda is free for the volumes here. | 25 min |

### Architecture Expectation (Enhanced)
```
PDF Upload (S3/Local)
  → Document Queue (batch processing — asyncio)
    → LangGraph Orchestrator
      → Parse Agent (extract text, tables, clauses)
      → Classification Agent (identify relevant regulation sections)
      → Compliance Check Agent (compare against rules, generate findings + confidence score)
      → Remediation Agent (suggest fixes for violations)
    → Confidence Filter
      → Auto-report (≥80% confidence)
      → Human review queue (Streamlit UI) (<80% confidence)
    → Report Generator (per-document + batch summary)
    → SQLite (lineage, version history, metrics)
    → Streamlit Dashboard (metrics, trends, cost)
```

---

## Option B: Agentic Data Engineering Operations System

### Core Deliverable (Unchanged)
3 autonomous agents: Quality Agent, Lineage/Governance Agent, Pipeline Fixer (detect errors → fix → alert).
- **Tech:** LangGraph/CrewAI + MCP + Snowflake/dbt
- **Output:** Agent demo + architecture diagram + autonomous run log

### Enterprise Enhancement Layers

| # | Enhancement | What It Adds | Production Relevance |
|---|---|---|---|
| B1 | **Agent Observability & Tracing** | Every agent decision logged with full trace: input → reasoning → action → outcome → cost. Viewable as a timeline. Support replaying a decision chain for debugging. | "Why did the agent drop 10,000 rows?" If you can't trace it, you can't deploy it. Observability is non-negotiable for autonomous systems. |
| B2 | **Cost Guardrails & Budget Management** | Each agent run tracks LLM token cost. Configurable budget per run (e.g., max $2.00). If budget exceeded: pause, alert, require human approval to continue. Daily/weekly cost reports. | An autonomous agent without a cost ceiling is a $10,000 invoice waiting to happen. Enterprises enforce spend controls on ALL automated systems. |
| B3 | **Human-in-the-Loop Escalation** | Agents classify decisions as LOW/MEDIUM/HIGH risk. High-risk actions (schema changes, data deletion, pipeline restarts) require explicit human approval before execution. Approval queue with timeout. | "The agent decided to recreate the production table at 3 AM" is a career-ending incident. Guardrails aren't optional — they're how you keep autonomy safe. |
| B4 | **Multi-Agent Coordination Protocol** | Define conflict resolution: what happens when Quality Agent says "quarantine this data" but Pipeline Fixer says "retry the load"? Priority rules, deadlock detection, consensus mechanism. | Multi-agent systems without coordination become chaos. Real systems need clear authority hierarchy and conflict resolution patterns. |
| B5 | **Incident Learning & Pattern Memory** | Agents store resolved incidents in a knowledge base. On new failures, search for similar past incidents first. "This looks like the schema drift we saw on March 15 — same fix applied." Track fix success rate. | Production systems improve over time. First occurrence: novel. Second occurrence with same fix: learned. This is institutional knowledge at machine speed. |
| B6 *(bonus)* | **Slack / Email Alerting** | Agent sends structured alert when high-risk action taken or budget threshold crossed. Message includes: what happened, confidence, recommended action, link to trace. | No enterprise ops team watches a dashboard 24/7. Alerts come to where people already are — Slack. |

### Recommended Free Tools — Option B

| Enhancement | Tool | Why | Setup Time |
|---|---|---|---|
| B1 — Observability | **Langfuse** (free cloud tier) | Full LangChain/LangGraph trace timeline, cost per run, input/output per node. 5-line integration. | 10 min |
| B1 — Alternative | **Arize Phoenix** (fully open source, local) | No account needed, runs on `localhost:6006`. Same trace UI. | 10 min |
| B2 — Cost Guardrails | **SQLite** + token count from Bedrock response | Track `input_tokens + output_tokens` per run, cumulative daily cost. Raise exception if budget exceeded. Visualise in Streamlit. | 20 min |
| B3 — Human Approval | **Slack Webhooks** (free tier) | Agent posts "HIGH RISK pending — approve?" to a Slack channel. Free tier supports unlimited webhooks. | 15 min |
| B3 — Alternative | **Gmail SMTP** (free) | Agent emails approval request, polls reply. Zero cost, works without Slack. | 15 min |
| B4 — Coordination | **SQLite shared state table** | Agents write `status = locked/queued/resolved` before acting. Poll before claiming a task. Enterprise-grade pattern, zero overhead. | 20 min |
| B5 — Pattern Memory | **ChromaDB** (local, free, no account) | Embed past incidents as vectors, similarity-search on new failures. Already used in Option C — shared skill. | 10 min |
| B6 — Alerting | **Slack Incoming Webhooks** (free) | `pip install slack-sdk`, one `WebhookClient.send()` call. Formatted message with fields. | 10 min |

### Architecture Expectation (Enhanced)
```
Trigger (schedule / event / anomaly detected)
  → Supervisor Agent (assigns work, enforces priority)
    → Quality Agent
        Tools: Great Expectations, data profiler, schema validator
        Actions: validate, quarantine, alert
    → Lineage/Governance Agent
        Tools: dbt manifest parser, column scanner, catalogue API
        Actions: extract lineage, classify PII, generate docs
    → Pipeline Fixer Agent
        Tools: log reader, DAG inspector, SQL executor
        Actions: diagnose, apply fix, re-validate, generate incident report
  → Coordination Layer (SQLite shared state, conflict resolution)
  → Risk Classifier → Human approval queue (Slack / Email)
  → Observability Layer — Langfuse or Arize Phoenix (trace every decision, cost per run)
  → Knowledge Base — ChromaDB (past incidents, fix patterns, success rates)
  → Budget Monitor (SQLite token tracker → alert if exceeded)
```

---

## Option C: Intelligent DE Operations Centre (RAG-Powered)

### Core Deliverable (Unchanged)
Conversational AI assistant for Data Engineers: pipeline debugging, design decisions, SLO definitions.
- **Tech:** ChromaDB + Snowflake + Bedrock/Claude + MCP
- **Output:** Live demo app + notebook + 10-slide deck

### Enterprise Enhancement Layers

| # | Enhancement | What It Adds | Production Relevance |
|---|---|---|---|
| C1 | **Multi-Source Knowledge Ingestion** | Ingest not just docs — also: pipeline logs (last 7 days), dbt manifest.json, Airflow DAG definitions, Great Expectations results, incident history. Each source tagged with freshness + reliability score. | A real DE assistant needs ALL context. "What went wrong?" requires logs. "What's the schema?" requires dbt. "Has this happened before?" requires incident history. Docs alone = partial answers. |
| C2 | **Tool-Calling Actions (Not Just Chat)** | Assistant can: run SQL queries (NL2SQL from Day 6), check pipeline run status, trigger DAG re-runs, create Jira/Linear tickets, fetch current Snowflake table stats. Moves from "tells you" to "does for you." | The difference between a chatbot and an operations tool is action. ChatGPT tells you what to do. An ops centre does it for you (with your approval). |
| C3 | **Proactive Anomaly Alerts** | Don't wait for questions. Background agent monitors logs + metrics. Detects: pipeline latency spike, unusual row count changes, new error patterns. Pushes notification: "Pipeline X is 3x slower than usual — here's why." | Enterprise = proactive, not reactive. The best on-call engineers notice problems BEFORE pages fire. This codifies that instinct. |
| C4 | **Session Memory & Incident Correlation** | Remembers conversation context across sessions. Correlates current issues with past incidents: "This error pattern matches the Feb 22 outage where root cause was Snowflake warehouse suspension." Builds institutional memory. | Senior engineers are valuable because they remember. "Last time this happened, the fix was..." This captures that knowledge so it survives team turnover. |
| C5 | **Feedback Loop & Self-Improvement** | User can mark responses as helpful/unhelpful. Corrections stored and used to improve future answers (retrieval re-ranking, prompt refinement). Track accuracy metrics: response helpfulness rate, correction rate over time. | Static systems degrade. Self-improving systems compound in value. After 1 month, the assistant is significantly better than on day one — because the team trained it through usage. |
| C6 *(bonus)* | **Source Attribution UI** | Every answer shows which document/log/incident it was drawn from, with a confidence score per source. User can click to see the original chunk. | Enterprises don't trust black-box answers. "Show your sources" is a legal and compliance requirement in regulated industries. |

### Recommended Free Tools — Option C

| Enhancement | Tool | Why | Setup Time |
|---|---|---|---|
| C1 — Multi-Source Ingestion | **LlamaIndex** (free, open source) | Built-in connectors for JSON, logs, CSV, dbt manifest. Handles chunking + embedding pipeline. `pip install llama-index`. | 20 min |
| C1 — Vector Store | **ChromaDB** (local, free) | Already in the core stack. Tag each chunk with `source_type`, `ingested_at`, `freshness_score` as metadata. | Already installed |
| C2 — Tool Calling | **LangGraph + MCP tools** | Already in the stack from Days 6–10. Wire NL2SQL (Day 6 script) as a tool node in LangGraph. | 20 min |
| C2 — Ticket Creation | **Linear API** (free tier) or **GitHub Issues API** | Create issues programmatically via REST. Free for personal/small teams. | 15 min |
| C3 — Proactive Alerts | **APScheduler** (free, `pip install apscheduler`) | Run background monitoring job every N minutes inside the same Python process. No separate infra needed. | 15 min |
| C3 — Alerting channel | **Slack Webhooks** (free) | Push anomaly notification to a #alerts Slack channel. One API call. | 10 min |
| C4 — Session Memory | **SQLite** (built-in) | Store conversation turns + entity extractions. Query on new session start for relevant past context. | 15 min |
| C4 — Semantic Memory | **ChromaDB** (already installed) | Embed past incidents + resolutions. On new query, similarity-search before answering. | 10 min |
| C5 — Feedback Loop | **Streamlit** with thumbs up/down buttons | Store feedback in SQLite. Re-rank ChromaDB results based on upvoted sources using metadata filter. | 25 min |
| C6 — Source Attribution | **Streamlit** expandable sections | Show retrieved chunks with source filename, chunk ID, relevance score. Native Streamlit `st.expander`. | 15 min |

### Architecture Expectation (Enhanced)
```
Knowledge Sources (continuously refreshed via APScheduler):
  → Pipeline logs (daily ingestion — LlamaIndex JSONReader)
  → dbt manifest + catalog.json (LlamaIndex JSONReader)
  → Airflow DAG definitions (LlamaIndex PythonReader)
  → Great Expectations validation results
  → Incident history / resolution records
  → Team runbooks and documentation

Ingestion Pipeline:
  → Chunking + embedding → ChromaDB
  → Source tagging (freshness, reliability, type) as metadata
  → Deduplication + staleness detection

User Interface (Streamlit):
  → Multi-turn conversational UI
  → Source attribution panel (which chunk answered this?)
  → Feedback buttons (helpful / not helpful / correction)
  → Tool execution log (what actions the assistant took)

Agent Layer (LangGraph):
  → RAG retrieval (ChromaDB — multi-source, ranked by relevance + freshness)
  → Tool-calling nodes (NL2SQL, pipeline status, ticket creation)
  → Proactive monitor (APScheduler background job → Slack alert)
  → Session memory (SQLite cross-conversation context)

Feedback & Improvement:
  → SQLite feedback store
  → ChromaDB re-ranking based on upvoted sources
  → Response quality metrics dashboard (Streamlit)
```

---

## Quick-Start Install Commands (All Options)

```bash
# Core tools (all options)
pip install streamlit boto3 langchain langgraph chromadb

# Option A additions
pip install pypdf plotly

# Option B additions
pip install langfuse slack-sdk
# OR for local observability (no account):
pip install arize-phoenix openinference-instrumentation-langchain

# Option C additions
pip install llama-index apscheduler plotly slack-sdk
```

---

## Cloud Deployment Track *(Optional — High Impact)*

> A live URL on AWS beats a localhost demo every time. All three options below are confirmed working on student free tier accounts with UPI payment.
>
> ⚠️ **Do NOT use AWS App Runner or Kinesis** — not available on student credits.

---

### Common Foundation (All Options)

Every team follows the same base pattern regardless of which capstone option they chose:

```
Your App Code
  → Dockerfile  (package app + dependencies)
    → Amazon ECR  (store the Docker image)
      → ECS Fargate  (run the container — no server to manage)
        → Public IP / URL  (accessible from anywhere)

Secrets  → AWS Secrets Manager  (never hardcode keys)
Logs     → AWS CloudWatch       (free tier, 5 GB)
LLM      → AWS Bedrock          (same region = low latency, uses $200 credits)
```

**Dockerfile template (same for all options):**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
# FastAPI alternative: CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
```

**Push to ECR (same for all options):**
```bash
aws ecr create-repository --repository-name sigma-capstone --region us-east-1

aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  <account-id>.dkr.ecr.us-east-1.amazonaws.com

docker build -t sigma-capstone .
docker tag sigma-capstone:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/sigma-capstone:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/sigma-capstone:latest
```

**Deploy on ECS Fargate (AWS Console):**
ECS → Create Cluster → Fargate → Create Task Definition → pick your ECR image, set port, add env vars → Create Service → assign to cluster → get Public IP from running task.

**Cost:** ~$0.04/vCPU-hr + $0.004/GB-hr. At 0.5 vCPU / 1 GB: ~$3–5 for 48 hours. Stop service after Demo Day.

---

### Option A — Intelligent Document Compliance Pipeline

**Production Architecture on AWS:**

```
USER
  → Streamlit UI (ECS Fargate — port 8501)
      ↓ PDF upload
  → S3 Bucket  (store incoming PDFs — event source)
      ↓ S3 Event Notification
  → AWS Lambda  (trigger: new PDF arrived → push to SQS queue)
      ↓
  → SQS Queue  (job queue — decouples upload from processing)
      ↓ consumer
  → LangGraph Pipeline (ECS Fargate — same container as UI or separate)
      ├── Parse Agent       → PyPDF extracts text
      ├── Compliance Agent  → Bedrock Claude checks violations + confidence score
      └── Remediation Agent → Bedrock Claude suggests fixes
      ↓
  → SQLite on EFS  (findings, lineage, version history — persists across Fargate restarts)
      ↓
  → Streamlit Dashboard  (violation trends, confidence scores, cost per run)

Secrets → AWS Secrets Manager
Logs    → CloudWatch (Lambda + Fargate task logs)
```

**Key AWS services used:**

| Service | Role | Free / Cost |
|---|---|---|
| ECS Fargate | Run Streamlit + LangGraph container | ~$3–5 for 48 hrs |
| S3 | PDF storage + event trigger | Free tier (5 GB) |
| Lambda | S3 → SQS trigger | Free tier (1M calls/month) |
| SQS | Job queue for batch PDFs | Free tier (1M requests/month) |
| ECR | Docker image registry | Free (500 MB) |
| EFS | Persistent storage for SQLite | ~$0.30/GB-month |
| Secrets Manager | API keys | Free first 30 days |
| CloudWatch | Logs | Free (5 GB) |

**Why EFS for SQLite?** ECS Fargate containers have no persistent disk. Without EFS, every task restart wipes the SQLite database. Mount an EFS volume and SQLite persists across restarts — exactly like a real production database.

**What to say on Demo Day:**
> *"PDFs land in S3, Lambda triggers the queue, Fargate processes them through our LangGraph compliance pipeline, findings stored in SQLite on EFS. Fully event-driven — zero manual intervention. In production we'd swap SQLite for RDS Aurora Serverless."*

---

### Option B — Agentic DE Operations System

**Production Architecture on AWS:**

```
TRIGGER (schedule / anomaly / manual)
  → ECS Fargate  (supervisor + 3 agents running as one containerised app)
      ├── Quality Agent        → Great Expectations + Bedrock
      ├── Lineage Agent        → dbt manifest parser + Bedrock
      └── Pipeline Fixer Agent → log reader + SQL executor + Bedrock
      ↓
  → SQLite on EFS  (shared agent state, coordination lock table, budget tracker)
      ↓
  → Risk Classifier
      ├── LOW / MEDIUM → auto-execute, log to CloudWatch
      └── HIGH         → Slack Webhook alert → human approval required
      ↓
  → Langfuse Cloud  (agent trace observability — free tier, external SaaS)
      ↓
  → Grafana Cloud   (operational metrics dashboard — free tier, external SaaS)
        data source: FastAPI /metrics endpoint on Fargate → Prometheus scrape
      ↓
  → ChromaDB on EFS  (incident pattern memory — persists across restarts)

Secrets → AWS Secrets Manager (Bedrock keys, Slack webhook URL)
Logs    → CloudWatch (all agent stdout)
```

**Key AWS services used:**

| Service | Role | Free / Cost |
|---|---|---|
| ECS Fargate | Run all 3 agents + supervisor | ~$3–5 for 48 hrs |
| EFS | Persist SQLite + ChromaDB data | ~$0.30/GB-month |
| ECR | Docker image | Free (500 MB) |
| Secrets Manager | Bedrock + Slack keys | Free first 30 days |
| CloudWatch | Agent logs | Free (5 GB) |
| Langfuse Cloud | LLM trace observability | Free tier (external) |
| Grafana Cloud | Metrics dashboard | Free tier (external) |
| Slack Webhooks | Human approval alerts | Free |

**Grafana data flow (for the team using it):**
```
Agent Python code
  → prometheus_client (expose /metrics endpoint on port 9090)
    → Grafana Cloud scrapes /metrics every 15s
      → Dashboards: token cost, run count, HIGH-risk actions, budget burn
```

**What to say on Demo Day:**
> *"Three autonomous agents running on ECS Fargate. Every decision traced in Langfuse. Operational metrics — cost, risk actions, budget burn — live in Grafana. HIGH-risk actions pause and alert Slack for human approval before executing. Incident memory in ChromaDB persists on EFS across restarts."*

---

### Option C — RAG-Powered DE Operations Centre

**Production Architecture on AWS:**

```
KNOWLEDGE SOURCES (ingested on schedule via APScheduler)
  → S3 Bucket
      ├── Pipeline logs (daily)
      ├── dbt manifest.json
      ├── Airflow DAG files
      ├── Great Expectations results
      └── Incident history / runbooks
      ↓
  → Ingestion Pipeline (ECS Fargate)
      → LlamaIndex readers → chunk + embed → ChromaDB on EFS
        (tagged with source_type, ingested_at, freshness_score)

USER QUERY FLOW
  → Streamlit UI (ECS Fargate — port 8501)
      ↓
  → LangGraph Agent (same container)
      ├── RAG retrieval    → ChromaDB on EFS (multi-source, ranked)
      ├── NL2SQL tool      → Snowflake / Athena (pipeline stats)
      ├── Tool-call node   → trigger DAG, create ticket, check status
      └── Session memory   → SQLite on EFS (cross-session context)
      ↓
  → Bedrock Claude  (answer generation — stays in AWS region)
      ↓
  → Streamlit UI  (answer + source attribution panel + feedback buttons)
      ↓
  → SQLite on EFS  (feedback store — helpful / not helpful / corrections)

PROACTIVE MONITORING (APScheduler background thread — same container)
  → polls S3 logs every 5 min
  → detects anomalies → Slack Webhook alert

Secrets → AWS Secrets Manager
Logs    → CloudWatch
```

**Key AWS services used:**

| Service | Role | Free / Cost |
|---|---|---|
| ECS Fargate | Run Streamlit + LangGraph + APScheduler | ~$3–5 for 48 hrs |
| S3 | Knowledge source storage (logs, manifests, runbooks) | Free tier (5 GB) |
| EFS | Persist ChromaDB vector index + SQLite | ~$0.30/GB-month |
| ECR | Docker image | Free (500 MB) |
| Bedrock Claude Haiku | Answer generation | Pay-per-token ($200 credits) |
| Secrets Manager | API keys | Free first 30 days |
| CloudWatch | App logs | Free (5 GB) |
| Slack Webhooks | Proactive anomaly alerts | Free |

**Why EFS is critical for Option C:** ChromaDB's vector index is the heart of the app. Without EFS, every Fargate task restart means re-ingesting and re-embedding all documents — could take 10–20 minutes. With EFS mounted, the index persists and the app is ready in seconds.

```bash
# Mount EFS in your ECS Task Definition
# Add this volume in task definition JSON:
{
  "name": "chroma-data",
  "efsVolumeConfiguration": {
    "fileSystemId": "fs-xxxxxxxx",
    "rootDirectory": "/chroma"
  }
}
# Mount point in container: /app/chroma_data
```

**What to say on Demo Day:**
> *"Knowledge from S3 — logs, dbt manifests, runbooks — ingested into ChromaDB on EFS via LlamaIndex. Every query hits RAG first, then Bedrock for generation. The assistant can also act — run SQL, check pipeline status, create tickets. Background monitor polls S3 logs every 5 minutes and pushes Slack alerts on anomalies. Session memory in SQLite means it remembers what we talked about last session."*

---

### Deployment Checklist (All Options)

- [ ] `docker build` succeeds locally — no errors
- [ ] `docker run` works locally — app loads in browser
- [ ] ECR repo created, image pushed
- [ ] ECS cluster created (Fargate)
- [ ] Task definition created — correct image URI, port, env vars set
- [ ] EFS volume created and mounted in task definition (Options A/B/C — for SQLite/ChromaDB persistence)
- [ ] ECS Service created — task shows **RUNNING** in console
- [ ] Public IP from running task loads the app from phone/browser
- [ ] No hardcoded credentials — all keys in Secrets Manager or ECS env vars
- [ ] CloudWatch log group shows app logs
- [ ] **Stop the ECS service after Demo Day**

---

## Scoring Guidance for Assessors

| Level | Core Deliverable | Enhancement Layers | Expected Score Range |
|---|---|---|---|
| **Basic Pass** | Working demo, code runs | 0 layers | 50–65% |
| **Good** | Clean code, handles edge cases | 1 layer implemented | 65–75% |
| **Strong** | Production-quality architecture | 2 layers implemented well | 75–85% |
| **Exceptional** | Could deploy tomorrow | 3+ layers, coherent system design | 85–95% |

Enhancement layers must be **functional** (working code/demo), not just described in a slide. Partial implementation with clear "what's left" documentation is acceptable and shows production thinking.

---

## Presentation Format (Demo Day)

**10 minutes per team:** 7 min live demo + 3 min Q&A

Suggested demo structure:
1. **Problem statement** (30 sec) — what business problem does this solve?
2. **Architecture overview** (60 sec) — one diagram, explain the flow
3. **Core demo** (3 min) — show the basic system working end-to-end
4. **Enhancement demo** (2 min) — show 1-2 enterprise layers in action
5. **What would you improve with 2 more weeks?** (30 sec) — shows maturity
6. **Q&A** (3 min) — panel asks production-readiness questions

### Sample Panel Questions (Prepare For These)
- "Your agent runs autonomously overnight. How do you know it didn't corrupt data?"
- "This works on 50 rows. What happens at 50 million?"
- "Bedrock is down. What does your system do?"
- "A new team member joins. How long to understand your codebase?"
- "What's the monthly cost to run this at 10x current scale?"
- "Show me the audit trail for the last decision your agent made."
- "Which source document did your RAG pull to answer that?" *(Option C)*
- "What happens if two agents disagree?" *(Option B)*
- "How do you handle a PDF with scanned images instead of text?" *(Option A)*

---


