# app/pages/03_reports.py
"""
Reports page — browse and download past compliance scan reports.
"""
import streamlit as st
from pathlib import Path
from storage.database import get_all_scans, get_result, delete_scan

st.set_page_config(page_title="View Reports", page_icon="📊", layout="wide")

st.title("📊 Compliance Scan Reports")
st.markdown("Browse and download your past compliance scan reports.")

scans = get_all_scans()

if not scans:
    st.info("No scans yet. Go to **📤 Upload & Scan** to run your first compliance check.")
    st.stop()

st.metric("Total Scans", len(scans))

for scan in scans:
    risk = scan.get("highest_risk", "low")
    risk_emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(risk, "⚪")

    with st.expander(
        f"{risk_emoji} {scan['pdf_name']} — {scan['scanned_at'][:16]} | "
        f"Flags: {scan['total_flags']} | Risk: {risk.upper()}"
    ):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Pages", scan.get("total_pages", 0))
        with col2:
            st.metric("Total Flags", scan.get("total_flags", 0))
        with col3:
            st.metric("Highest Risk", risk.upper())
        with col4:
            st.metric("Scan ID", scan["upload_id"])

        # Download report PDF
        report_path = scan.get("report_path")
        if report_path and Path(report_path).exists():
            with open(report_path, "rb") as f:
                st.download_button(
                    label=f"📥 Download Compliance Report",
                    data=f.read(),
                    file_name=f"compliance_{scan['upload_id']}.pdf",
                    mime="application/pdf",
                    key=f"dl_{scan['upload_id']}"
                )
        else:
            st.warning("Report PDF not found (may have been deleted or moved)")

        # Full result data — use toggle instead of nested expander
        full = get_result(scan["upload_id"])
        if full and "data" in full:
            show_json = st.toggle("🔍 Show Raw JSON Summary", key=f"json_{scan['upload_id']}")
            if show_json:
                st.json(full["data"].get("summary", {}))

        # Delete button
        if st.button(f"🗑️ Delete Scan", key=f"del_{scan['upload_id']}"):
            delete_scan(scan["upload_id"])
            st.success("Scan deleted.")
            st.rerun()
