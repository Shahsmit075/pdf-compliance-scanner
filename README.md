# 🛡️ Enterprise PDF & Data Source Compliance Scanner

[![Python](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.55+-red.svg)](https://streamlit.io/)
[![LangGraph](https://img.shields.io/badge/LangGraph-1.1+-orange.svg)](https://github.com/langchain-ai/langgraph)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-0.3+-green.svg)](https://www.trychroma.com/)
[![Observability](https://img.shields.io/badge/Langfuse-2.0+-blueviolet.svg)](https://langfuse.com/)
[![Docker](https://img.shields.io/badge/Docker-python:3.11--slim-blue.svg)](https://www.docker.com/)

An AI-powered, enterprise-grade data and document compliance scanning platform. It features two distinct operational modes sharing a unified storage, vector search, alert infrastructure, and telemetry analytics dashboard, all wrapped in a sleek, custom **Noir Amber** dark-mode UI.

---

## 📌 Table of Contents
1. [Core Capabilities](#-core-capabilities)
2. [System Architecture](#%EF%B8%8F-system-architecture)
3. [Technology Stack](#%EF%B8%8F-technology-stack)
4. [Getting Started](#-getting-started)
5. [Environment & Configuration](#-environment--configuration)
6. [Observability & Testing](#-observability--testing)
7. [Database Schema](#-database-schema)

---

## 🚀 Core Capabilities

| Operational Mode / Feature | Description | Core Engine |
| :--- | :--- | :--- |
| **PDF Document Scanner** | Ingests PDF files and executes 4 parallel compliance nodes (PII, Confidentiality, Encoding, Abuse) under 30 seconds. | LangGraph DAG + PyMuPDF |
| **Data Source Scanner** | Classifies schema columns (PII/PHI/PCI), detects schema drift, and tracks compliance trends for 10+ databases/cloud warehouses. | Multi-Agent System + Rules Engine |
| **AI Copilot (RAG)** | Interactive conversational assistant retrieving compliance findings and querying live database metrics. | ChromaDB (Vector Store) + LLM |
| **Telemetry & Alerts** | Monitored token usages, scanning latencies, Slack/Email/Webhook threshold notifications with cooldowns. | Plotly + SMTP/Slack API |

---

## ⚙️ System Architecture

### 1. Architecture Diagram
<!-- ARCHITECTURE_DIAGRAM_PLACEHOLDER_START -->
![System Architecture Flow](file:///Users/as-mac-1320/Downloads/genai-capstone/pdf-compliance-scanner/documentations/arch.png)
<!-- ARCHITECTURE_DIAGRAM_PLACEHOLDER_END -->

For additional details, refer to the [documentations/architecture.md](file:///Users/as-mac-1320/Downloads/genai-capstone/pdf-compliance-scanner/documentations/architecture.md) specification file.

### 2. High-Level System Flow (Mermaid)

```mermaid
flowchart TD
    User([Compliance Officer]) -->|Upload PDF / Connect DB| WebApp[Streamlit Web UI\nNoir Amber Theme]
    
    %% Main Operational Modes
    WebApp -->|Trigger PDF Scan| LangGraphDAG[LangGraph Parallel DAG]
    WebApp -->|Trigger DB Scan| AgentLayer[Multi-Agent Schema Crawler]
    WebApp -->|Conversational Q&A| Copilot[AI Copilot RAG]
    
    %% PDF Pipeline details
    subgraph PDF Scanning Pipeline
        LangGraphDAG --> Ingest[Ingest Node\nPyMuPDF]
        Ingest --> PII[PII Detector\nRegex + LLM Verify]
        Ingest --> Conf[Confidentiality Node\nSecrets Regex + LLM]
        Ingest --> Enc[Encoding Guard\nASCII / Language / Corruptions]
        Ingest --> Abuse[Abuse Detector\nKeyword + LLM Severity]
        PII & Conf & Enc & Abuse --> Agg[Aggregator & Risk Scorer]
        Agg --> RepGen[Report Generator\nReportLab PDF + JSON]
    end

    %% Data Source Pipeline details
    subgraph Data Source Scanning System
        AgentLayer --> MetaAgent[Metadata Agent\nSchema Discovery]
        MetaAgent --> DiffEngine[Change Engine\nStructural Drift Check]
        MetaAgent --> CompAgent[Compliance Agent\n25+ Regex Classifiers + LLM]
        CompAgent --> ChromaSync[Knowledge Indexer\nGenerate Natural-Language Findings]
    end
    
    %% Storage & Vector DB
    RepGen --> SQLite[(SQLite DB\ncompliance.db)]
    ChromaSync --> Chroma[(ChromaDB\nPersistent Vector Store)]
    SQLite -.->|Telemetry| Dashboard[Telemetry & Plotly Analytics]
    
    %% LLM & Observability
    PII & Conf & Abuse & CompAgent & Copilot <-->|Universal call_ai| LLM{AI Provider\nGroq / Gemini / Claude / Ollama}
    LLM -.->|Observability Logs| Langfuse[Langfuse Cloud\nRedacted Generation Traces]
    
    %% Alerts
    CompAgent & Agg -.->|Trigger Rules| AlertAgent[Alert Dispatcher\nSlack / Email / Webhook]
```

### 3. PDF Scan Pipeline (LangGraph DAG)

```mermaid
graph TD
    Start([Start Scan]) --> Ingest[ingest\nExtract Page Text & Encoding]
    Ingest --> pii_check[pii_check\n12 PII Pattern Matchers]
    Ingest --> confidentiality[confidentiality\n15 Credential/Key Matchers]
    Ingest --> encoding_check[encoding_check\n6 Deterministic Checks]
    Ingest --> abuse_check[abuse_check\n3-Layer Abuse Classifier]
    
    pii_check --> aggregate[aggregate\nMerge & Score Risk]
    confidentiality --> aggregate
    encoding_check --> aggregate
    abuse_check --> aggregate
    
    aggregate --> build_report[build_report\nGenerate PDF & JSON Reports]
    build_report --> End([Scan Complete])
    
    style Ingest fill:#141414,stroke:#E8A838,stroke-width:2px,color:#fff
    style aggregate fill:#141414,stroke:#E8A838,stroke-width:2px,color:#fff
    style build_report fill:#141414,stroke:#38C8E8,stroke-width:2px,color:#fff
```

### 4. Data Source Compliance Scan Pipeline

```mermaid
sequenceDiagram
    participant UI as Streamlit UI
    participant MA as Metadata Agent
    participant CE as Change Engine
    participant CA as Compliance Agent
    participant DB as SQLite / ChromaDB
    participant AA as Alert Agent

    UI->>MA: Run Compliance Scan
    MA->>MA: Connect and Extract Schema Metadata
    MA->>DB: Fetch Previous Schema Snapshot
    alt Schema Hash Changed
        MA->>CE: Run Structural & Row-Count Diff
        CE->>DB: Log Schema Changes (detected_changes)
    end
    MA->>CA: Trigger Classification
    CA->>CA: Match 25+ Regex Rules (PII, PCI, PHI, Confidential)
    CA->>CA: LLM-based Column Classification (Confidence >= 70%)
    CA->>DB: Save Scan Result & Daily Risk Trends
    CA->>DB: Index natural-language finding docs in ChromaDB
    CA->>AA: Check Violation Alert Rules
    alt Threshold Breached
        AA->>UI: Dispatch Notifications (Slack / Email / Webhook)
    end
```

---

## 🛠️ Technology Stack

*   **Frontend UI:** [Streamlit](https://streamlit.io/) (>= 1.55) - styled with custom **Noir Amber** CSS layout.
*   **Orchestration:** [LangGraph](https://github.com/langchain-ai/langgraph) (>= 1.1) for parallel compliance execution.
*   **Vector Database:** [ChromaDB](https://www.trychroma.com/) (>= 0.3) for Persistent Retrieval-Augmented Generation (RAG).
*   **Inference Abstraction:** Unified AI Gateway supporting runtime switching between **Groq**, **Google Gemini**, **Anthropic**, and local **Ollama** backends.
*   **Database:** Local SQL database using **SQLite** with WAL (Write-Ahead Logging) enabled.
*   **Parsing & Generation:** [PyMuPDF (fitz)](https://pymupdf.readthedocs.io/en/latest/) for extraction; [ReportLab](https://www.reportlab.com/) for PDF report building.
*   **Observability:** [Langfuse](https://langfuse.com/) (>= 2.0) for execution tracing, cost tracking, and token counting.

---

## ⚙️ Environment & Configuration

Configure your environment variables in the [.env](file:///Users/as-mac-1320/Downloads/genai-capstone/pdf-compliance-scanner/.env) file (use [.env.example](file:///Users/as-mac-1320/Downloads/genai-capstone/pdf-compliance-scanner/.env.example) as reference):

```bash
# Gateway Selection: groq | gemini | anthropic | ollama
AI_PROVIDER=groq

# AI Provider Credentials
GROQ_API_KEY=gsk_...
GOOGLE_API_KEY=AIza...
ANTHROPIC_API_KEY=sk-ant-...

# Observability Configuration
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com

# SMTP Email Alerts Configuration (Optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=sender@example.com
SMTP_PASSWORD=app_password_here
```

### Supported Connectors (Lazy-Loaded)
The Data Source Scanner supports 10 distinct connectors. Note that the required packages are **lazy-loaded**; you only need to install what you use:
*   **Databases:** PostgreSQL (`psycopg2-binary`), MySQL (`pymysql`), MongoDB (`pymongo`), SQL Server (`pyodbc`).
*   **Cloud Stores:** AWS S3 (`boto3`), Azure ADLS Gen2 (`azure-storage-file-datalake`), Google Cloud Storage (`google-cloud-storage`).
*   **Warehouses:** Snowflake (`snowflake-connector-python`), BigQuery (`google-cloud-bigquery`), Databricks (`databricks-sql-connector`).

---

## 📦 Getting Started

### Prerequisites
*   Python 3.11+
*   pip / virtualenv

### 1. Local Setup
```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/pdf-compliance-scanner.git
cd pdf-compliance-scanner

# Initialize virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install required dependencies
pip install -r requirements.txt

# Copy and update the environment template
cp .env.example .env
```

### 2. Run the Streamlit Application
```bash
streamlit run app/main.py
```
Access the dashboard at `http://localhost:8501`.

### 3. Docker Deployment
```bash
# Build and run using Docker Compose
docker-compose up --build
```
This mounts local volumes to persist reports in [reports](file:///Users/as-mac-1320/Downloads/genai-capstone/pdf-compliance-scanner/reports) and the SQLite database in `storage/`.

---

## 🔍 Observability & Testing

### Test Suite Execution
Run the unit and integration tests (which utilize mocked LLM responses):
```bash
pytest tests/ -v
```

### Observability Traces
*   All LLM calls are traced using the `@observe()` decorator via Langfuse.
*   Traces include execution latency, total token counts, and input/output schema.
*   **Privacy Guard:** Strict user data privacy is maintained; text inputs and outputs sent to LLMs are systematically replaced with `<redacted>` in the Langfuse traces, logging only token counts, execution states, and provider names.

---

## 🗄️ Database Schema

The SQLite database [storage/compliance.db](file:///Users/as-mac-1320/Downloads/genai-capstone/pdf-compliance-scanner/storage/compliance.db) consists of **12 core tables**:

### PDF Scanning
*   `scans`: Keeps historical records of scanned PDFs, status, risk parameters, token consumption, and report files.

### Data Source Scanning & Alerts
*   `data_sources`: Registry of configured databases, storage buckets, and warehouses.
*   `metadata_snapshots`: History of schema metadata structures and snapshot hashes.
*   `column_metadata`: Individual column structural configurations.
*   `detected_changes`: Tracked structural schema changes (new/dropped tables/columns).
*   `ds_scan_runs` & `ds_scan_results`: History of warehouse runs and identified columns.
*   `risk_trends` & `compliance_drift`: Daily aggregated compliance percentages and risk histories.
*   `alert_configs` & `alert_history`: Active channels, threshold rules, and alerts dispatch ledger.