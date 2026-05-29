# agents/metadata_agent/nodes.py
"""
Metadata Agent Node implementations.

Flow: connect_source → collect_metadata → compare_snapshots
        → [has_changes] → classify_changes → save_snapshot → done
        → [no_changes]  → log_no_change → done
"""
import uuid
import json
import logging
from datetime import datetime

from connectors.factory import ConnectorFactory
from connectors.secrets.secret_manager import SecretManager
from storage.database import DataSourceDB
from intelligence.change_engine import diff_schemas, check_statistical_changes
from agents.metadata_agent.state import MetadataAgentState

logger = logging.getLogger(__name__)

# Module-level connector cache (keyed by source_id for reuse across nodes)
_connector_cache: dict = {}


def connect_source_node(state: MetadataAgentState) -> dict:
    """Load source config from DB, resolve secrets, create and connect connector."""
    source = DataSourceDB.get_source(state["source_id"])

    if not source:
        return {
            "connection_status": "failed",
            "connector_type": "",
            "errors": [f"Source {state['source_id']} not found"],
        }

    try:
        config = json.loads(source["connection_config"])
        config = SecretManager.resolve_config(config)

        connector = ConnectorFactory.create(state["source_id"], config)
        connected = connector.connect()

        if not connected:
            DataSourceDB.update_source_status(state["source_id"], "error")
            return {
                "connection_status": "failed",
                "connector_type": config.get("type", ""),
                "errors": ["connector.connect() returned False"],
            }

        ok, message = connector.test_connection()
        if not ok:
            DataSourceDB.update_source_status(state["source_id"], "error")
            return {
                "connection_status": "failed",
                "connector_type": config.get("type", ""),
                "errors": [f"Connection test failed: {message}"],
            }

        _connector_cache[state["source_id"]] = connector
        DataSourceDB.update_source_status(state["source_id"], "active")

        return {
            "connection_status": "connected",
            "connector_type": config.get("type", ""),
            "errors": [],
        }

    except Exception as e:
        logger.error(f"[{state['source_id']}] connect_source_node error: {e}")
        return {
            "connection_status": "failed",
            "connector_type": "",
            "errors": [str(e)],
        }


def collect_metadata_node(state: MetadataAgentState) -> dict:
    """Collect current metadata snapshot from the data source."""
    connector = _connector_cache.get(state["source_id"])
    if not connector:
        return {"errors": state.get("errors", []) + ["No connector in cache"]}

    try:
        metadata = connector.get_metadata()
        metadata_dict = metadata.to_dict()
        return {
            "current_metadata": metadata_dict,
            "current_schema_hash": metadata_dict["schema_hash"],
        }
    except Exception as e:
        logger.error(f"[{state['source_id']}] collect_metadata_node error: {e}")
        return {"errors": state.get("errors", []) + [f"Metadata error: {e}"]}


def compare_snapshots_node(state: MetadataAgentState) -> dict:
    """
    Compare current metadata hash against last stored snapshot.
    Uses hash for O(1) quick check, then detailed diff only when needed.
    """
    source_id = state["source_id"]
    last_snapshot = DataSourceDB.get_latest_snapshot(source_id)

    if not last_snapshot:
        logger.info(f"[{source_id}] No prior snapshot — initial scan")
        return {
            "has_changes": True,
            "previous_snapshot_id": None,
            "previous_schema_hash": None,
            "changes": [{"type": "initial_scan", "detail": "First metadata collection"}],
        }

    prev_hash = last_snapshot["schema_hash"]
    curr_hash = state.get("current_schema_hash")

    if prev_hash == curr_hash:
        # Schema unchanged — check statistics
        prev_meta = json.loads(last_snapshot["snapshot_json"])
        stat_changes = check_statistical_changes(
            prev_meta, state["current_metadata"],
            source_id=source_id,
            snapshot_before_id=last_snapshot["snapshot_id"],
        )
        return {
            "has_changes": bool(stat_changes),
            "previous_snapshot_id": last_snapshot["snapshot_id"],
            "previous_schema_hash": prev_hash,
            "changes": stat_changes,
        }

    # Hash differs — full schema diff
    prev_meta = json.loads(last_snapshot["snapshot_json"])
    structural_changes = diff_schemas(
        prev_meta, state["current_metadata"],
        source_id=source_id,
        snapshot_before_id=last_snapshot["snapshot_id"],
    )

    return {
        "has_changes": bool(structural_changes),
        "previous_snapshot_id": last_snapshot["snapshot_id"],
        "previous_schema_hash": prev_hash,
        "changes": structural_changes,
    }


def classify_changes_node(state: MetadataAgentState) -> dict:
    """
    Classify changes by severity and determine whether a compliance scan is needed.
    High/critical severity changes always trigger a scan.
    """
    changes = state.get("changes", [])
    SCAN_TRIGGERS = {"new_table", "new_column", "type_change", "initial_scan",
                     "row_count_spike"}

    should_scan = any(
        c.get("change_type") in SCAN_TRIGGERS or
        c.get("severity") in {"high", "critical"}
        for c in changes
    )

    scan_scope = []
    for c in changes:
        if c.get("change_type") in {"new_table", "new_column", "type_change"}:
            detail = c.get("change_detail") or c.get("detail", {})
            table = detail.get("table") if isinstance(detail, dict) else None
            if table and table not in scan_scope:
                scan_scope.append(table)

    return {
        "should_scan": should_scan,
        "scan_scope": scan_scope,
    }


def save_snapshot_node(state: MetadataAgentState) -> dict:
    """Persist metadata snapshot and detected changes to the database."""
    source_id = state["source_id"]
    metadata = state.get("current_metadata", {})
    snapshot_id = str(uuid.uuid4())

    snap_saved = DataSourceDB.save_snapshot({
        "snapshot_id":   snapshot_id,
        "source_id":     source_id,
        "snapshot_type": "schema",
        "snapshot_json": json.dumps(metadata),
        "schema_hash":   metadata.get("schema_hash", ""),
        "table_count":   metadata.get("table_count", 0),
        "column_count":  metadata.get("column_count", 0),
        "captured_at":   metadata.get("captured_at", datetime.utcnow().isoformat()),
        "agent_run_id":  state.get("run_id"),
    })

    # Save detected changes (skip sentinel initial_scan entries)
    change_ids = []
    real_changes = [c for c in state.get("changes", []) if c.get("change_id")]
    # Add snapshot_after to all changes
    for c in real_changes:
        c["snapshot_after"] = snapshot_id
    if real_changes:
        DataSourceDB.save_changes(real_changes)
        change_ids = [c["change_id"] for c in real_changes]

    return {
        "snapshot_id":  snapshot_id,
        "change_ids":   change_ids,
        "completed_at": datetime.utcnow().isoformat(),
    }


def log_no_change_node(state: MetadataAgentState) -> dict:
    """Log that no changes were detected (still saves a snapshot for history)."""
    logger.info(f"[{state['source_id']}] No schema changes detected")
    return save_snapshot_node(state)
