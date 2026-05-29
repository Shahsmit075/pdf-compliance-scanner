# app/pages/07_copilot.py
"""
Module 07 — AI Copilot
RAG-backed compliance assistant. Answers questions about your data sources, scan results, and policy.
"""
import streamlit as st
import textwrap
from datetime import datetime

from app.styles.theme import GLOBAL_CSS
from storage.database import DataSourceDB, init_ds_db
from connectors.factory import CONNECTOR_META

st.set_page_config(page_title="AI Copilot", page_icon="⟁", layout="wide")
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
init_ds_db()

# ── EXTRA COPILOT STYLES ───────────────────────────────────────────────────────
st.markdown("""
<style>
.copilot-msg-user {
  background:rgba(232,168,56,0.10);
  border:1px solid rgba(232,168,56,0.25);
  border-radius:4px 4px 2px 4px;
  padding:14px 18px;
  margin:0 0 12px 48px;
  font-family:'DM Sans',sans-serif;
  font-size:16px;
  color:#f5f0e8;
}
.copilot-msg-ai {
  background:rgba(255,255,255,0.04);
  border:1px solid rgba(255,255,255,0.08);
  border-radius:2px 4px 4px 4px;
  padding:14px 18px;
  margin:0 48px 12px 0;
  font-family:'DM Sans',sans-serif;
  font-size:16px;
  color:#c9c4b8;
  line-height:1.7;
}
.copilot-msg-ai strong { color:#E8A838; }
.copilot-label {
  font-family:'Space Mono',monospace;
  font-size:11px;
  letter-spacing:0.1em;
  color:#6b7280;
  margin-bottom:4px;
}
.suggested-chip {
  display:inline-block;
  background:rgba(125,211,252,0.08);
  border:1px solid rgba(125,211,252,0.2);
  border-radius:20px;
  padding:5px 14px;
  font-family:'Space Mono',monospace;
  font-size:12px;
  color:#7dd3fc;
  margin:4px;
  cursor:pointer;
}
</style>
""", unsafe_allow_html=True)

# ── PAGE HEADER ────────────────────────────────────────────────────────────────
col_head, col_clear = st.columns([5, 1])
with col_head:
    st.markdown(textwrap.dedent("""
    <div class="animate-fadein" style="padding:0 0 20px">
      <div class="caption-label">MODULE 07</div>
      <h1 style="font-family:'Space Mono',monospace;font-size:33px;font-weight:700;color:var(--text);margin:6px 0 4px">
        AI <span style="color:var(--amber)">COPILOT</span>
      </h1>
      <p style="color:var(--text-muted);font-size:17px;margin:0">
        Ask anything about your data sources, scan results, compliance policies, and risk posture.
      </p>
    </div>
    """), unsafe_allow_html=True)
with col_clear:
    st.markdown('<div style="padding-top:52px"></div>', unsafe_allow_html=True)
    if st.button("✕ CLEAR", use_container_width=True):
        st.session_state.copilot_messages = []
        st.rerun()

# ── SOURCE CONTEXT SELECTOR ────────────────────────────────────────────────────
sources = DataSourceDB.get_all_sources()
source_options = {"All Sources": None}
for s in sources:
    meta = CONNECTOR_META.get(s["source_type"], {"icon": "🔌"})
    source_options[f"{meta['icon']} {s['name']}"] = s["source_id"]

col_ctx, col_rag_info = st.columns([2, 3])
with col_ctx:
    selected_ctx = st.selectbox("Context", options=list(source_options.keys()),
                                label_visibility="collapsed")
    context_source_id = source_options.get(selected_ctx)

with col_rag_info:
    try:
        from rag.vector_store import get_collection_stats
        stats = get_collection_stats()
        total_docs = stats.get("total_documents", 0)
        st.markdown(textwrap.dedent(f"""
        <div style="display:inline-flex;align-items:center;gap:12px;background:var(--surface);border:1px solid var(--border);border-radius:3px;padding:8px 16px;font-family:'JetBrains Mono',monospace;font-size:13px">
          <span style="color:var(--text-muted)">RAG STORE</span>
          <span style="color:var(--{'amber' if total_docs > 0 else 'text-muted'})">{total_docs} documents indexed</span>
        </div>
        """), unsafe_allow_html=True)
    except Exception:
        pass

# ── SUGGESTED PROMPTS ──────────────────────────────────────────────────────────
SUGGESTED = [
    "What PII columns were found in the last scan?",
    "Which source has the highest risk score?",
    "What changed in the schema since last week?",
    "Explain what PCI DSS compliance means for our data.",
    "Show me columns that should be encrypted immediately.",
    "What is the compliance score across all sources?",
]

if "copilot_messages" not in st.session_state:
    st.session_state.copilot_messages = []

if not st.session_state.copilot_messages:
    st.markdown('<div class="caption-label" style="margin-bottom:6px">SUGGESTED QUESTIONS</div>', unsafe_allow_html=True)
    chips_html = "".join(
        f'<span class="suggested-chip">{q}</span>' for q in SUGGESTED
    )
    st.markdown(f'<div>{chips_html}</div>', unsafe_allow_html=True)

    # Clickable suggestion buttons (Streamlit can't handle HTML click events directly)
    cols = st.columns(3)
    for i, q in enumerate(SUGGESTED):
        with cols[i % 3]:
            if st.button(q, key=f"suggest_{i}", use_container_width=True):
                st.session_state.copilot_messages.append({"role": "user", "content": q})
                st.rerun()

# ── CHAT HISTORY ───────────────────────────────────────────────────────────────
for msg in st.session_state.get("copilot_messages", []):
    if msg["role"] == "user":
        st.markdown(textwrap.dedent(f"""
        <div class="copilot-label">YOU</div>
        <div class="copilot-msg-user">{msg['content']}</div>
        """), unsafe_allow_html=True)
    else:
        st.markdown(textwrap.dedent(f"""
        <div class="copilot-label">⟁ COPILOT</div>
        <div class="copilot-msg-ai">{msg['content']}</div>
        """), unsafe_allow_html=True)

# ── INPUT BOX ──────────────────────────────────────────────────────────────────

def _get_copilot_answer(question: str, source_id: str = None) -> str:
    """
    Generate a RAG-backed answer using:
    1. ChromaDB similarity search for relevant findings
    2. Database context (recent scans, risk trends, changes)
    3. AI LLM for final answer generation
    """
    rag_context = ""
    db_context = ""

    # ── 1. RAG retrieval ─────────────────────────────────────────────────
    try:
        from rag.vector_store import query_similar
        where = {"source_id": source_id} if source_id else None
        results = query_similar(question, n_results=5, where=where)
        docs = results.get("documents", [[]])[0]
        if docs:
            rag_context = "\n\n".join(f"[Finding {i+1}]\n{d}" for i, d in enumerate(docs))
    except Exception:
        rag_context = ""

    # ── 2. Database context ───────────────────────────────────────────────
    try:
        sources = DataSourceDB.get_all_sources()
        recent_scans = DataSourceDB.get_scan_runs(source_id, limit=5)
        db_parts = []

        if sources:
            src_summary = "; ".join(
                f"{s['name']} ({s['source_type']}, status:{s['status']})" for s in sources
            )
            db_parts.append(f"Registered Sources: {src_summary}")

        if recent_scans:
            scan_summary = "; ".join(
                f"Scan {r['scan_id'][:8]} on {r.get('started_at','')[:10]}: "
                f"{r.get('total_flags',0)} flags, risk={r.get('highest_risk','?')}"
                for r in recent_scans[:3]
            )
            db_parts.append(f"Recent Scans: {scan_summary}")

        if source_id:
            latest_trend = DataSourceDB.get_risk_trends(source_id, days=7)
            if latest_trend:
                lt = latest_trend[-1]
                db_parts.append(
                    f"Latest Risk Trend: score={lt['risk_score']:.1f}, "
                    f"compliance={lt['compliance_pct']:.1f}%, violations={lt['total_violations']}"
                )
            changes = DataSourceDB.get_changes(source_id, limit=5)
            if changes:
                chg_summary = "; ".join(
                    f"{c.get('change_type','?')} on {c.get('entity_name','?')} ({c.get('severity','?')})"
                    for c in changes[:3]
                )
                db_parts.append(f"Recent Schema Changes: {chg_summary}")

        db_context = "\n".join(db_parts)
    except Exception:
        db_context = ""

    # ── 3. AI call ────────────────────────────────────────────────────────
    try:
        from config.ai_provider import call_ai

        system_prompt = """You are a data compliance AI copilot — sharp, precise, knowledgeable.
You help engineers and data teams understand their compliance posture and act on findings.
You have access to real-time scan results, schema change logs, and risk trends.

Guidelines:
- Be concise and actionable
- Use specific data from the context when available
- For PII/PCI/PHI findings, always mention the severity and recommended remediation
- Use markdown formatting (bold for key terms, bullet points for lists)
- If you don't have specific data, say so clearly and provide general guidance
- Never make up scan results that aren't in the context

Your personality: Professional but direct. You don't sugarcoat compliance risks."""

        context_block = ""
        if rag_context:
            context_block += f"\n\n## Relevant Compliance Findings (from RAG store)\n{rag_context}"
        if db_context:
            context_block += f"\n\n## Current System State\n{db_context}"

        user_message = f"Question: {question}{context_block}"
        return call_ai(system_prompt=system_prompt, user_message=user_message, max_tokens=800)

    except Exception as e:
        if db_context:
            return (
                f"⚠ *AI provider unavailable.* Based on available data:\n\n"
                f"{db_context}\n\n"
                f"Configure an AI provider (Groq/Gemini/Anthropic) in Settings for full copilot capability."
            )
        return (
            "⚠ AI provider not configured. "
            "Set up an API key in the Settings page to use the Copilot. "
            "Run scans first to populate the knowledge base."
        )


with st.form("copilot_form", clear_on_submit=True):
    col_input, col_send = st.columns([5, 1])
    with col_input:
        user_input = st.text_input(
            "Ask Copilot",
            placeholder="e.g. What PII columns were found in my Postgres source?",
            label_visibility="collapsed",
        )
    with col_send:
        submitted = st.form_submit_button("SEND ▶", type="primary", use_container_width=True)

# ── PROCESS QUERY ──────────────────────────────────────────────────────────────
if submitted and user_input.strip():
    user_q = user_input.strip()
    st.session_state.copilot_messages.append({"role": "user", "content": user_q})

    with st.spinner("⟁ Thinking…"):
        answer = _get_copilot_answer(user_q, context_source_id)

    st.session_state.copilot_messages.append({"role": "assistant", "content": answer})
    st.rerun()

