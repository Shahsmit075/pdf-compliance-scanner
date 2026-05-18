# app/pages/01_upload.py
"""
Upload & Scan page — handles PDF upload and runs the full compliance pipeline.
"""
import streamlit as st
import tempfile
import uuid
import os
import time
from pathlib import Path

from pipeline.graph import run_pipeline
from config.rules import load_rules
from storage.database import save_result
from app.utils.redaction import build_redaction_table, mask_value

st.set_page_config(page_title="Upload & Scan", page_icon="📤", layout="wide")

st.title("📤 Upload PDF for Compliance Scan")
st.markdown("Upload any PDF document to automatically scan for compliance violations.")

uploaded_file = st.file_uploader(
    "Choose a PDF file",
    type=["pdf"],
    help="Maximum 50MB. Scans for PII, confidential data, encoding issues, and abusive content."
)

if uploaded_file is None:
    st.info("👆 Upload a PDF file to begin scanning")
    st.markdown("""
    **What gets checked:**
    | Check | Examples |
    |-------|---------|
    | PII Detection | Emails, phone numbers, Aadhaar, SSN, credit cards, passport, bank account |
    | Confidentiality | API keys, passwords, AWS/GitHub credentials, salary data, trade secrets |
    | Encoding | Non-ASCII content, multilingual text, OCR corruption, non-UTF-8 |
    | Abuse Detection | Threats, hate speech, harassment, violence incitement, illegal content |
    """)
    st.stop()

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("📄 File Name", uploaded_file.name[:30] + ("…" if len(uploaded_file.name) > 30 else ""))
with col2:
    st.metric("📦 File Size", f"{uploaded_file.size / 1024:.1f} KB")
with col3:
    st.metric("📂 File Type", "PDF Document")

st.markdown("---")

col_btn, col_info = st.columns([1, 3])
with col_btn:
    scan_btn = st.button("🔍 Run Compliance Scan", type="primary", use_container_width=True)
with col_info:
    st.caption("Detection uses regex + AI. Processing takes ~2–5 seconds per page.")

if scan_btn:
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(uploaded_file.read())
        tmp_path = tmp.name

    upload_id = str(uuid.uuid4())[:8]
    rules = load_rules()

    progress_bar = st.progress(0, text="Starting compliance scan…")
    status_text  = st.empty()
    start_time   = time.time()

    try:
        progress_bar.progress(10, text="📄 Extracting text from PDF…")
        status_text.info("Reading document structure…")
        time.sleep(0.3)

        progress_bar.progress(20, text="🤖 Running AI compliance checks…")
        status_text.info("Regex + AI nodes analysing PII, credentials, encoding, abuse…")

        result = run_pipeline(
            pdf_path=tmp_path,
            pdf_name=uploaded_file.name,
            upload_id=upload_id,
            compliance_rules=rules,
        )

        progress_bar.progress(90, text="💾 Saving results…")
        save_result(upload_id, uploaded_file.name, result)

        progress_bar.progress(100, text="✅ Scan complete!")
        elapsed = time.time() - start_time
        status_text.success(f"✅ Scan completed in {elapsed:.1f}s — Report ID: `{upload_id}`")

        st.session_state["latest_result"]    = result
        st.session_state["latest_upload_id"] = upload_id

    except Exception as e:
        st.error(f"❌ Scan failed: {str(e)}")
        st.exception(e)
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass

# ── Display results ───────────────────────────────────────────────────────────
if "latest_result" in st.session_state:
    result  = st.session_state["latest_result"]
    summary = result.get("summary", {})

    st.markdown("---")
    st.subheader("📊 Scan Results")

    risk_emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}
    highest = summary.get("highest_risk", "low")

    # Summary metrics
    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        st.metric("📄 Pages Scanned", summary.get("total_pages", 0))
    with m2:
        st.metric("🚩 Total Flags", summary.get("total_flags", 0))
    with m3:
        st.metric(f"{risk_emoji.get(highest, '')} Highest Risk", highest.upper())
    with m4:
        st.metric("🔴 PII Issues", summary.get("total_issues", {}).get("pii", 0))
    with m5:
        st.metric("🔐 Confidential", summary.get("total_issues", {}).get("confidential", 0))

    # Issue type breakdown
    st.markdown("#### Issue Breakdown by Type")
    issues = summary.get("total_issues", {})
    col_a, col_b, col_c, col_d = st.columns(4)
    with col_a:
        st.error(f"🔴 PII: **{issues.get('pii', 0)}** flags")
    with col_b:
        st.warning(f"🔐 Confidential: **{issues.get('confidential', 0)}** flags")
    with col_c:
        st.info(f"🔤 Encoding: **{issues.get('encoding', 0)}** flags")
    with col_d:
        st.error(f"⚠️ Abuse: **{issues.get('abuse', 0)}** flags")

    # Page heatmap
    st.markdown("#### Page-by-Page Risk Summary")
    page_data = []
    for pr in result.get("page_results", []):
        page_data.append({
            "Page":       pr["page_num"],
            "PII":        len(pr.get("pii_flags", [])),
            "Confidential": len(pr.get("confidential_flags", [])),
            "Encoding":   len(pr.get("encoding_flags", [])),
            "Abuse":      len(pr.get("abuse_flags", [])),
            "Total Flags": pr.get("total_flags", 0),
            "Risk":       pr.get("overall_risk", "low").upper(),
        })
    if page_data:
        st.dataframe(page_data, use_container_width=True)

    # ── Redaction Table ───────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("🔒 Redaction View — Masked Entity Table")
    st.caption(
        "Shows each detected entity with its masked/anonymised value. "
        "Use this to verify what would be redacted in a compliant export."
    )

    redaction_records = build_redaction_table(result.get("page_results", []))
    if redaction_records:
        # Filter controls
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            type_filter = st.multiselect(
                "Filter by Type",
                options=["PII", "CONFIDENTIAL", "ENCODING", "ABUSE"],
                default=["PII", "CONFIDENTIAL", "ENCODING", "ABUSE"],
            )
        with col_f2:
            sev_filter = st.multiselect(
                "Filter by Severity",
                options=["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"],
                default=["CRITICAL", "HIGH", "MEDIUM"],
            )

        filtered = [
            r for r in redaction_records
            if r["Type"] in type_filter and r["Severity"] in sev_filter
        ]

        if filtered:
            st.dataframe(
                filtered,
                use_container_width=True,
                column_config={
                    "Page":          st.column_config.NumberColumn("Page", width="small"),
                    "Type":          st.column_config.TextColumn("Type", width="small"),
                    "Category":      st.column_config.TextColumn("Category"),
                    "Matched Value": st.column_config.TextColumn("Matched Value"),
                    "Masked Value":  st.column_config.TextColumn("🔒 Masked"),
                    "Confidence":    st.column_config.TextColumn("Conf.", width="small"),
                    "Severity":      st.column_config.TextColumn("Severity", width="small"),
                    "Method":        st.column_config.TextColumn("Method", width="small"),
                    "Context":       st.column_config.TextColumn("Context Snippet"),
                }
            )
            st.caption(f"Showing {len(filtered)} of {len(redaction_records)} total findings")
        else:
            st.info("No findings match the current filters.")
    else:
        st.success("✅ No compliance violations found — document is clean.")

    # ── Download Report ───────────────────────────────────────────────────
    report_path = result.get("report_path")
    if report_path and Path(report_path).exists():
        st.markdown("---")
        with open(report_path, "rb") as f:
            st.download_button(
                label="📥 Download Full Compliance Report (PDF)",
                data=f.read(),
                file_name=f"compliance_report_{st.session_state.get('latest_upload_id', 'scan')}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )

    # ── Errors / warnings ─────────────────────────────────────────────────
    if result.get("errors"):
        with st.expander("⚠️ Scan Warnings"):
            for err in result["errors"]:
                st.warning(err)
