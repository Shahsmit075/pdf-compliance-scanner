# app/main.py
"""
Streamlit entry point — Noir Amber war-room landing page.
"""
import sys
import os
# Inject project root path to allow absolute imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
import textwrap
from app.styles.theme import GLOBAL_CSS

st.set_page_config(
    page_title="PDF Compliance Scanner",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

# ── SIDEBAR ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(textwrap.dedent("""
    <div style="padding: 4px 0 20px">
      <div style="font-family:'Space Mono',monospace; font-size:21px; font-weight:700; color:var(--amber); letter-spacing:0.05em; margin-bottom:4px">
        COMPLIANCE<br>SCANNER
      </div>
      <div style="font-family:'Space Mono',monospace; font-size:10px; color:var(--text-muted); letter-spacing:0.05em; text-transform:uppercase">
        AI-Powered Document Compliance Guard
      </div>
    </div>
    """), unsafe_allow_html=True)

    with st.expander("⚙️ API CONFIGURATION", expanded=False):
        import os
        st.markdown("<div style='font-size:13px; color:var(--text-muted); margin-bottom:8px'>Override .env keys dynamically</div>", unsafe_allow_html=True)
        
        # Groq
        groq_key = st.text_input("Groq API Key", value=os.environ.get("GROQ_API_KEY", ""), type="password", help="Required for Llama3 models")
        if groq_key:
            os.environ["GROQ_API_KEY"] = groq_key
            
        # Gemini
        gemini_key = st.text_input("Gemini API Key", value=os.environ.get("GOOGLE_API_KEY", ""), type="password", help="Required if AI_PROVIDER=gemini")
        if gemini_key:
            os.environ["GOOGLE_API_KEY"] = gemini_key
            
        # Anthropic
        anthropic_key = st.text_input("Anthropic API Key", value=os.environ.get("ANTHROPIC_API_KEY", ""), type="password", help="Required if AI_PROVIDER=anthropic")
        if anthropic_key:
            os.environ["ANTHROPIC_API_KEY"] = anthropic_key

    st.markdown(textwrap.dedent("""
    <hr style="border:none;border-top:1px solid var(--border);margin:20px 0">
    <div class="caption-label" style="margin-bottom:10px">PIPELINE STACK</div>
    <div style="font-family:'JetBrains Mono',monospace; font-size:13px; color:var(--text-muted); line-height:1.9">
      Groq Llama 3<br>
      LangGraph DAG<br>
      PyMuPDF · ReportLab<br>
      ChromaDB RAG<br>
      SQLite Storage
    </div>
    <hr style="border:none;border-top:1px solid var(--border);margin:20px 0">
    <div style="font-family:'Space Mono',monospace; font-size:11px; color:#3A3A3A; letter-spacing:0.1em">
      PDF · DB · S3 · WAREHOUSE<br>
      ALL SYSTEMS OPERATIONAL
    </div>
    """), unsafe_allow_html=True)

# ── HERO BANNER ────────────────────────────────────────────────────────────────
st.markdown(textwrap.dedent("""
<div style="
  background: linear-gradient(135deg, #0D0D0D 0%, #1A1200 50%, #0D0D0D 100%);
  border-bottom: 1px solid #2A2A2A;
  padding: 48px 32px 36px;
  position: relative;
  overflow: hidden;
  border-radius: 4px;
  margin-bottom: 24px;
">
  <!-- Noise grid pattern -->
  <div style="
    position:absolute; inset:0;
    background-image: radial-gradient(circle, #E8A838 1px, transparent 1px);
    background-size: 32px 32px;
    opacity: 0.04;
  "></div>

  <!-- Diagonal decorative line -->
  <div style="
    position:absolute; width:1px; height:120%;
    background:linear-gradient(to bottom, transparent, #E8A838 40%, transparent);
    opacity:0.15; right:20%; top:-10%; transform:rotate(15deg);
  "></div>

  <!-- System Online badge -->
  <div style="position:relative;z-index:1;margin-bottom:20px">
    <span style="
      display:inline-flex; align-items:center; gap:8px;
      font-family:'Space Mono',monospace; font-size:13px; color:#4FD180;
      letter-spacing:0.2em; text-transform:uppercase;
    ">
      <span style="
        display:inline-block; width:6px; height:6px; border-radius:50%;
        background:#4FD180; animation: pulseDot 2s ease-in-out infinite;
      "></span>
      SYSTEM ONLINE
    </span>
  </div>

  <!-- Main title -->
  <div style="position:relative;z-index:1">
    <h1 style="
      font-family:'Space Mono',monospace; font-weight:700;
      font-size:clamp(36px,5vw,64px); line-height:1.1;
      margin:0; padding:0;
    ">
      <span style="color:#F0EDE6">PDF COMPLIANCE</span><br>
      <span style="color:#E8A838;text-shadow:0 0 40px rgba(232,168,56,0.3)">SCANNER</span>
    </h1>
  </div>

  <!-- Subtitle -->
  <p style="
    position:relative; z-index:1;
    font-family:'DM Sans',sans-serif; color:#7A7A7A;
    font-size:18px; letter-spacing:0.04em; margin-top:12px;
  ">
    Automated PII · Confidentiality · Encoding · Abuse Detection
  </p>

  <!-- Version tag -->
  <div style="
    position:absolute; bottom:16px; right:24px; z-index:1;
    font-family:'Space Mono',monospace; font-size:13px; color:#3A3A3A;
  ">
    v2.0 — NOIR AMBER BUILD
  </div>
</div>
"""), unsafe_allow_html=True)

# ── FEATURE CARDS (2×2 grid) ──────────────────────────────────────────────────
cards = [
    {
        "icon": "◈",
        "badge_class": "badge-high",
        "badge_label": "HIGH",
        "title": "PII DETECTION",
        "desc": "Emails, phone numbers, Aadhaar, SSN, passports — nothing slips past. Regex speed + AI brains.",
        "stat": "12 pattern types · dual-engine",
        "delay": "0s",
    },
    {
        "icon": "⬡",
        "badge_class": "badge-critical",
        "badge_label": "CRITICAL",
        "title": "CONFIDENTIALITY",
        "desc": "AWS keys, GitHub tokens, passwords, salary data. If it shouldn't be here, it won't stay quiet.",
        "stat": "15 credential patterns · AI semantic",
        "delay": "0.08s",
    },
    {
        "icon": "⟁",
        "badge_class": "badge-medium",
        "badge_label": "MEDIUM",
        "title": "ENCODING GUARD",
        "desc": "UTF-8 validation, OCR corruption, multilingual content. Your documents should speak one language.",
        "stat": "6 check types · rule-based",
        "delay": "0.16s",
    },
    {
        "icon": "⚠",
        "badge_class": "badge-critical",
        "badge_label": "CRITICAL",
        "title": "ABUSE DETECTION",
        "desc": "Threats, hate speech, harassment, illegal content. Three detection layers because one is never enough.",
        "stat": "3-layer detection · zero-tolerance",
        "delay": "0.24s",
    },
]

row1_l, row1_r = st.columns(2)
row2_l, row2_r = st.columns(2)
cols = [row1_l, row1_r, row2_l, row2_r]

for col, card in zip(cols, cards):
    with col:
        st.markdown(textwrap.dedent(f"""
        <div class="feature-card animate-fadein" style="animation-delay:{card['delay']}">
          <div class="card-icon-line">
            <span class="card-icon">{card['icon']}</span>
            <span class="badge {card['badge_class']}">{card['badge_label']}</span>
          </div>
          <h3 class="card-title">{card['title']}</h3>
          <p class="card-desc">{card['desc']}</p>
          <div class="card-footer-line">
            <span class="mono" style="font-size:13px;color:var(--text-muted)">{card['stat']}</span>
          </div>
        </div>
        """), unsafe_allow_html=True)

# ── ANIMATED STATS TICKER ─────────────────────────────────────────────────────
st.markdown(textwrap.dedent("""
<div class="stats-ticker-wrap">
  <div class="stats-ticker">
    <span class="ticker-item">⬤ PII PATTERNS LOADED: 12</span>
    <span class="ticker-sep">///</span>
    <span class="ticker-item">⬤ CREDENTIAL CHECKS: 15</span>
    <span class="ticker-sep">///</span>
    <span class="ticker-item">⬤ ABUSE CATEGORIES: 6</span>
    <span class="ticker-sep">///</span>
    <span class="ticker-item">⬤ AI PROVIDER: GROQ LLAMA 3</span>
    <span class="ticker-sep">///</span>
    <span class="ticker-item">⬤ PIPELINE: LANGGRAPH DAG</span>
    <span class="ticker-sep">///</span>
    <span class="ticker-item">⬤ REPORT ENGINE: REPORTLAB</span>
    <span class="ticker-sep">///</span>
    <!-- duplicate for seamless loop -->
    <span class="ticker-item">⬤ PII PATTERNS LOADED: 12</span>
    <span class="ticker-sep">///</span>
    <span class="ticker-item">⬤ CREDENTIAL CHECKS: 15</span>
    <span class="ticker-sep">///</span>
    <span class="ticker-item">⬤ ABUSE CATEGORIES: 6</span>
    <span class="ticker-sep">///</span>
    <span class="ticker-item">⬤ AI PROVIDER: GROQ LLAMA 3</span>
    <span class="ticker-sep">///</span>
    <span class="ticker-item">⬤ PIPELINE: LANGGRAPH DAG</span>
    <span class="ticker-sep">///</span>
    <span class="ticker-item">⬤ REPORT ENGINE: REPORTLAB</span>
    <span class="ticker-sep">///</span>
  </div>
</div>
"""), unsafe_allow_html=True)

# ── BOTTOM NAVIGATION HINT ────────────────────────────────────────────────────
st.markdown(textwrap.dedent("""
<div style="text-align:center; padding: 32px 0 16px; animation: fadeSlideUp 0.5s ease 0.4s both;">
  <p style="font-family:'Space Mono',monospace; font-size:14px; color:var(--text-muted); letter-spacing:0.15em; text-transform:uppercase">
    ← NAVIGATE VIA SIDEBAR TO BEGIN SCANNING
  </p>
  <div style="width:1px;height:32px;background:linear-gradient(to bottom,var(--amber),transparent);margin:12px auto 0;"></div>
</div>
"""), unsafe_allow_html=True)
