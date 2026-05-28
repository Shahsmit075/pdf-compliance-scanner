# app/pages/01_upload.py
"""
Upload & Scan page — handles PDF upload and runs the full compliance pipeline.
Noir Amber UI redesign.
"""
import streamlit as st
import textwrap
import tempfile
import uuid
import os
import time
from pathlib import Path

from pipeline.graph import run_pipeline
from config.rules import load_rules
from storage.database import save_result
from app.utils.redaction import build_redaction_table, mask_value
from app.styles.theme import GLOBAL_CSS
from app.components.ui import (
    risk_badge,
    section_header,
    metric_grid,
    flag_count_row,
    scan_result_header,
    loading_message,
    section_divider,
)
from app.components.sarcasm import get_stage_message, get_risk_quip, get_empty_state_quip

st.set_page_config(page_title="Upload & Scan", page_icon="⬡", layout="wide")
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

# ── PAGE HEADER ────────────────────────────────────────────────────────────────
st.markdown(textwrap.dedent("""
<div class="animate-fadein" style="padding:0 0 24px">
  <div class="caption-label">MODULE 01</div>
  <h1 style="font-family:'Space Mono',monospace; font-size:33px; font-weight:700; color:var(--text); margin:6px 0 4px; letter-spacing:-0.01em">
    UPLOAD <span style="color:var(--amber)">&</span> SCAN
  </h1>
  <p style="color:var(--text-muted); font-size:17px; margin:0">
    Drop your document. We'll find everything that shouldn't be there.
  </p>
</div>
"""), unsafe_allow_html=True)

# ── FILE UPLOADER ──────────────────────────────────────────────────────────────
st.markdown('<div class="caption-label animate-fadein" style="margin-bottom:8px">DOCUMENT INPUT</div>', unsafe_allow_html=True)

uploaded_file = st.file_uploader(
    "Choose a PDF file",
    type=["pdf"],
    help="Maximum 50MB. Scans for PII, confidential data, encoding issues, and abusive content.",
    label_visibility="collapsed",
)

# ── NO FILE UPLOADED — detection capabilities showcase ─────────────────────────
if uploaded_file is None:
    st.markdown(textwrap.dedent("""
    <div class="animate-fadein-2" style="background:var(--surface); border:1px solid var(--border); border-radius:4px; padding:32px; margin-top:16px">
      <div class="caption-label" style="margin-bottom:20px">DETECTION CAPABILITIES</div>
      <div style="display:grid; grid-template-columns:1fr 1fr; gap:1px; background:var(--border)">
        <div style="background:var(--surface-2);padding:16px">
          <div style="font-family:'Space Mono',monospace;font-size:13px;color:var(--amber);letter-spacing:0.1em;margin-bottom:8px">◈ PII DETECTION</div>
          <div style="font-family:'JetBrains Mono',monospace;font-size:14px;color:var(--text-muted);line-height:2">
            john.doe@email.com → j***@e***.com<br>
            +91-9876543210 → ****3210<br>
            1234-5678-9012 → XXXX XXXX 9012<br>
            ABLDE1234F → A****1234F
          </div>
        </div>
        <div style="background:var(--surface-2);padding:16px">
          <div style="font-family:'Space Mono',monospace;font-size:13px;color:var(--red);letter-spacing:0.1em;margin-bottom:8px">⬡ CONFIDENTIALITY</div>
          <div style="font-family:'JetBrains Mono',monospace;font-size:14px;color:var(--text-muted);line-height:2">
            sk-abc123... → sk-abc…3 [CRITICAL]<br>
            AKIA1234... → AKIA1…PLE [CRITICAL]<br>
            password=hunter2 → [CRITICAL]<br>
            salary: $950,000 → [HIGH]
          </div>
        </div>
        <div style="background:var(--surface-2);padding:16px">
          <div style="font-family:'Space Mono',monospace;font-size:13px;color:var(--ice);letter-spacing:0.1em;margin-bottom:8px">⟁ ENCODING</div>
          <div style="font-family:'JetBrains Mono',monospace;font-size:14px;color:var(--text-muted);line-height:2">
            UTF-8 validation<br>
            OCR corruption detection<br>
            Multilingual script ID<br>
            Language compliance check
          </div>
        </div>
        <div style="background:var(--surface-2);padding:16px">
          <div style="font-family:'Space Mono',monospace;font-size:13px;color:var(--medium);letter-spacing:0.1em;margin-bottom:8px">⚠ ABUSE DETECTION</div>
          <div style="font-family:'JetBrains Mono',monospace;font-size:14px;color:var(--text-muted);line-height:2">
            Threat language → [REDACTED]<br>
            Hate speech → [REDACTED]<br>
            Harassment patterns → [REDACTED]<br>
            Illegal content → [REDACTED]
          </div>
        </div>
      </div>
      <div style="margin-top:20px; text-align:center; font-family:'Space Mono',monospace; font-size:13px; color:var(--text-muted); letter-spacing:0.1em">
        ↑ UPLOAD A PDF TO BEGIN — ALL DETECTIONS SHOWN ABOVE WILL BE APPLIED AUTOMATICALLY
      </div>
    </div>
    """), unsafe_allow_html=True)
    st.stop()

# ── FILE METADATA ──────────────────────────────────────────────────────────────
file_size_kb = uploaded_file.size / 1024
if file_size_kb >= 1024:
    file_size_str = f"{file_size_kb / 1024:.1f} MB"
else:
    file_size_str = f"{file_size_kb:.1f} KB"

fname_display = uploaded_file.name if len(uploaded_file.name) <= 40 else uploaded_file.name[:37] + "…"

st.markdown(textwrap.dedent(f"""
<div class="animate-fadein" style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:1px;background:var(--border);margin:16px 0;border:1px solid var(--border)">
  <div style="background:var(--surface);padding:14px 18px">
    <div class="caption-label" style="margin-bottom:4px">FILENAME</div>
    <div style="font-family:'JetBrains Mono',monospace;font-size:16px;color:var(--text);overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{fname_display}</div>
  </div>
  <div style="background:var(--surface);padding:14px 18px">
    <div class="caption-label" style="margin-bottom:4px">FILE SIZE</div>
    <div style="font-family:'JetBrains Mono',monospace;font-size:23px;color:var(--amber);font-weight:700">{file_size_str}</div>
  </div>
  <div style="background:var(--surface);padding:14px 18px">
    <div class="caption-label" style="margin-bottom:4px">FORMAT</div>
    <div style="font-family:'JetBrains Mono',monospace;font-size:16px;color:var(--low)">● PDF DOCUMENT</div>
  </div>
</div>
"""), unsafe_allow_html=True)

# ── SCAN BUTTON ────────────────────────────────────────────────────────────────
st.markdown('<div class="caption-label" style="margin-bottom:8px">INITIATE SCAN</div>', unsafe_allow_html=True)

col_btn, col_info = st.columns([1, 3])
with col_btn:
    scan_btn = st.button("▶  RUN COMPLIANCE SCAN", type="primary", use_container_width=True)
with col_info:
    st.markdown(textwrap.dedent("""
    <div style="font-family:'Space Mono',monospace; font-size:13px; color:var(--text-muted); padding-top:8px; letter-spacing:0.05em">
      DETECTION: regex + ai · ESTIMATED: 2–5s/page
    </div>
    """), unsafe_allow_html=True)

# ── RUN SCAN ───────────────────────────────────────────────────────────────────
if scan_btn:
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(uploaded_file.read())
        tmp_path = tmp.name

    upload_id = str(uuid.uuid4())[:8]
    rules = load_rules()

    progress_bar = st.progress(0, text="Initializing compliance scan…")
    status_text = st.empty()
    start_time = time.time()

    try:
        # Stage: Extracting
        progress_bar.progress(10, text="Extracting text from PDF…")
        status_text.markdown(loading_message(get_stage_message("extracting")), unsafe_allow_html=True)
        time.sleep(0.3)

        # Stage: Running AI checks
        progress_bar.progress(20, text="Running AI compliance checks…")
        status_text.markdown(loading_message(get_stage_message("pii_scanning")), unsafe_allow_html=True)

        result = run_pipeline(
            pdf_path=tmp_path,
            pdf_name=uploaded_file.name,
            upload_id=upload_id,
            compliance_rules=rules,
        )

        # Stage: Saving
        progress_bar.progress(90, text="Saving results…")
        status_text.markdown(loading_message(get_stage_message("building_report")), unsafe_allow_html=True)
        save_result(upload_id, uploaded_file.name, result)

        # Complete
        progress_bar.progress(100, text="Scan complete")
        elapsed = time.time() - start_time
        status_text.markdown(loading_message(get_stage_message("complete")), unsafe_allow_html=True)

        st.session_state["latest_result"] = result
        st.session_state["latest_upload_id"] = upload_id
        st.session_state["latest_elapsed"] = elapsed

    except Exception as e:
        st.error(f"Scan failed: {str(e)}")
        st.exception(e)
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass

# ── DISPLAY RESULTS ────────────────────────────────────────────────────────────
if "latest_result" in st.session_state:
    result = st.session_state["latest_result"]
    summary = result.get("summary", {})
    highest = summary.get("highest_risk", "low")
    issues = summary.get("total_issues", {})
    elapsed = st.session_state.get("latest_elapsed", 0)
    upload_id = st.session_state.get("latest_upload_id", "")

    # ── SCAN RESULT HEADER ─────────────────────────────────────────────────
    st.markdown(section_divider(), unsafe_allow_html=True)
    st.markdown(
        scan_result_header(uploaded_file.name, upload_id, elapsed, highest),
        unsafe_allow_html=True,
    )

    # Risk quip
    st.markdown(textwrap.dedent(f"""
    <div style="font-family:'DM Sans',sans-serif;font-size:16px;color:var(--text-muted);font-style:italic;text-align:center;padding:8px 0 16px">
      "{get_risk_quip(highest)}"
    </div>
    """), unsafe_allow_html=True)

    # ── SUMMARY METRICS ────────────────────────────────────────────────────
    risk_colors = {
        "critical": "var(--red)",
        "high": "var(--high)",
        "medium": "var(--medium)",
        "low": "var(--low)",
    }
    st.markdown(
        metric_grid([
            {"label": "PAGES SCANNED", "value": summary.get("total_pages", 0), "color": "var(--ice)"},
            {"label": "TOTAL FLAGS", "value": summary.get("total_flags", 0), "color": "var(--amber)"},
            {"label": "HIGHEST RISK", "value": highest.upper(), "color": risk_colors.get(highest, "var(--text)")},
            {"label": "PII", "value": issues.get("pii", 0), "color": "var(--red)"},
            {"label": "CONFIDENTIAL", "value": issues.get("confidential", 0), "color": "var(--high)"},
        ]),
        unsafe_allow_html=True,
    )

    # ── ISSUE BREAKDOWN ────────────────────────────────────────────────────
    st.markdown(
        flag_count_row(
            pii=issues.get("pii", 0),
            confidential=issues.get("confidential", 0),
            encoding=issues.get("encoding", 0),
            abuse=issues.get("abuse", 0),
        ),
        unsafe_allow_html=True,
    )

    # ── PAGE HEATMAP ───────────────────────────────────────────────────────
    st.markdown('<div class="caption-label" style="margin-bottom:8px">PAGE-BY-PAGE RISK MATRIX</div>', unsafe_allow_html=True)
    page_data = []
    for pr in result.get("page_results", []):
        page_data.append({
            "Page": pr["page_num"],
            "PII": len(pr.get("pii_flags", [])),
            "Confidential": len(pr.get("confidential_flags", [])),
            "Encoding": len(pr.get("encoding_flags", [])),
            "Abuse": len(pr.get("abuse_flags", [])),
            "Total Flags": pr.get("total_flags", 0),
            "Risk": pr.get("overall_risk", "low").upper(),
        })
    if page_data:
        st.dataframe(page_data, use_container_width=True)

    # ── REDACTION TABLE ────────────────────────────────────────────────────
    st.markdown(textwrap.dedent("""
    <div style="padding:16px 0 12px;border-top:1px solid var(--border);margin-top:8px">
      <div class="caption-label">REDACTION PREVIEW</div>
      <h3 style="font-family:'Space Mono',monospace;font-size:19px;color:var(--text);margin:6px 0 4px">MASKED ENTITY TABLE</h3>
      <p style="color:var(--text-muted);font-size:15px;margin:0;font-family:'JetBrains Mono',monospace">
        Verified redaction output — what a compliant export would look like.
      </p>
    </div>
    """), unsafe_allow_html=True)

    redaction_records = build_redaction_table(result.get("page_results", []))
    if redaction_records:
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
                    "Page": st.column_config.NumberColumn("Page", width="small"),
                    "Type": st.column_config.TextColumn("Type", width="small"),
                    "Category": st.column_config.TextColumn("Category"),
                    "Matched Value": st.column_config.TextColumn("Matched Value"),
                    "Masked Value": st.column_config.TextColumn("🔒 Masked"),
                    "Confidence": st.column_config.TextColumn("Conf.", width="small"),
                    "Severity": st.column_config.TextColumn("Severity", width="small"),
                    "Method": st.column_config.TextColumn("Method", width="small"),
                    "Context": st.column_config.TextColumn("Context Snippet"),
                },
            )
            st.markdown(textwrap.dedent(f"""
            <div style="font-family:'JetBrains Mono',monospace;font-size:14px;color:var(--text-muted);margin-top:4px">
              Showing {len(filtered)} of {len(redaction_records)} total findings
            </div>
            """), unsafe_allow_html=True)
        else:
            st.markdown(textwrap.dedent("""
            <div style="text-align:center;padding:24px;border:1px dashed var(--border);border-radius:3px;margin:8px 0">
              <div style="font-family:'Space Mono',monospace;font-size:14px;color:var(--text-muted);letter-spacing:0.1em">
                NO FINDINGS MATCH THE CURRENT FILTERS
              </div>
            </div>
            """), unsafe_allow_html=True)
    else:
        quip = get_empty_state_quip()
        st.markdown(textwrap.dedent(f"""
        <div style="text-align:center;padding:48px 24px;border:1px solid var(--low);background:rgba(79,209,128,0.04);border-radius:4px">
          <div style="font-family:'Space Mono',monospace;font-size:37px;margin-bottom:16px">✓</div>
          <div style="font-family:'Space Mono',monospace;font-size:17px;color:var(--low);letter-spacing:0.1em;margin-bottom:8px">DOCUMENT IS CLEAN</div>
          <div style="font-family:'DM Sans',sans-serif;font-size:16px;color:var(--text-muted)">
            {quip}
          </div>
        </div>
        """), unsafe_allow_html=True)

    # ── DOWNLOAD REPORT ────────────────────────────────────────────────────
    report_path = result.get("report_path")
    if report_path and Path(report_path).exists():
        st.markdown(textwrap.dedent("""
        <div style="margin-top:24px;padding:20px;background:var(--surface);border:1px solid var(--amber);border-radius:4px;display:flex;align-items:center;justify-content:space-between">
          <div>
            <div class="caption-label">COMPLIANCE REPORT</div>
            <div style="font-family:'Space Mono',monospace;font-size:16px;color:var(--text);margin-top:4px">Full PDF report with findings, heatmap, and masked entity table</div>
          </div>
        </div>
        """), unsafe_allow_html=True)
        with open(report_path, "rb") as f:
            st.download_button(
                label="↓  DOWNLOAD FULL COMPLIANCE REPORT (PDF)",
                data=f.read(),
                file_name=f"compliance_report_{upload_id}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )

    # ── SCAN WARNINGS ──────────────────────────────────────────────────────
    if result.get("errors"):
        with st.expander("SCAN WARNINGS"):
            for err in result["errors"]:
                st.warning(err)
