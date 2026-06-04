# app/pages/05_ds_scan.py
"""
Module 05 — Data Source Scan
Trigger compliance scans on registered data sources. View live results.
"""
import streamlit as st
import textwrap
import json
import time
from datetime import datetime

from storage.database import DataSourceDB, init_ds_db
from connectors.factory import CONNECTOR_META
from app.styles.theme import GLOBAL_CSS

st.set_page_config(page_title="Data Source Scan", page_icon="⬡", layout="wide", initial_sidebar_state="expanded")
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
init_ds_db()

# ── PAGE HEADER ────────────────────────────────────────────────────────────────
st.markdown(textwrap.dedent("""
<div class="animate-fadein" style="padding:0 0 24px">
  <div class="caption-label">MODULE 05</div>
  <h1 style="font-family:'Space Mono',monospace;font-size:33px;font-weight:700;color:var(--text);margin:6px 0 4px">
    DATA SOURCE <span style="color:var(--amber)">SCAN</span>
  </h1>
  <p style="color:var(--text-muted);font-size:17px;margin:0">
    Run compliance scans on registered data sources — schema discovery + PII/confidential classification.
  </p>
</div>
"""), unsafe_allow_html=True)

sources = DataSourceDB.get_all_sources()

if not sources:
    st.markdown(textwrap.dedent("""
    <div style="text-align:center;padding:64px 24px;border:1px dashed var(--border);border-radius:4px">
      <div style="font-family:'Space Mono',monospace;font-size:16px;color:var(--text-muted);letter-spacing:0.1em">
        NO DATA SOURCES REGISTERED<br>
        <span style="font-size:14px;color:var(--border-bright)">Add a source in Module 04 first.</span>
      </div>
    </div>
    """), unsafe_allow_html=True)
    st.stop()

# ── SOURCE SELECTOR ────────────────────────────────────────────────────────────
source_options = {
    f"{CONNECTOR_META.get(s['source_type'], {}).get('icon', '🔌')} {s['name']} ({s['source_type']})": s
    for s in sources
}
selected_label = st.selectbox("Select Data Source", options=list(source_options.keys()),
                              label_visibility="collapsed")
selected_source = source_options[selected_label]
source_id = selected_source["source_id"]
source_name = selected_source["name"]

# ── SOURCE STATUS CARD ─────────────────────────────────────────────────────────
meta = CONNECTOR_META.get(selected_source["source_type"], {"icon": "🔌", "label": selected_source["source_type"]})
last_conn = (selected_source.get("last_connected_at") or "Never")[:16]
status_color = {"active": "var(--low)", "paused": "var(--medium)", "error": "var(--red)"}.get(
    selected_source.get("status", "active"), "var(--text-muted)"
)

snapshot = DataSourceDB.get_latest_snapshot(source_id)
recent_scans = DataSourceDB.get_scan_runs(source_id, limit=5)

col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
with col_stat1:
    st.markdown(textwrap.dedent(f"""
    <div style="background:var(--surface);border:1px solid var(--border);padding:16px;border-radius:3px">
      <div class="caption-label" style="margin-bottom:4px">SOURCE STATUS</div>
      <div style="font-family:'Space Mono',monospace;font-size:18px;font-weight:700;color:{status_color}">
        {selected_source.get('status', 'active').upper()}
      </div>
    </div>
    """), unsafe_allow_html=True)
with col_stat2:
    snap_tables = snapshot.get("table_count", 0) if snapshot else "—"
    st.markdown(textwrap.dedent(f"""
    <div style="background:var(--surface);border:1px solid var(--border);padding:16px;border-radius:3px">
      <div class="caption-label" style="margin-bottom:4px">TABLES IN SNAPSHOT</div>
      <div style="font-family:'JetBrains Mono',monospace;font-size:28px;font-weight:700;color:var(--amber)">{snap_tables}</div>
    </div>
    """), unsafe_allow_html=True)
with col_stat3:
    snap_cols = snapshot.get("column_count", 0) if snapshot else "—"
    st.markdown(textwrap.dedent(f"""
    <div style="background:var(--surface);border:1px solid var(--border);padding:16px;border-radius:3px">
      <div class="caption-label" style="margin-bottom:4px">COLUMNS IN SNAPSHOT</div>
      <div style="font-family:'JetBrains Mono',monospace;font-size:28px;font-weight:700;color:var(--ice)">{snap_cols}</div>
    </div>
    """), unsafe_allow_html=True)
with col_stat4:
    snap_hash = (snapshot.get("schema_hash") or "—")[:12] if snapshot else "—"
    snap_time = (snapshot.get("captured_at") or "Never")[:16] if snapshot else "Never"
    st.markdown(textwrap.dedent(f"""
    <div style="background:var(--surface);border:1px solid var(--border);padding:16px;border-radius:3px">
      <div class="caption-label" style="margin-bottom:4px">LAST SNAPSHOT</div>
      <div style="font-family:'JetBrains Mono',monospace;font-size:14px;color:var(--text-muted)">{snap_time}</div>
      <div style="font-family:'JetBrains Mono',monospace;font-size:13px;color:var(--border-bright);margin-top:2px">{snap_hash}</div>
    </div>
    """), unsafe_allow_html=True)

st.markdown('<div style="height:16px"></div>', unsafe_allow_html=True)

# ── SCAN TRIGGER ───────────────────────────────────────────────────────────────
col_btn, col_help = st.columns([1, 3])
with col_btn:
    run_scan = st.button("▶  RUN COMPLIANCE SCAN", type="primary", use_container_width=True, key="run_ds_scan")
with col_help:
    st.markdown(textwrap.dedent("""
    <div style="font-family:'Space Mono',monospace;font-size:13px;color:var(--text-muted);padding-top:8px;letter-spacing:0.05em">
      Metadata → Schema Diff → Column Classification → Risk Score
    </div>
    """), unsafe_allow_html=True)

# ── RUN SCAN ───────────────────────────────────────────────────────────────────
if run_scan:
    from agents.metadata_agent.graph import run_metadata_agent
    from agents.compliance_agent.graph import run_compliance_agent
    from intelligence.risk_scorer import build_trend_entry
    from rag.vector_store import index_scan_findings

    progress = st.progress(0, text="Starting metadata agent…")
    status_ph = st.empty()

    try:
        # Stage 1: Metadata agent
        progress.progress(15, text="Connecting to data source…")
        status_ph.markdown(textwrap.dedent("""
        <div style="font-family:'Space Mono',monospace;font-size:14px;color:var(--amber);padding:8px 0;letter-spacing:0.08em">
          ◈ METADATA AGENT — collecting schema…
        </div>
        """), unsafe_allow_html=True)

        meta_state = run_metadata_agent(source_id, triggered_by="manual")

        if meta_state.get("connection_status") != "connected":
            errors = meta_state.get("errors", ["Unknown connection error"])
            st.error(f"Connection failed: {'; '.join(errors)}")
            st.stop()

        progress.progress(45, text="Schema collected — running compliance agent…")
        status_ph.markdown(textwrap.dedent(f"""
        <div style="font-family:'Space Mono',monospace;font-size:14px;color:var(--amber);padding:8px 0;letter-spacing:0.08em">
          ⬡ COMPLIANCE AGENT — classifying {meta_state.get('current_metadata', {}).get('column_count', 0)} columns…
        </div>
        """), unsafe_allow_html=True)

        # Stage 2: Compliance agent
        comp_state = run_compliance_agent(
            source_id=source_id,
            metadata=meta_state.get("current_metadata", {}),
            scan_scope=meta_state.get("scan_scope", []),
        )

        progress.progress(80, text="Indexing findings…")
        status_ph.markdown(textwrap.dedent("""
        <div style="font-family:'Space Mono',monospace;font-size:14px;color:var(--amber);padding:8px 0;letter-spacing:0.08em">
          ⟁ KNOWLEDGE AGENT — indexing into RAG store…
        </div>
        """), unsafe_allow_html=True)

        # Stage 3: Index into RAG
        try:
            index_scan_findings(
                scan_id=comp_state.get("scan_id", ""),
                source_id=source_id,
                source_name=source_name,
                scan_results=comp_state.get("scan_results", []),
            )
        except Exception:
            pass  # RAG indexing is non-fatal

        # Stage 4: Save risk trend
        from storage.database import DataSourceDB as DB2
        try:
            trend = build_trend_entry(source_id, {
                "risk_score":         comp_state.get("risk_score", 0.0),
                "pii_count":          sum(1 for r in comp_state.get("scan_results", []) if r.get("check_type") == "pii"),
                "confidential_count": sum(1 for r in comp_state.get("scan_results", []) if r.get("check_type") == "confidential"),
                "total_violations":   comp_state.get("total_flags", 0),
                "compliance_pct":     max(0.0, 100.0 - comp_state.get("risk_score", 0.0)),
            })
            DB2.upsert_risk_trend(trend)
        except Exception:
            pass

        # Stage 5: Alert check
        from agents.alert_agent.nodes import check_thresholds_node, send_alerts_node
        alert_state = {
            "source_id": source_id,
            "source_name": source_name,
            "scan_id": comp_state.get("scan_id", ""),
            "highest_risk": comp_state.get("highest_risk", "low"),
            "total_flags": comp_state.get("total_flags", 0),
            "risk_score": comp_state.get("risk_score", 0.0),
        }
        threshold_result = check_thresholds_node(alert_state)
        if threshold_result.get("should_alert"):
            alert_state.update(threshold_result)
            send_alerts_node(alert_state)

        progress.progress(100, text="Scan complete ✓")
        status_ph.empty()

        # Store in session state
        st.session_state["ds_scan_result"] = comp_state
        st.session_state["ds_meta_result"] = meta_state
        st.session_state["ds_scan_source"] = source_name

    except Exception as e:
        st.error(f"Scan failed: {e}")
        st.exception(e)

# ── DISPLAY RESULTS ────────────────────────────────────────────────────────────
if "ds_scan_result" in st.session_state:
    comp = st.session_state["ds_scan_result"]
    meta = st.session_state.get("ds_meta_result", {})
    scanned_name = st.session_state.get("ds_scan_source", source_name)

    highest = comp.get("highest_risk", "low")
    risk_colors = {"critical": "var(--red)", "high": "var(--high)", "medium": "var(--medium)", "low": "var(--low)"}
    r_color = risk_colors.get(highest, "var(--text)")

    st.markdown(textwrap.dedent(f"""
    <div style="border:1px solid {r_color};border-radius:4px;padding:20px 24px;margin:16px 0;background:rgba(0,0,0,0.2)">
      <div class="caption-label" style="margin-bottom:4px">SCAN COMPLETE</div>
      <div style="display:flex;align-items:center;gap:16px">
        <span style="font-family:'Space Mono',monospace;font-size:24px;font-weight:700;color:var(--text)">{scanned_name}</span>
        <span class="badge badge-{'critical' if highest == 'critical' else 'high' if highest == 'high' else 'medium' if highest == 'medium' else 'low'}">{highest.upper()}</span>
      </div>
    </div>
    """), unsafe_allow_html=True)

    # Metrics
    c1, c2, c3, c4, c5 = st.columns(5)
    metrics = [
        (c1, "TABLES", comp.get("total_tables", 0), "var(--ice)"),
        (c2, "COLUMNS", comp.get("total_columns", 0), "var(--amber)"),
        (c3, "FLAGS", comp.get("total_flags", 0), "var(--red)"),
        (c4, "RISK SCORE", f"{comp.get('risk_score', 0.0):.1f}", r_color),
        (c5, "SCHEMA CHANGES", len(meta.get("changes", [])), "var(--medium)"),
    ]
    for col, label, value, color in metrics:
        with col:
            st.markdown(textwrap.dedent(f"""
            <div style="background:var(--surface);border:1px solid var(--border);padding:14px;border-radius:3px;text-align:center">
              <div class="caption-label" style="margin-bottom:4px">{label}</div>
              <div style="font-family:'JetBrains Mono',monospace;font-size:28px;font-weight:700;color:{color}">{value}</div>
            </div>
            """), unsafe_allow_html=True)

    # Schema changes
    changes = meta.get("changes", [])
    if changes:
        st.markdown('<div class="caption-label" style="margin:20px 0 8px">SCHEMA CHANGES DETECTED</div>', unsafe_allow_html=True)
        sev_badge = {"critical": "badge-critical", "high": "badge-high", "medium": "badge-medium", "low": "badge-low"}
        for chg in changes[:20]:
            sev = chg.get("severity", "medium")
            st.markdown(textwrap.dedent(f"""
            <div style="background:var(--surface);border-left:3px solid var(--{'red' if sev == 'critical' else 'high' if sev == 'high' else 'medium'});padding:10px 14px;margin-bottom:4px;border-radius:0 3px 3px 0">
              <div style="display:flex;align-items:center;gap:8px">
                <span style="font-family:'Space Mono',monospace;font-size:13px;color:var(--amber)">{chg.get('change_type', '').replace('_', ' ').upper()}</span>
                <span style="font-family:'JetBrains Mono',monospace;font-size:14px;color:var(--text)">{chg.get('entity_name', '')}</span>
                <span class="badge {sev_badge.get(sev, 'badge-info')}" style="margin-left:auto">{sev.upper()}</span>
              </div>
            </div>
            """), unsafe_allow_html=True)

    # Flagged columns table
    scan_results = comp.get("scan_results", [])
    if scan_results:
        st.markdown('<div class="caption-label" style="margin:20px 0 8px">FLAGGED COLUMNS</div>', unsafe_allow_html=True)

        col_filter1, col_filter2 = st.columns(2)
        with col_filter1:
            type_filter = st.multiselect(
                "Filter by Type", options=["pii", "confidential", "custom"],
                default=["pii", "confidential", "custom"], key="ds_type_filter"
            )
        with col_filter2:
            risk_filter = st.multiselect(
                "Filter by Risk", options=["critical", "high", "medium", "low"],
                default=["critical", "high", "medium"], key="ds_risk_filter"
            )

        display_rows = [
            {
                "Column": r["entity_name"],
                "Type": r.get("check_type", "").upper(),
                "Category": r.get("flag_category", ""),
                "Risk": (r.get("risk_level") or "low").upper(),
                "Confidence": f"{float(r.get('confidence') or 0):.0%}",
                "Recommendation": (r.get("recommendation") or "")[:80],
            }
            for r in scan_results
            if r.get("check_type") in type_filter
            and (r.get("risk_level") or "low") in risk_filter
        ]

        if display_rows:
            st.dataframe(display_rows, use_container_width=True)
        else:
            st.info("No results match current filters.")
    else:
        st.markdown(textwrap.dedent("""
        <div style="text-align:center;padding:40px;border:1px solid var(--low);background:rgba(79,209,128,0.04);border-radius:4px;margin-top:16px">
          <div style="font-family:'Space Mono',monospace;font-size:37px;margin-bottom:12px">✓</div>
          <div style="font-family:'Space Mono',monospace;font-size:17px;color:var(--low);letter-spacing:0.1em">NO COMPLIANCE ISSUES DETECTED</div>
          <div style="font-family:'DM Sans',sans-serif;font-size:15px;color:var(--text-muted);margin-top:6px">All columns passed the compliance rules engine.</div>
        </div>
        """), unsafe_allow_html=True)

# ── RECENT SCANS ───────────────────────────────────────────────────────────────
st.markdown('<div class="caption-label" style="margin:24px 0 10px">RECENT SCANS FOR THIS SOURCE</div>', unsafe_allow_html=True)
recent = DataSourceDB.get_scan_runs(source_id, limit=8)

if recent:
    for run in recent:
        rl = run.get("highest_risk", "low")
        rc = {"critical": "var(--red)", "high": "var(--high)", "medium": "var(--medium)", "low": "var(--low)"}.get(rl, "var(--text-muted)")
        st.markdown(textwrap.dedent(f"""
        <div style="display:grid;grid-template-columns:2fr 1fr 1fr 1fr 1fr;gap:1px;background:var(--border);border:1px solid var(--border);margin-bottom:4px">
          <div style="background:var(--surface);padding:10px 14px;font-family:'JetBrains Mono',monospace;font-size:13px;color:var(--text-muted)">{run.get('started_at', '')[:16]}</div>
          <div style="background:var(--surface);padding:10px 14px;font-family:'Space Mono',monospace;font-size:13px;color:{rc}">{rl.upper()}</div>
          <div style="background:var(--surface);padding:10px 14px;font-family:'JetBrains Mono',monospace;font-size:13px;color:var(--amber)">{run.get('total_flags', 0)} flags</div>
          <div style="background:var(--surface);padding:10px 14px;font-family:'JetBrains Mono',monospace;font-size:13px;color:var(--text-muted)">{run.get('status', '').upper()}</div>
          <div style="background:var(--surface);padding:10px 14px;font-family:'JetBrains Mono',monospace;font-size:13px;color:var(--text-muted)">{run.get('scan_id', '')[:10]}</div>
        </div>
        """), unsafe_allow_html=True)
else:
    st.markdown(textwrap.dedent("""
    <div style="font-family:'Space Mono',monospace;font-size:14px;color:var(--text-muted);text-align:center;padding:20px;border:1px dashed var(--border);border-radius:3px">
      NO PREVIOUS SCANS FOR THIS SOURCE
    </div>
    """), unsafe_allow_html=True)
