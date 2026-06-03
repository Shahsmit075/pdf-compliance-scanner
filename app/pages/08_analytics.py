# app/pages/08_analytics.py
"""
Telemetry & Analytics page — displays LLM token usage, latency, and cost savings metrics.
Noir Amber UI design.
"""
import sys
import os
# Inject project root path to allow absolute imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import textwrap
from datetime import datetime
from storage.database import get_all_scans
from app.styles.theme import GLOBAL_CSS
from app.components.ui import metric_grid, empty_state, section_divider

# ── Noir Amber Plotly theme helper ────────────────────────────────────────────
def _noir_bar(x_vals, y_vals, color: str = "#E8A838", name: str = "") -> go.Figure:
    """Create a Plotly bar chart styled for the Noir Amber dark theme."""
    fig = go.Figure(go.Bar(
        x=x_vals,
        y=y_vals,
        marker_color=color,
        marker_line_color="rgba(0,0,0,0)",
        name=name,
    ))
    fig.update_layout(
        paper_bgcolor="#141414",
        plot_bgcolor="#141414",
        font=dict(family="'Space Mono', monospace", color="#7A7A7A", size=11),
        margin=dict(l=0, r=0, t=8, b=0),
        height=220,
        showlegend=False,
        xaxis=dict(
            showgrid=False,
            zeroline=False,
            tickfont=dict(color="#7A7A7A", size=10),
            linecolor="#2A2A2A",
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="#2A2A2A",
            zeroline=False,
            tickfont=dict(color="#7A7A7A", size=10),
            linecolor="#2A2A2A",
        ),
    )
    return fig

st.set_page_config(page_title="Telemetry & Analytics", page_icon="📊", layout="wide", initial_sidebar_state="expanded")
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

# ── PAGE HEADER ────────────────────────────────────────────────────────────────
st.markdown(textwrap.dedent("""
<div class="animate-fadein" style="padding:0 0 24px">
  <div class="caption-label">MODULE 08</div>
  <h1 style="font-family:'Space Mono',monospace; font-size:33px; font-weight:700; color:var(--text); margin:6px 0 4px; letter-spacing:-0.01em">
    TELEMETRY <span style="color:var(--amber)">&</span> ANALYTICS
  </h1>
  <p style="color:var(--text-muted); font-size:17px; margin:0">
    Monitor pipeline latency, token consumption, and estimated LLM cost efficiency.
  </p>
</div>
"""), unsafe_allow_html=True)

scans = get_all_scans()

# ── EMPTY STATE ────────────────────────────────────────────────────────────────
if not scans:
    st.markdown(
        empty_state(
            title="NO TELEMETRY RECORDED",
            subtitle="Your analytics board is empty. Run a scan to populate telemetry.",
            icon="📊"
        ),
        unsafe_allow_html=True
    )
    st.stop()

# Load into DataFrame
df = pd.DataFrame(scans)

# Ensure numeric types
if "total_tokens" in df.columns:
    df["total_tokens"] = pd.to_numeric(df["total_tokens"], errors="coerce").fillna(0).astype(int)
else:
    df["total_tokens"] = 0

if "execution_time_sec" in df.columns:
    df["execution_time_sec"] = pd.to_numeric(df["execution_time_sec"], errors="coerce").fillna(0.0).astype(float)
else:
    df["execution_time_sec"] = 0.0

if "total_flags" in df.columns:
    df["total_flags"] = pd.to_numeric(df["total_flags"], errors="coerce").fillna(0).astype(int)
else:
    df["total_flags"] = 0

# ── KPI METRICS GRID ──────────────────────────────────────────────────────────
total_scans = len(df)
avg_latency = f"{df['execution_time_sec'].mean():.2f}s"
total_tokens = f"{df['total_tokens'].sum():,}"
# cost_saved = f"${(df['total_tokens'].sum() * 0.03 / 1000):.2f}"  # Est $0.03 per 1K tokens comparison baseline

metrics = [
    {"label": "TOTAL SCANS", "value": total_scans, "color": "var(--amber)"},
    {"label": "AVG LATENCY", "value": avg_latency, "color": "var(--ice)"},
    {"label": "TOTAL TOKENS", "value": total_tokens, "color": "var(--amber)"},
    # {"label": "EST. COST SAVED", "value": cost_saved, "color": "var(--low)"}
]

st.markdown(metric_grid(metrics), unsafe_allow_html=True)

# ── CHARTS SECTIONS ───────────────────────────────────────────────────────────
if "scanned_at" in df.columns:
    df["scanned_at"] = pd.to_datetime(df["scanned_at"])
    df["date"] = df["scanned_at"].dt.date
else:
    df["date"] = datetime.now().date()

col1, col2 = st.columns(2)

with col1:
    st.markdown('<div class="caption-label" style="margin-bottom:8px">SCANS OVER TIME</div>', unsafe_allow_html=True)
    timeline_df = df.groupby("date").size().reset_index(name="scans")
    st.plotly_chart(
        _noir_bar([str(d) for d in timeline_df["date"]], timeline_df["scans"], color="#E8A838"),
        use_container_width=True, config={"displayModeBar": False}
    )

with col2:
    st.markdown('<div class="caption-label" style="margin-bottom:8px">TOKEN CONSUMPTION BY DATE</div>', unsafe_allow_html=True)
    tokens_df = df.groupby("date")["total_tokens"].sum().reset_index(name="tokens")
    st.plotly_chart(
        _noir_bar([str(d) for d in tokens_df["date"]], tokens_df["tokens"], color="#38C8E8"),
        use_container_width=True, config={"displayModeBar": False}
    )

st.markdown(section_divider(), unsafe_allow_html=True)

col3, col4 = st.columns(2)

with col3:
    st.markdown('<div class="caption-label" style="margin-bottom:8px">RISK PROFILE FREQUENCY</div>', unsafe_allow_html=True)
    risk_order = ["low", "medium", "high", "critical"]
    risk_df = df.groupby("highest_risk").size().reset_index(name="count")
    risk_df["highest_risk"] = pd.Categorical(risk_df["highest_risk"], categories=risk_order, ordered=True)
    risk_df = risk_df.sort_values("highest_risk")
    risk_colors_map = {"low": "#4FD180", "medium": "#E8C838", "high": "#FF8C42", "critical": "#FF4545"}
    bar_colors = [risk_colors_map.get(str(r), "#E8A838") for r in risk_df["highest_risk"]]
    fig3 = go.Figure(go.Bar(
        x=risk_df["highest_risk"].astype(str),
        y=risk_df["count"],
        marker_color=bar_colors,
        marker_line_color="rgba(0,0,0,0)",
    ))
    fig3.update_layout(
        paper_bgcolor="#141414", plot_bgcolor="#141414",
        font=dict(family="'Space Mono', monospace", color="#7A7A7A", size=11),
        margin=dict(l=0, r=0, t=8, b=0), height=220, showlegend=False,
        xaxis=dict(showgrid=False, zeroline=False, tickfont=dict(color="#7A7A7A", size=10), linecolor="#2A2A2A"),
        yaxis=dict(showgrid=True, gridcolor="#2A2A2A", zeroline=False, tickfont=dict(color="#7A7A7A", size=10), linecolor="#2A2A2A"),
    )
    st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})

with col4:
    st.markdown('<div class="caption-label" style="margin-bottom:8px">AI PROVIDER DISTRIBUTION</div>', unsafe_allow_html=True)
    provider_col = "ai_provider" if "ai_provider" in df.columns else "provider"
    if provider_col in df.columns:
        provider_df = df.groupby(provider_col).size().reset_index(name="count")
        st.plotly_chart(
            _noir_bar(provider_df[provider_col].astype(str), provider_df["count"], color="#C8F135"),
            use_container_width=True, config={"displayModeBar": False}
        )
    else:
        st.markdown("<div style='color:var(--text-muted); padding-top:20px'>No provider telemetry available.</div>", unsafe_allow_html=True)

st.markdown(section_divider(), unsafe_allow_html=True)

# ── RAW TELEMETRY LOGS ────────────────────────────────────────────────────────
st.markdown('<div class="caption-label" style="margin-bottom:12px">RAW PIPELINE TELEMETRY</div>', unsafe_allow_html=True)

display_df = df.copy()
display_cols = ["upload_id", "pdf_name", "scanned_at", "total_pages", "total_flags", "highest_risk", "total_tokens", "execution_time_sec", "ai_provider"]
available_cols = [c for c in display_cols if c in display_df.columns]
display_df = display_df[available_cols]

# Format scanned_at to string
if "scanned_at" in display_df.columns:
    display_df["scanned_at"] = display_df["scanned_at"].dt.strftime("%Y-%m-%d %H:%M:%S")

# Rename columns for presentation
renames = {
    "upload_id": "UPLOAD ID",
    "pdf_name": "FILE NAME",
    "scanned_at": "TIMESTAMP",
    "total_pages": "PAGES",
    "total_flags": "FLAGS",
    "highest_risk": "RISK LEVEL",
    "total_tokens": "TOKENS",
    "execution_time_sec": "DURATION (S)",
    "ai_provider": "PROVIDER"
}
display_df = display_df.rename(columns={k: v for k, v in renames.items() if k in display_df.columns})

st.dataframe(display_df, use_container_width=True, hide_index=True)
