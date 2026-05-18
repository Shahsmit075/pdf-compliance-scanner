# app/components/report_card.py
"""
Reusable report card component for displaying scan results.
"""
import streamlit as st


RISK_COLORS = {
    "critical": "🔴",
    "high": "🟠",
    "medium": "🟡",
    "low": "🟢",
}


def render_report_card(scan: dict) -> None:
    """Render a scan summary card."""
    risk = scan.get("highest_risk", "low")
    emoji = RISK_COLORS.get(risk, "⚪")

    with st.container():
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Pages", scan.get("total_pages", 0))
        with col2:
            st.metric("Total Flags", scan.get("total_flags", 0))
        with col3:
            st.metric("Highest Risk", f"{emoji} {risk.upper()}")
        with col4:
            st.metric("Scan ID", scan.get("upload_id", "N/A"))
