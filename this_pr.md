# PR Summary: Telemetry, Analytics & PDF Layout Fixes

## 📊 Telemetry & Analytics Dashboard
- **New Page**: Added `app/pages/04_analytics.py` styled in Noir Amber dark theme.
- **KPI Metrics**: Total Scans, Average Latency, and Total Tokens.
- **Charts**: Scans over time, AI token usage, Risk profiles, and AI provider breakdown.
- **Scan Log**: A detailed history table of all completed scans.
- **Database**: Extended SQLite `scans` table with new telemetry columns (`total_tokens`, `execution_time_sec`, `ai_provider`) via graceful migrations in `storage/database.py`.

## 🛡️ Langfuse v4 Tracing Integration
- **SDK Upgrade**: Tracing refactored to use the modern, OpenTelemetry-native **Langfuse v4 SDK**.
- **DAG Tracing**: Decorated the LangGraph execution loop and all seven compliance nodes (`ingest`, `pii_check`, `confidentiality`, `encoding_check`, `abuse_check`, `aggregate`, `build_report`) with `@observe` to generate structured, hierarchical waterfall traces in Langfuse Cloud.
- **Context Propagation**: Used `propagate_attributes` to automatically bind unique `upload_id` (as `session_id`), tags, and PDF file names to all nested trace observations.
- **Redaction & Privacy**: Configured generation tracking in `config/ai_provider.py` to redact raw PDF user input and AI outputs, transmitting only system prompts, latencies, and token counts.

## 📄 PDF Export Layout Fixes
- **Text Wrapping**: Wrapped Detailed Findings table elements (`Type`, `Entity`, `Matched Value`, `Context / Snippet`) inside ReportLab `Paragraph` flowables to support text wrapping.
- **Overlap Prevention**: Added `wordWrap='CJK'` and `splitLongWords=True` to prevent overflow of long contiguous strings (e.g. database credentials and API keys without space boundaries).
- **Grid Tuning**: Redistributed column widths (`colWidths=[2.0*cm, 2.2*cm, 2.6*cm, 1.0*cm, 1.2*cm, 1.5*cm, 6.7*cm]`) to align cells and avoid vertical or horizontal overlapping.

## ⚙️ Dependencies & Refactoring
- **Model Upgrades**: Replaced decommissioned `llama3-70b-8192` with `llama-3.3-70b-versatile` across configurations.
- **State Schema**: Added node-specific token keys to the `PipelineState` to prevent LangGraph concurrent write conflicts.
- **Requirements**: Pinned `langfuse`, `pandas`, and `httpx==0.27.2` (to resolve groq client conflicts).
- **Test Suite**: Updated unit tests in `tests/` to align with the database migrations and node-specific token keys. All 10 tests passing.
