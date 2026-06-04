# app/pages/03_reports.py
"""
Reports page — browse and download past compliance scan reports.
Noir Amber UI redesign.
"""
import sys
import os
# Inject project root path to allow absolute imports (robust for Streamlit Cloud)
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)
_cwd = os.getcwd()
if _cwd not in sys.path:
    sys.path.insert(0, _cwd)

import streamlit as st
import textwrap
from pathlib import Path
from storage.database import get_all_scans, get_result, delete_scan
from app.styles.theme import GLOBAL_CSS
from app.components.ui import risk_badge, empty_state, render_sidebar_opener

st.set_page_config(page_title="Scan Archive", page_icon="⚠", layout="wide", initial_sidebar_state="expanded")
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
from app.components.ui import render_common_sidebar
render_common_sidebar()
render_sidebar_opener()


# ── PAGE HEADER ────────────────────────────────────────────────────────────────
st.markdown(textwrap.dedent("""
<div class="animate-fadein" style="padding:0 0 24px">
  <div class="caption-label">MODULE 03</div>
  <h1 style="font-family:'Space Mono',monospace;font-size:33px;font-weight:700;color:var(--text);margin:6px 0 4px">
    SCAN <span style="color:var(--amber)">ARCHIVE</span>
  </h1>
  <p style="color:var(--text-muted);font-size:17px;margin:0">
    Browse, review, and download past compliance scan reports.
  </p>
</div>
"""), unsafe_allow_html=True)

scans = get_all_scans()

# ── EMPTY STATE ────────────────────────────────────────────────────────────────
if not scans:
    st.markdown(textwrap.dedent("""
    <div style="text-align:center;padding:64px 24px;border:1px dashed var(--border);border-radius:4px;margin-top:24px">
      <div style="font-family:'Space Mono',monospace;font-size:53px;color:var(--border-bright);margin-bottom:16px">□</div>
      <div style="font-family:'Space Mono',monospace;font-size:16px;color:var(--text-muted);letter-spacing:0.1em;margin-bottom:8px">NO SCANS ON RECORD</div>
      <div style="font-family:'DM Sans',sans-serif;font-size:16px;color:var(--text-muted)">
        Your archive is empty. Upload a document to run your first scan.<br>
        <span style="font-style:italic">The archive doesn't judge. Neither do we. Much.</span>
      </div>
    </div>
    """), unsafe_allow_html=True)
    st.stop()

# ── GLOBAL ANALYTICS DASHBOARD ───────────────────────────────────────────
import pandas as pd
import plotly.graph_objects as go

def _noir_bar(x_vals, y_vals, colors, height=200):
    """Plotly bar chart styled for Noir Amber dark theme."""
    fig = go.Figure(go.Bar(
        x=x_vals, y=y_vals,
        marker_color=colors,
        marker_line_color="rgba(0,0,0,0)",
    ))
    fig.update_layout(
        paper_bgcolor="#141414", plot_bgcolor="#141414",
        font=dict(family="'Space Mono', monospace", color="#7A7A7A", size=10),
        margin=dict(l=0, r=0, t=8, b=0), height=height, showlegend=False,
        xaxis=dict(showgrid=False, zeroline=False, tickfont=dict(color="#7A7A7A", size=10), linecolor="#2A2A2A"),
        yaxis=dict(showgrid=True, gridcolor="#2A2A2A", zeroline=False, tickfont=dict(color="#7A7A7A", size=10), linecolor="#2A2A2A"),
    )
    return fig

df = pd.DataFrame(scans)
if not df.empty and "scanned_at" in df.columns:
    df["scanned_at"] = pd.to_datetime(df["scanned_at"])
    df["date"] = df["scanned_at"].dt.date
    
    col_chart1, col_chart2 = st.columns(2)
    with col_chart1:
        st.markdown('<div class="caption-label" style="margin-bottom:8px">SCANS OVER TIME</div>', unsafe_allow_html=True)
        timeline_df = df.groupby("date").size().reset_index(name="scans")
        st.plotly_chart(
            _noir_bar([str(d) for d in timeline_df["date"]], timeline_df["scans"], colors="#E8A838"),
            use_container_width=True, config={"displayModeBar": False}
        )
        
    with col_chart2:
        st.markdown('<div class="caption-label" style="margin-bottom:8px">RISK DISTRIBUTION</div>', unsafe_allow_html=True)
        risk_df = df.groupby("highest_risk").size().reset_index(name="count")
        risk_colors_map = {"low": "#4FD180", "medium": "#E8C838", "high": "#FF8C42", "critical": "#FF4545"}
        bar_colors = [risk_colors_map.get(str(r), "#E8A838") for r in risk_df["highest_risk"]]
        st.plotly_chart(
            _noir_bar(risk_df["highest_risk"].astype(str), risk_df["count"], colors=bar_colors),
            use_container_width=True, config={"displayModeBar": False}
        )

# ── TOTAL SCANS ────────────────────────────────────────────────────────────────
st.markdown(textwrap.dedent(f"""
<div style="display:inline-flex;align-items:center;gap:16px;background:var(--surface);border:1px solid var(--border);border-radius:3px;padding:12px 20px;margin-bottom:20px;margin-top:20px">
  <div class="caption-label">TOTAL SCANS</div>
  <div style="font-family:'JetBrains Mono',monospace;font-size:33px;font-weight:700;color:var(--amber)">{len(scans)}</div>
</div>
"""), unsafe_allow_html=True)

# ── SCAN CARDS ─────────────────────────────────────────────────────────────────
risk_color_map = {
    "critical": "var(--red)",
    "high": "var(--high)",
    "medium": "var(--medium)",
    "low": "var(--low)",
}

for scan in scans:
    risk = scan.get("highest_risk", "low")
    r_color = risk_color_map.get(risk, "var(--text-muted)")
    scan_date = scan.get("scanned_at", "")[:16]
    scan_id = scan.get("upload_id", "")
    pdf_name_short = scan["pdf_name"][:40]
    total_flags = scan.get("total_flags", 0)
    state_key = f"open_{scan_id}"

    # Date / ID label above card
    st.markdown(textwrap.dedent(f"""
    <div style="font-family:'Space Mono',monospace;font-size:12px;color:var(--text-muted);letter-spacing:0.12em;text-transform:uppercase;margin-bottom:2px">
      {scan_date} · ID: {scan_id}
    </div>
    """), unsafe_allow_html=True)

    # ── Custom toggle header (replaces st.expander — no arrow, no key leakage) ──
    is_open = st.session_state.get(state_key, False)
    indicator = "▲" if is_open else "▼"
    if st.button(
        f"[{risk.upper()}]  {pdf_name_short}  —  {total_flags} flags  {indicator}",
        key=f"toggle_{scan_id}",
        use_container_width=True,
    ):
        st.session_state[state_key] = not is_open
        st.rerun()

    # ── Card content shown when toggled open ────────────────────────────────────
    if st.session_state.get(state_key, False):
        with st.container():
            # Metrics grid
            st.markdown(textwrap.dedent(f"""
            <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:1px;background:var(--border);border:1px solid var(--border);margin-bottom:16px">
              <div style="background:var(--surface);padding:12px">
                <div class="caption-label" style="margin-bottom:4px">PAGES</div>
                <div style="font-family:'JetBrains Mono',monospace;font-size:23px;color:var(--ice)">{scan.get("total_pages", 0)}</div>
              </div>
              <div style="background:var(--surface);padding:12px">
                <div class="caption-label" style="margin-bottom:4px">FLAGS</div>
                <div style="font-family:'JetBrains Mono',monospace;font-size:23px;color:var(--amber)">{total_flags}</div>
              </div>
              <div style="background:var(--surface);padding:12px">
                <div class="caption-label" style="margin-bottom:4px">RISK LEVEL</div>
                <div style="font-family:'Space Mono',monospace;font-size:17px;color:{r_color};font-weight:700">{risk.upper()}</div>
              </div>
              <div style="background:var(--surface);padding:12px">
                <div class="caption-label" style="margin-bottom:4px">SCAN ID</div>
                <div style="font-family:'JetBrains Mono',monospace;font-size:15px;color:var(--text-muted)">{scan_id}</div>
              </div>
            </div>
            """), unsafe_allow_html=True)

            # Download report PDF
            report_path = scan.get("report_path")
            if report_path and Path(report_path).exists():
                with open(report_path, "rb") as f:
                    st.download_button(
                        label="DOWNLOAD COMPLIANCE REPORT",
                        data=f.read(),
                        file_name=f"compliance_{scan_id}.pdf",
                        mime="application/pdf",
                        key=f"dl_{scan_id}",
                    )
            else:
                st.markdown(textwrap.dedent("""
                <div style="font-family:'Space Mono',monospace;font-size:14px;color:var(--medium);letter-spacing:0.06em;padding:8px 0">
                  REPORT PDF NOT FOUND (may have been deleted or moved)
                </div>
                """), unsafe_allow_html=True)

            # Full result JSON toggle
            full = get_result(scan_id)
            if full and "data" in full:
                show_json = st.toggle("Show Raw JSON Summary", key=f"json_{scan_id}")
                if show_json:
                    st.json(full["data"].get("summary", {}))

            # Danger zone — delete
            st.markdown(textwrap.dedent("""
            <div style="height:1px;background:var(--border);margin:12px 0"></div>
            <div class="caption-label" style="margin-bottom:6px;color:var(--red)">DANGER ZONE</div>
            """), unsafe_allow_html=True)

            if st.button("DELETE SCAN", key=f"del_{scan_id}"):
                delete_scan(scan_id)
                st.toast("Scan deleted.")
                st.rerun()

    # Spacer between scan cards
    st.markdown('<div style="height:8px"></div>', unsafe_allow_html=True)

