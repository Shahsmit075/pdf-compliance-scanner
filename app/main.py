# app/main.py
"""
Streamlit entry point — configures the app and renders the main navigation.
"""
import streamlit as st
from pathlib import Path

st.set_page_config(
    page_title="PDF Compliance Scanner",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #1e3a5f 0%, #2c3e50 100%);
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
        color: white;
        text-align: center;
    }
    .risk-critical { color: #C0392B; font-weight: bold; }
    .risk-high { color: #E67E22; font-weight: bold; }
    .risk-medium { color: #F39C12; font-weight: bold; }
    .risk-low { color: #27AE60; font-weight: bold; }
    .metric-card {
        background: #262730;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #FF4B4B;
        margin-bottom: 10px;
    }
    .stProgress .st-bo { background-color: #FF4B4B; }
</style>
""", unsafe_allow_html=True)

# Sidebar navigation
with st.sidebar:
    st.markdown("## 🛡️ PDF Compliance Scanner")
    st.markdown("---")
    st.markdown("""
    **Powered by:**
    - 🤖 Groq Llama 3 (Free AI)
    - 🔗 LangGraph Orchestration
    - 📄 PyMuPDF Extraction
    - 📊 ReportLab Reports
    """)
    st.markdown("---")
    st.caption("v1.0 · Compliance Checks: PII · Confidential · Encoding · Abuse")

# Main page content
st.markdown("""
<div class="main-header">
    <h1>🛡️ AI-Powered PDF Compliance Scanner</h1>
    <p>Automatically detect PII, confidential data, encoding issues, and abusive content</p>
</div>
""", unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.info("📋 **PII Detection**\nEmails, phones, IDs, addresses")
with col2:
    st.warning("🔐 **Confidentiality**\nAPI keys, trade secrets, credentials")
with col3:
    st.success("🔤 **Encoding Check**\nUTF-8 validation, language detection")
with col4:
    st.error("⚠️ **Abuse Detection**\nHate speech, harassment, unlawful content")

st.markdown("---")
st.markdown("### 👈 Select a page from the sidebar to get started")
st.markdown("1. **📤 Upload & Scan** — Upload your PDF and run compliance checks")
st.markdown("2. **⚙️ Compliance Rules** — Configure detection rules and thresholds")
st.markdown("3. **📊 View Reports** — Browse and download past scan reports")
