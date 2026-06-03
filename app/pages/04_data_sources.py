# app/pages/04_data_sources.py
"""
Module 04 — Data Source Registry
Add, manage, test, and monitor data source connections.
Noir Amber UI — consistent with existing pages.
"""
import streamlit as st
import textwrap
import json
import uuid
from pathlib import Path

from storage.database import DataSourceDB, init_ds_db
from connectors.factory import ConnectorFactory, CONNECTOR_META, CONNECTOR_FIELDS, SECRET_FIELDS
from app.styles.theme import GLOBAL_CSS

st.set_page_config(page_title="Data Sources", page_icon="🔌", layout="wide")
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

# Ensure tables exist
init_ds_db()

# ── PAGE HEADER ────────────────────────────────────────────────────────────────
st.markdown(textwrap.dedent("""
<div class="animate-fadein" style="padding:0 0 24px">
  <div class="caption-label">MODULE 04</div>
  <h1 style="font-family:'Space Mono',monospace;font-size:33px;font-weight:700;color:var(--text);margin:6px 0 4px">
    DATA <span style="color:var(--amber)">SOURCES</span>
  </h1>
  <p style="color:var(--text-muted);font-size:17px;margin:0">
    Register and manage database, cloud storage, and data warehouse connections.
  </p>
</div>
"""), unsafe_allow_html=True)

# ── TABS ───────────────────────────────────────────────────────────────────────
tab_list, tab_add, tab_alerts = st.tabs(["◈  REGISTERED SOURCES", "⬡  ADD NEW SOURCE", "⟁  ALERT CONFIG"])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 — REGISTERED SOURCES
# ═══════════════════════════════════════════════════════════════════════════════
with tab_list:
    sources = DataSourceDB.get_all_sources()

    if not sources:
        st.markdown(textwrap.dedent("""
        <div style="text-align:center;padding:64px 24px;border:1px dashed var(--border);border-radius:4px;margin-top:24px">
          <div style="font-family:'Space Mono',monospace;font-size:53px;color:var(--border-bright);margin-bottom:16px">◎</div>
          <div style="font-family:'Space Mono',monospace;font-size:16px;color:var(--text-muted);letter-spacing:0.1em;margin-bottom:8px">NO DATA SOURCES REGISTERED</div>
          <div style="font-family:'DM Sans',sans-serif;font-size:16px;color:var(--text-muted)">
            Switch to the <strong>ADD NEW SOURCE</strong> tab to connect your first data source.
          </div>
        </div>
        """), unsafe_allow_html=True)
    else:
        st.markdown(textwrap.dedent(f"""
        <div style="display:inline-flex;align-items:center;gap:16px;background:var(--surface);border:1px solid var(--border);border-radius:3px;padding:12px 20px;margin-bottom:20px">
          <div class="caption-label">REGISTERED SOURCES</div>
          <div style="font-family:'JetBrains Mono',monospace;font-size:33px;font-weight:700;color:var(--amber)">{len(sources)}</div>
        </div>
        """), unsafe_allow_html=True)

        status_colors = {"active": "var(--low)", "paused": "var(--medium)", "error": "var(--red)"}
        status_badges = {"active": "badge-low", "paused": "badge-medium", "error": "badge-critical"}

        for src in sources:
            meta = CONNECTOR_META.get(src["source_type"], {"icon": "🔌", "label": src["source_type"], "category": ""})
            status = src.get("status", "active")
            last_conn = (src.get("last_connected_at") or "Never")[:16]

            col_info, col_actions = st.columns([4, 1])
            with col_info:
                st.markdown(textwrap.dedent(f"""
                <div style="background:var(--surface);border:1px solid var(--border);border-radius:3px;padding:16px 20px;margin-bottom:8px">
                  <div style="display:flex;align-items:center;gap:12px;margin-bottom:8px">
                    <span style="font-size:24px">{meta['icon']}</span>
                    <div>
                      <div style="font-family:'Space Mono',monospace;font-size:16px;font-weight:700;color:var(--text)">{src['name']}</div>
                      <div style="font-family:'JetBrains Mono',monospace;font-size:13px;color:var(--text-muted)">{meta['label']} · {meta['category']}</div>
                    </div>
                    <span class="badge {status_badges.get(status, 'badge-info')}" style="margin-left:auto">{status.upper()}</span>
                  </div>
                  <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:1px;background:var(--border)">
                    <div style="background:var(--surface-2);padding:8px 12px">
                      <div class="caption-label" style="margin-bottom:2px">SOURCE ID</div>
                      <div style="font-family:'JetBrains Mono',monospace;font-size:13px;color:var(--text-muted)">{src['source_id'][:12]}…</div>
                    </div>
                    <div style="background:var(--surface-2);padding:8px 12px">
                      <div class="caption-label" style="margin-bottom:2px">LAST CONNECTED</div>
                      <div style="font-family:'JetBrains Mono',monospace;font-size:13px;color:var(--text-muted)">{last_conn}</div>
                    </div>
                    <div style="background:var(--surface-2);padding:8px 12px">
                      <div class="caption-label" style="margin-bottom:2px">AUTO MONITOR</div>
                      <div style="font-family:'JetBrains Mono',monospace;font-size:13px;color:var(--text-muted)">{'✓ ' + str(src.get('scan_interval_minutes', 60)) + 'min' if src.get('auto_monitor') else '— Off'}</div>
                    </div>
                  </div>
                </div>
                """), unsafe_allow_html=True)

            with col_actions:
                st.markdown('<div style="padding-top:16px"></div>', unsafe_allow_html=True)

                if st.button("▶ TEST", key=f"test_{src['source_id']}", use_container_width=True):
                    with st.spinner("Testing connection…"):
                        try:
                            config = json.loads(src["connection_config"])
                            connector = ConnectorFactory.create(src["source_id"], config)
                            connected = connector.connect()
                            if connected:
                                ok, msg = connector.test_connection()
                                connector.disconnect()
                                if ok:
                                    DataSourceDB.update_source_status(src["source_id"], "active")
                                    st.success(f"✓ {msg}")
                                else:
                                    st.error(f"✗ {msg}")
                            else:
                                st.error("Connection failed")
                        except Exception as e:
                            st.error(f"Error: {e}")

                if st.button("✕ REMOVE", key=f"del_{src['source_id']}", use_container_width=True):
                    DataSourceDB.delete_source(src["source_id"])
                    st.toast("Source removed", icon="🗑️")
                    st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 — ADD NEW SOURCE
# ═══════════════════════════════════════════════════════════════════════════════
with tab_add:
    st.markdown(textwrap.dedent("""
    <div style="margin-bottom:20px">
      <div class="caption-label">SELECT CONNECTOR TYPE</div>
      <p style="color:var(--text-muted);font-size:15px;margin:4px 0 0">Choose the type of data source to connect.</p>
    </div>
    """), unsafe_allow_html=True)

    # Connector type picker (grouped by category)
    categories = {}
    for stype in ConnectorFactory.list_supported():
        meta = CONNECTOR_META[stype]
        cat = meta["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(stype)

    # Build display options
    all_options = []
    for cat, stypes in categories.items():
        for stype in stypes:
            meta = CONNECTOR_META[stype]
            all_options.append(f"{meta['icon']} {meta['label']}")

    all_stypes = [
        stype
        for cat, stypes in categories.items()
        for stype in stypes
    ]

    selected_display = st.selectbox(
        "Connector Type",
        options=all_options,
        label_visibility="collapsed",
    )
    selected_type = all_stypes[all_options.index(selected_display)]

    meta = CONNECTOR_META[selected_type]
    fields = CONNECTOR_FIELDS.get(selected_type, [])

    st.markdown(textwrap.dedent(f"""
    <div style="background:rgba(232,168,56,0.06);border:1px solid rgba(232,168,56,0.2);border-radius:3px;padding:10px 16px;margin:12px 0;font-family:'Space Mono',monospace;font-size:13px;color:var(--amber);letter-spacing:0.08em">
      {meta['icon']} {meta['label']} · {meta['category']}
    </div>
    """), unsafe_allow_html=True)

    with st.form("add_source_form", clear_on_submit=True):
        source_name = st.text_input("Connection Name", placeholder="e.g. Production Postgres, Analytics S3")

        st.markdown('<div class="caption-label" style="margin:16px 0 8px">CONNECTION PARAMETERS</div>', unsafe_allow_html=True)

        field_values = {}
        col_a, col_b = st.columns(2)
        for i, field in enumerate(fields):
            is_secret = field in SECRET_FIELDS
            col = col_a if i % 2 == 0 else col_b
            with col:
                field_values[field] = st.text_input(
                    field.replace("_", " ").title(),
                    type="password" if is_secret else "default",
                    key=f"field_{field}",
                )

        col_opt1, col_opt2 = st.columns(2)
        with col_opt1:
            auto_monitor = st.toggle("Enable Auto-Monitoring", value=False)
        with col_opt2:
            scan_interval = st.number_input(
                "Scan Interval (minutes)", min_value=5, max_value=1440,
                value=60, disabled=not auto_monitor
            )

        test_on_add = st.checkbox("Test connection before saving", value=True)

        submitted = st.form_submit_button("⬡  REGISTER DATA SOURCE", type="primary", use_container_width=True)

    if submitted:
        if not source_name.strip():
            st.error("Connection name is required")
        else:
            # Build config dict (exclude empty secret fields from storage)
            config = {"type": selected_type}
            for field, value in field_values.items():
                if value:
                    config[field] = value

            connection_ok = True
            if test_on_add:
                with st.spinner("Testing connection…"):
                    try:
                        temp_id = str(uuid.uuid4())[:8]
                        connector = ConnectorFactory.create(temp_id, config)
                        if connector.connect():
                            ok, msg = connector.test_connection()
                            connector.disconnect()
                            if ok:
                                st.success(f"✓ Connection successful: {msg}")
                            else:
                                st.error(f"✗ Connection test failed: {msg}")
                                connection_ok = False
                        else:
                            st.error("✗ Could not establish connection")
                            connection_ok = False
                    except ImportError as e:
                        st.warning(f"⚠ Connector package not installed: {e}\nSource will be saved but may not work until the package is installed.")
                    except Exception as e:
                        st.error(f"✗ Error: {e}")
                        connection_ok = False

            if connection_ok:
                source_id = str(uuid.uuid4())
                added = DataSourceDB.add_source({
                    "source_id":             source_id,
                    "name":                  source_name.strip(),
                    "source_type":           selected_type,
                    "connection_config":     json.dumps(config),
                    "auto_monitor":          auto_monitor,
                    "scan_interval_minutes": scan_interval,
                    "status":                "active",
                })

                if added:
                    st.success(f"✓ Source '{source_name}' registered successfully!")
                    st.rerun()
                else:
                    st.error("Failed to save source (name may already exist)")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 — ALERT CONFIG
# ═══════════════════════════════════════════════════════════════════════════════
with tab_alerts:
    st.markdown(textwrap.dedent("""
    <div style="margin-bottom:20px">
      <div class="caption-label">ALERT CHANNELS</div>
      <p style="color:var(--text-muted);font-size:15px;margin:4px 0 0">
        Configure Slack, email, or webhook alerts for high-risk scans.
      </p>
    </div>
    """), unsafe_allow_html=True)

    with st.form("alert_config_form"):
        alert_name = st.text_input("Alert Name", placeholder="e.g. Security Team Slack")

        channel = st.selectbox("Channel", ["slack", "email", "webhook"])

        if channel == "slack":
            webhook_url = st.text_input("Slack Webhook URL", type="password",
                                        placeholder="https://hooks.slack.com/services/...")
            channel_config_data = {"webhook_url": webhook_url}
        elif channel == "email":
            recipients_raw = st.text_input("Recipients (comma-separated)",
                                           placeholder="security@company.com, dpo@company.com")
            channel_config_data = {"recipients": [r.strip() for r in recipients_raw.split(",") if r.strip()]}
        else:
            wh_url = st.text_input("Webhook URL", type="password")
            channel_config_data = {"url": wh_url}

        trigger_levels = st.multiselect(
            "Trigger on risk levels",
            options=["critical", "high", "medium"],
            default=["critical", "high"],
        )
        cooldown = st.number_input("Cooldown (minutes) — suppress duplicates", min_value=0, max_value=1440, value=30)

        alert_submitted = st.form_submit_button("⟁  SAVE ALERT CONFIG", type="primary", use_container_width=True)

    if alert_submitted and alert_name:
        import json
        DataSourceDB.save_alert_config({
            "config_id":          str(uuid.uuid4())[:12],
            "name":               alert_name,
            "channel":            channel,
            "channel_config":     channel_config_data,
            "trigger_risk_levels": trigger_levels,
            "is_active":          True,
            "cooldown_minutes":   cooldown,
        })
        st.success("✓ Alert configuration saved")
        st.rerun()

    # Show existing configs
    configs = DataSourceDB.get_alert_configs()
    if configs:
        st.markdown('<div class="caption-label" style="margin:20px 0 12px">ACTIVE ALERT CONFIGS</div>', unsafe_allow_html=True)
        for cfg in configs:
            levels = cfg.get("trigger_risk_levels", [])
            if isinstance(levels, str):
                levels = json.loads(levels)
            st.markdown(textwrap.dedent(f"""
            <div style="background:var(--surface);border:1px solid var(--border);border-radius:3px;padding:12px 16px;margin-bottom:8px;display:flex;justify-content:space-between;align-items:center">
              <div>
                <div style="font-family:'Space Mono',monospace;font-size:15px;color:var(--text)">{cfg['name']}</div>
                <div style="font-family:'JetBrains Mono',monospace;font-size:13px;color:var(--text-muted);margin-top:2px">{cfg['channel'].upper()} · triggers on: {', '.join(levels)}</div>
              </div>
              <span class="badge badge-low">ACTIVE</span>
            </div>
            """), unsafe_allow_html=True)
