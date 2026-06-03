# Architecture Overview: PDF Compliance Scanner

The **PDF Compliance Scanner** operates as a **local web application**, not a browser plugin. 
When you run `streamlit run app/main.py`, it spins up a local web server on your machine. All your files and data are kept on your device, with the only external communication being the API calls to the AI models (unless you use a local AI model).

Here is a breakdown of the architecture:

## 1. Storage (Local)
The database is created and maintained **entirely on your device**. 
- It uses **SQLite** (`storage/compliance.db`), a lightweight, file-based database that requires no separate server setup.
- Scan metadata and results are stored locally, meaning no third party has access to your scan history.

## 2. Processing Engine (Local + Cloud AI)
The processing is split into two parts:
- **Local Execution:** Document ingestion (reading the PDF), text extraction (using `PyMuPDF`), regex-based scanning, LangGraph state management, and report generation all happen on your local CPU.
- **AI Inference (Cloud or Local):** The heavy lifting of semantic understanding (detecting context-based PII, abuse, or secrets) is outsourced to an LLM provider (like Groq, Gemini, or Claude) via API calls. However, if you configure it to use **Ollama**, even the AI inference happens 100% locally on your machine.

---

## Architecture Diagrams

### High-Level Architecture Flow

```mermaid
flowchart TD
    User([User]) -->|Uploads PDF| UI[Streamlit UI\nlocalhost:8501]
    UI -->|Triggers| Pipeline[LangGraph Pipeline]
    
    subgraph Local Machine Processing
        Pipeline --> Ingest[Ingest Node\nPyMuPDF Extraction]
        Ingest --> DetectorNodes[Detection Nodes\nRegex + AI]
        DetectorNodes --> Aggregator[Aggregator Node]
        Aggregator --> Report[Report Generation]
    end
    
    subgraph Storage layer
        Aggregator --> DB[(SQLite Database\ncompliance.db)]
        Report --> PDF[PDF Reports Folder]
    end
    
    subgraph AI Layer
        DetectorNodes <-->|Prompts / JSON Results| AIProvider{AI Provider}
    end
    
    AIProvider -.->|Option 1| CloudAPI[Cloud APIs\nGroq / Gemini / Anthropic]
    AIProvider -.->|Option 2| LocalAI[Local AI\nOllama]
    
    style User fill:#f9f9f9,stroke:#333,stroke-width:2px
    style UI fill:#FFDB58,stroke:#333,stroke-width:2px
    style DB fill:#4CAF50,stroke:#333,stroke-width:2px
```

### Detection Node Breakdown

Here is a closer look at what happens inside the `Detection Nodes` step. The pipeline uses **LangGraph** to process multiple checks in parallel.

```mermaid
flowchart LR
    Ingest[Text Extraction] --> PII[PII Detector]
    Ingest --> Confid[Confidentiality Guard]
    Ingest --> Abuse[Abuse Detector]
    Ingest --> Enc[Encoding Guard]
    
    PII --> AI[Groq LLM API]
    Confid --> AI
    Abuse --> AI
    Enc --> LocalRegex[Local Regex/Rules]
    
    AI --> Agg[Aggregator]
    LocalRegex --> Agg
    Agg --> Final[Final Risk Score]
```

## Summary
- **Is it a plugin?** No, it is a standalone Python web app (Streamlit).
- **Where is the DB?** On your local hard drive (`storage/compliance.db`).
- **Where does processing happen?** 
  - Text extraction, rule checking, and report generation happen on your device.
  - The AI analysis runs on Groq's servers (by default), meaning the extracted text is temporarily sent to Groq for analysis. If you want 100% local privacy, you can switch the `AI_PROVIDER` to `ollama`.
