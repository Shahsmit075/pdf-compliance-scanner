# app/pages/03_reports.py
"""
Reports page — browse and download past compliance scan reports.
Noir Amber UI redesign.
"""
import sys
import os
# Inject project root path to allow absolute imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import streamlit as st
import textwrap
from pathlib import Path
from storage.database import get_all_scans, get_result, delete_scan
from app.styles.theme import GLOBAL_CSS
from app.components.ui import risk_badge, empty_state

st.set_page_config(page_title="Scan Archive", page_icon="⚠", layout="wide", initial_sidebar_state="expanded")
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

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

# ── GLOBAL ANALYTICS DASHBOARD ─────────────────────────────────────────────────
import pandas as pd
df = pd.DataFrame(scans)
if not df.empty and "scanned_at" in df.columns:
    df["scanned_at"] = pd.to_datetime(df["scanned_at"])
    df["date"] = df["scanned_at"].dt.date
    
    col_chart1, col_chart2 = st.columns(2)
    with col_chart1:
        st.markdown('<div class="caption-label" style="margin-bottom:8px">SCANS OVER TIME</div>', unsafe_allow_html=True)
        timeline_df = df.groupby("date").size().reset_index(name="scans")
        timeline_df.set_index("date", inplace=True)
        st.bar_chart(timeline_df, use_container_width=True, height=200, color="#E8A838")
        
    with col_chart2:
        st.markdown('<div class="caption-label" style="margin-bottom:8px">RISK DISTRIBUTION</div>', unsafe_allow_html=True)
        risk_df = df.groupby("highest_risk").size().reset_index(name="count")
        risk_df.set_index("highest_risk", inplace=True)
        st.bar_chart(risk_df, use_container_width=True, height=200, color="#FF5F57")

# ── TOTAL SCANS ────────────────────────────────────────────────────────────────
st.markdown(textwrap.dedent(f"""
<div style="display:inline-flex;align-items:center;gap:16px;background:var(--surface);border:1px solid var(--border);border-radius:3px;padding:12px 20px;margin-bottom:20px;margin-top:20px">
  <div class="caption-label">TOTAL SCANS</div>
  <div style="font-family:'JetBrains Mono',monospace;font-size:33px;font-weight:700;color:var(--amber)">{len(scans)}</div>
</div>
"""), unsafe_allow_html=True)

# ── SCAN CARDS ─────────────────────────────────────────────────────────────────
risk_emoji_map = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}
risk_color_map = {
    "critical": "var(--red)",
    "high": "var(--high)",
    "medium": "var(--medium)",
    "low": "var(--low)",
}

for scan in scans:
    risk = scan.get("highest_risk", "low")
    r_emoji = risk_emoji_map.get(risk, "⚪")
    r_color = risk_color_map.get(risk, "var(--text-muted)")
    scan_date = scan.get("scanned_at", "")[:16]
    scan_id = scan.get("upload_id", "")

    # Date / ID label above expander
    st.markdown(textwrap.dedent(f"""
    <div style="font-family:'Space Mono',monospace;font-size:12px;color:var(--text-muted);letter-spacing:0.12em;text-transform:uppercase;margin-bottom:2px">
      {scan_date} · ID: {scan_id}
    </div>
    """), unsafe_allow_html=True)

    pdf_name_short = scan["pdf_name"][:40]
    total_flags = scan.get("total_flags", 0)

    with st.expander(
        f"{r_emoji}  {pdf_name_short}  —  {total_flags} flags  ·  {risk.upper()}"
    ):
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
                    label="↓  DOWNLOAD COMPLIANCE REPORT",
                    data=f.read(),
                    file_name=f"compliance_{scan_id}.pdf",
                    mime="application/pdf",
                    key=f"dl_{scan_id}",
                )
        else:
            st.markdown(textwrap.dedent("""
            <div style="font-family:'Space Mono',monospace;font-size:14px;color:var(--medium);letter-spacing:0.06em;padding:8px 0">
              ⚠ Report PDF not found (may have been deleted or moved)
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

        if st.button("✕  DELETE SCAN", key=f"del_{scan_id}"):
            delete_scan(scan_id)
            st.toast("Scan deleted.", icon="🗑️")
            st.rerun()

    # Spacer between scan cards
    st.markdown('<div style="height:8px"></div>', unsafe_allow_html=True)
