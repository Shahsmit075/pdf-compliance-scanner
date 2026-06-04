# 🎤 CUE CARD — ARPIT | Layer 3 & Layer 4
### Presentation Time: ~4–5 minutes | Speak slowly and clearly!

---

## 🟢 OPENING LINE (5 sec)

> *"So my part is Layer 3 and Layer 4 — which is the brain that connects to real databases and scans them automatically."*

---

## 🔵 LAYER 3 — Data Source Agent Pipeline (~2.5 min)

### What is it? (say this first)
- Layer 2 scanned PDFs. **Layer 3 scans live databases** — like PostgreSQL, Snowflake, etc.
- We built **3 AI agents** that work together in a pipeline using **LangGraph**.

---

### Agent 1 — Metadata Agent
- First, this agent **connects to the database**.
- It reads the **schema** — meaning, it looks at all the tables and columns.
- Then it **compares** the current schema with the last saved snapshot.
- If something changed — like a new column was added — it **detects that change**.

> 💬 *"Think of it like a watchdog. It notices when your database structure changes."*

---

### Agent 2 — Compliance Agent
- This agent takes the metadata and **classifies each column**.
- It checks: *"Is this column storing PII? Is it confidential? Is it a risk?"*
- Then it **calculates a risk score** for the whole data source.

> 💬 *"So if a column is named 'user_ssn' or 'salary', the agent flags it as high risk."*

---

### Agent 3 — Alert Agent
- After the compliance agent gives results, this agent **decides whether to send an alert**.
- If risk is HIGH or CRITICAL, it **sends notifications** — to Slack, Email, or a Webhook.
- It also **logs everything** to the database for history.

> 💬 *"So your security team gets notified automatically — no manual checking needed."*

---

### One key point about Layer 3:
- All 3 agents are connected using **LangGraph** — a framework that manages the flow between agents.
- Every agent run is also **traced by Langfuse** — so we can debug and monitor each run in the cloud.

---

## 🟠 LAYER 4 — Connector Layer (~1.5 min)

### What is it? (say this first)
- For the agents in Layer 3 to work, they need to actually **connect to different databases**.
- That's what Layer 4 does — it provides **10 ready-made connectors**.

---

### 3 categories of connectors:

**1. Databases** (4 connectors)
- PostgreSQL, MySQL, MongoDB, SQL Server
- These are your traditional relational and NoSQL databases.

**2. Cloud Storage** (3 connectors)
- AWS S3, Azure ADLS Gen2, Google Cloud Storage
- These are for file storage in the cloud.

**3. Data Warehouses** (3 connectors)
- Snowflake, BigQuery, Databricks
- These are for large-scale analytics data.

---

### Smart Design — Lazy Loading
- We did not load all 10 connectors at startup — that would be slow.
- Instead, we use **lazy loading** — the connector only loads **when you actually use it**.
- This keeps the app fast and lightweight.

---

### How it works — Factory Pattern
- We use a **Factory Pattern** in code.
- The user picks a database type in the UI.
- Our `ConnectorFactory` automatically picks the right connector class and creates it.

> 💬 *"So as a developer, if we want to add an 11th connector tomorrow, we just register it in one place — nothing else changes."*

---

## ✅ CLOSING LINE (10 sec)

> *"So to summarize — Layer 3 is the intelligent scanning pipeline with 3 agents that detect, classify, and alert. Layer 4 is what makes it work across 10 different data sources. Together, they make the system work beyond just PDFs — on real production databases."*

---

## 📌 QUICK CHEAT SHEET (if you forget)

| | Layer 3 | Layer 4 |
|---|---|---|
| **What** | 3 AI Agents (LangGraph) | 10 Connectors |
| **Agent 1** | Metadata — reads schema, detects changes | — |
| **Agent 2** | Compliance — classifies columns, risk score | — |
| **Agent 3** | Alert — sends Slack/Email if high risk | — |
| **Connectors** | — | DB + Cloud + Warehouse |
| **Key design** | Langfuse tracing | Lazy loading + Factory Pattern |

---

> ⏱️ **Pace guide:** Layer 3 = ~2.5 min | Layer 4 = ~1.5 min | Total = ~4 min
> 🗣️ Speak slowly. Pause after each agent. Make eye contact when saying the "think of it like..." lines.
