# intelligence/change_engine.py
"""
Change Engine — detects structural and statistical differences between two metadata snapshots.
Used by the metadata agent to determine what changed and how severe the change is.
"""
import uuid
from datetime import datetime


def diff_schemas(prev: dict, curr: dict, source_id: str,
                 snapshot_before_id: str = None,
                 snapshot_after_id: str = None) -> list:
    """
    Compute structural differences between two metadata snapshot dicts.

    Returns a list of change dicts, each with:
        change_id, source_id, change_type, entity_type, entity_name,
        change_detail, severity, snapshot_before, snapshot_after, detected_at
    """
    changes = []
    now = datetime.utcnow().isoformat()

    prev_tables = {t["name"]: t for t in prev.get("tables", [])}
    curr_tables = {t["name"]: t for t in curr.get("tables", [])}

    # ── New tables ──────────────────────────────────────────────────────
    for table_name in curr_tables:
        if table_name not in prev_tables:
            changes.append({
                "change_id":      str(uuid.uuid4())[:12],
                "source_id":      source_id,
                "change_type":    "new_table",
                "entity_type":    "table",
                "entity_name":    table_name,
                "change_detail":  {
                    "columns": [c["name"] for c in curr_tables[table_name].get("columns", [])],
                    "column_count": len(curr_tables[table_name].get("columns", [])),
                },
                "severity":       "high",
                "snapshot_before": snapshot_before_id,
                "snapshot_after":  snapshot_after_id,
                "detected_at":    now,
            })

    # ── Dropped tables ──────────────────────────────────────────────────
    for table_name in prev_tables:
        if table_name not in curr_tables:
            changes.append({
                "change_id":      str(uuid.uuid4())[:12],
                "source_id":      source_id,
                "change_type":    "dropped_table",
                "entity_type":    "table",
                "entity_name":    table_name,
                "change_detail":  {
                    "column_count": len(prev_tables[table_name].get("columns", [])),
                },
                "severity":       "critical",
                "snapshot_before": snapshot_before_id,
                "snapshot_after":  snapshot_after_id,
                "detected_at":    now,
            })

    # ── Modified tables ──────────────────────────────────────────────────
    for table_name in curr_tables:
        if table_name not in prev_tables:
            continue

        prev_cols = {c["name"]: c for c in prev_tables[table_name].get("columns", [])}
        curr_cols = {c["name"]: c for c in curr_tables[table_name].get("columns", [])}

        # New columns
        for col_name in curr_cols:
            if col_name not in prev_cols:
                changes.append({
                    "change_id":      str(uuid.uuid4())[:12],
                    "source_id":      source_id,
                    "change_type":    "new_column",
                    "entity_type":    "column",
                    "entity_name":    f"{table_name}.{col_name}",
                    "change_detail":  {
                        "table":     table_name,
                        "column":    col_name,
                        "data_type": curr_cols[col_name].get("data_type"),
                    },
                    "severity":       "high",
                    "snapshot_before": snapshot_before_id,
                    "snapshot_after":  snapshot_after_id,
                    "detected_at":    now,
                })

        # Dropped columns
        for col_name in prev_cols:
            if col_name not in curr_cols:
                changes.append({
                    "change_id":      str(uuid.uuid4())[:12],
                    "source_id":      source_id,
                    "change_type":    "dropped_column",
                    "entity_type":    "column",
                    "entity_name":    f"{table_name}.{col_name}",
                    "change_detail":  {
                        "table":     table_name,
                        "column":    col_name,
                        "data_type": prev_cols[col_name].get("data_type"),
                    },
                    "severity":       "high",
                    "snapshot_before": snapshot_before_id,
                    "snapshot_after":  snapshot_after_id,
                    "detected_at":    now,
                })

        # Type changes
        for col_name in curr_cols:
            if col_name in prev_cols:
                prev_type = prev_cols[col_name].get("data_type", "")
                curr_type = curr_cols[col_name].get("data_type", "")
                if prev_type != curr_type:
                    changes.append({
                        "change_id":      str(uuid.uuid4())[:12],
                        "source_id":      source_id,
                        "change_type":    "type_change",
                        "entity_type":    "column",
                        "entity_name":    f"{table_name}.{col_name}",
                        "change_detail":  {
                            "table":  table_name,
                            "column": col_name,
                            "before": prev_type,
                            "after":  curr_type,
                        },
                        "severity":       "medium",
                        "snapshot_before": snapshot_before_id,
                        "snapshot_after":  snapshot_after_id,
                        "detected_at":    now,
                    })

    return changes


def check_statistical_changes(prev: dict, curr: dict, source_id: str,
                               snapshot_before_id: str = None,
                               snapshot_after_id: str = None) -> list:
    """
    Detect anomalies in statistical properties (row count spikes, etc.)
    Used when schema hash is unchanged but data volume changed significantly.
    """
    changes = []
    now = datetime.utcnow().isoformat()

    prev_tables = {t["name"]: t for t in prev.get("tables", [])}
    curr_tables = {t["name"]: t for t in curr.get("tables", [])}

    for table_name, curr_table in curr_tables.items():
        if table_name not in prev_tables:
            continue

        prev_rows = prev_tables[table_name].get("row_count") or 0
        curr_rows = curr_table.get("row_count") or 0

        # Row count spike > 300%
        if prev_rows > 0 and curr_rows > prev_rows * 3:
            changes.append({
                "change_id":      str(uuid.uuid4())[:12],
                "source_id":      source_id,
                "change_type":    "row_count_spike",
                "entity_type":    "table",
                "entity_name":    table_name,
                "change_detail":  {
                    "before": prev_rows,
                    "after":  curr_rows,
                    "ratio":  round(curr_rows / max(prev_rows, 1), 2),
                },
                "severity":       "medium",
                "snapshot_before": snapshot_before_id,
                "snapshot_after":  snapshot_after_id,
                "detected_at":    now,
            })

        # Row count drop > 80% (potential data deletion)
        if prev_rows > 1000 and curr_rows < prev_rows * 0.2:
            changes.append({
                "change_id":      str(uuid.uuid4())[:12],
                "source_id":      source_id,
                "change_type":    "row_count_drop",
                "entity_type":    "table",
                "entity_name":    table_name,
                "change_detail":  {
                    "before": prev_rows,
                    "after":  curr_rows,
                    "drop_pct": round((1 - curr_rows / prev_rows) * 100, 1),
                },
                "severity":       "high",
                "snapshot_before": snapshot_before_id,
                "snapshot_after":  snapshot_after_id,
                "detected_at":    now,
            })

    return changes
