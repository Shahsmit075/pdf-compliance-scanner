# storage/database.py
"""
SQLite-based persistence for scan results.
Each upload gets a UUID; results stored as JSON blobs.

Extended with data-source scanning tables (migrations 001-008).
Existing PDF scanner functions are fully preserved.
"""
import sqlite3
import json
import os
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / "compliance.db"


def get_connection():
    """Get a SQLite connection with WAL mode for concurrent reads."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create database tables if they don't exist."""
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS scans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                upload_id TEXT UNIQUE NOT NULL,
                pdf_name TEXT NOT NULL,
                scanned_at TEXT NOT NULL,
                total_pages INTEGER DEFAULT 0,
                total_flags INTEGER DEFAULT 0,
                highest_risk TEXT DEFAULT 'low',
                status TEXT DEFAULT 'completed',
                result_json TEXT,
                report_path TEXT
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_upload_id ON scans(upload_id)
        """)
        
        # Graceful migrations for new columns
        for col_name, col_type in [
            ("total_tokens", "INTEGER DEFAULT 0"),
            ("execution_time_sec", "REAL DEFAULT 0.0"),
            ("ai_provider", "TEXT DEFAULT 'groq'")
        ]:
            try:
                conn.execute(f"ALTER TABLE scans ADD COLUMN {col_name} {col_type}")
            except sqlite3.OperationalError:
                # Column already exists
                pass

        conn.commit()


def save_result(upload_id: str, pdf_name: str, result: dict) -> None:
    """Save scan result to database."""
    init_db()
    summary = result.get("summary", {})

    with get_connection() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO scans
            (upload_id, pdf_name, scanned_at, total_pages, total_flags, 
             highest_risk, status, result_json, report_path,
             total_tokens, execution_time_sec, ai_provider)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            upload_id,
            pdf_name,
            datetime.now().isoformat(),
            result.get("total_pages", 0),
            summary.get("total_flags", 0),
            summary.get("highest_risk", "low"),
            "completed",
            json.dumps(result),  # Store full result as JSON
            result.get("report_path"),
            result.get("total_tokens_used", 0),
            result.get("scan_duration_seconds", 0.0),
            result.get("ai_provider_used", "groq"),
        ))
        conn.commit()


def get_result(upload_id: str) -> dict | None:
    """Retrieve scan result by upload ID."""
    init_db()
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM scans WHERE upload_id = ?", (upload_id,)
        ).fetchone()

    if not row:
        return None

    result = dict(row)
    if result.get("result_json"):
        result["data"] = json.loads(result["result_json"])
    return result


def get_all_scans() -> list:
    """Get all scan records (metadata only, not full JSON)."""
    init_db()
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT upload_id, pdf_name, scanned_at, total_pages, 
                   total_flags, highest_risk, status, report_path,
                   total_tokens, execution_time_sec, ai_provider
            FROM scans 
            ORDER BY scanned_at DESC 
            LIMIT 50
        """).fetchall()
    return [dict(row) for row in rows]


def delete_scan(upload_id: str) -> bool:
    """Delete a scan record."""
    with get_connection() as conn:
        cursor = conn.execute("DELETE FROM scans WHERE upload_id = ?", (upload_id,))
        conn.commit()
        return cursor.rowcount > 0


# ─────────────────────────────────────────────────────────────────────────────
# Data Source Tables — added alongside the existing PDF scanner tables
# ─────────────────────────────────────────────────────────────────────────────

DS_MIGRATIONS = [
    # data_sources — registry
    """
    CREATE TABLE IF NOT EXISTS data_sources (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        source_id       TEXT UNIQUE NOT NULL,
        name            TEXT NOT NULL UNIQUE,
        source_type     TEXT NOT NULL,
        connection_config TEXT NOT NULL,
        credentials_ref TEXT,
        status          TEXT DEFAULT 'active',
        auto_monitor    INTEGER DEFAULT 0,
        scan_interval_minutes INTEGER DEFAULT 60,
        last_connected_at TEXT,
        created_at      TEXT DEFAULT (datetime('now')),
        created_by      TEXT
    )
    """,
    # metadata_snapshots
    """
    CREATE TABLE IF NOT EXISTS metadata_snapshots (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        snapshot_id     TEXT UNIQUE NOT NULL,
        source_id       TEXT NOT NULL REFERENCES data_sources(source_id),
        snapshot_type   TEXT NOT NULL,
        snapshot_json   TEXT NOT NULL,
        schema_hash     TEXT NOT NULL,
        table_count     INTEGER DEFAULT 0,
        column_count    INTEGER DEFAULT 0,
        captured_at     TEXT DEFAULT (datetime('now')),
        agent_run_id    TEXT
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_snapshots_source ON metadata_snapshots(source_id, captured_at DESC)",
    # column_metadata
    """
    CREATE TABLE IF NOT EXISTS column_metadata (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        snapshot_id     TEXT NOT NULL REFERENCES metadata_snapshots(snapshot_id),
        source_id       TEXT NOT NULL,
        table_name      TEXT NOT NULL,
        column_name     TEXT NOT NULL,
        data_type       TEXT,
        is_nullable     INTEGER,
        classification  TEXT,
        classification_confidence REAL,
        is_new          INTEGER DEFAULT 0,
        is_modified     INTEGER DEFAULT 0,
        captured_at     TEXT DEFAULT (datetime('now'))
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_col_meta_source ON column_metadata(source_id, table_name)",
    # detected_changes
    """
    CREATE TABLE IF NOT EXISTS detected_changes (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        change_id       TEXT UNIQUE NOT NULL,
        source_id       TEXT NOT NULL REFERENCES data_sources(source_id),
        snapshot_before TEXT REFERENCES metadata_snapshots(snapshot_id),
        snapshot_after  TEXT REFERENCES metadata_snapshots(snapshot_id),
        change_type     TEXT NOT NULL,
        entity_type     TEXT NOT NULL,
        entity_name     TEXT NOT NULL,
        change_detail   TEXT NOT NULL,
        severity        TEXT DEFAULT 'medium',
        triggered_scan  INTEGER DEFAULT 0,
        detected_at     TEXT DEFAULT (datetime('now'))
    )
    """,
    # ds_scan_runs
    """
    CREATE TABLE IF NOT EXISTS ds_scan_runs (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        scan_id         TEXT UNIQUE NOT NULL,
        source_id       TEXT REFERENCES data_sources(source_id),
        scan_type       TEXT NOT NULL,
        trigger_change_id TEXT,
        status          TEXT DEFAULT 'running',
        total_tables    INTEGER DEFAULT 0,
        total_columns   INTEGER DEFAULT 0,
        total_flags     INTEGER DEFAULT 0,
        risk_score      REAL DEFAULT 0.0,
        highest_risk    TEXT DEFAULT 'low',
        started_at      TEXT DEFAULT (datetime('now')),
        completed_at    TEXT,
        initiated_by    TEXT,
        result_json     TEXT,
        error_detail    TEXT
    )
    """,
    # ds_scan_results
    """
    CREATE TABLE IF NOT EXISTS ds_scan_results (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        result_id       TEXT UNIQUE NOT NULL,
        scan_id         TEXT NOT NULL REFERENCES ds_scan_runs(scan_id),
        source_id       TEXT NOT NULL,
        entity_type     TEXT NOT NULL,
        entity_name     TEXT NOT NULL,
        check_type      TEXT NOT NULL,
        flag_category   TEXT,
        confidence      REAL,
        risk_level      TEXT,
        evidence        TEXT,
        recommendation  TEXT,
        is_acknowledged INTEGER DEFAULT 0,
        acknowledged_by TEXT,
        acknowledged_at TEXT,
        created_at      TEXT DEFAULT (datetime('now'))
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_ds_scan_results_scan ON ds_scan_results(scan_id)",
    "CREATE INDEX IF NOT EXISTS idx_ds_scan_results_source ON ds_scan_results(source_id)",
    # risk_trends
    """
    CREATE TABLE IF NOT EXISTS risk_trends (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        source_id       TEXT NOT NULL REFERENCES data_sources(source_id),
        trend_date      TEXT NOT NULL,
        risk_score      REAL NOT NULL,
        pii_count       INTEGER DEFAULT 0,
        confidential_count INTEGER DEFAULT 0,
        abuse_count     INTEGER DEFAULT 0,
        custom_count    INTEGER DEFAULT 0,
        total_violations INTEGER DEFAULT 0,
        compliance_pct  REAL DEFAULT 100.0,
        UNIQUE(source_id, trend_date)
    )
    """,
    # compliance_drift
    """
    CREATE TABLE IF NOT EXISTS compliance_drift (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        drift_id        TEXT UNIQUE NOT NULL,
        source_id       TEXT NOT NULL REFERENCES data_sources(source_id),
        entity_name     TEXT NOT NULL,
        drift_type      TEXT NOT NULL,
        risk_before     TEXT NOT NULL,
        risk_after      TEXT NOT NULL,
        risk_delta      REAL NOT NULL,
        drift_detail    TEXT NOT NULL,
        scan_before     TEXT,
        scan_after      TEXT,
        detected_at     TEXT DEFAULT (datetime('now'))
    )
    """,
    # alert_configs
    """
    CREATE TABLE IF NOT EXISTS alert_configs (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        config_id       TEXT UNIQUE NOT NULL,
        name            TEXT NOT NULL,
        channel         TEXT NOT NULL,
        channel_config  TEXT NOT NULL,
        trigger_risk_levels TEXT NOT NULL,
        is_active       INTEGER DEFAULT 1,
        cooldown_minutes INTEGER DEFAULT 30,
        created_at      TEXT DEFAULT (datetime('now'))
    )
    """,
    # alert_history
    """
    CREATE TABLE IF NOT EXISTS alert_history (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        alert_id        TEXT UNIQUE NOT NULL,
        config_id       TEXT REFERENCES alert_configs(config_id),
        scan_id         TEXT REFERENCES ds_scan_runs(scan_id),
        channel         TEXT,
        message_preview TEXT,
        status          TEXT,
        sent_at         TEXT DEFAULT (datetime('now'))
    )
    """,
]


def init_ds_db():
    """Create all data-source tables if they don't exist."""
    with get_connection() as conn:
        for sql in DS_MIGRATIONS:
            conn.execute(sql)
        conn.commit()


class DataSourceDB:
    """CRUD operations for all data-source-related tables."""

    # ── Data Sources ──────────────────────────────────────────────────────

    @staticmethod
    def add_source(source: dict) -> bool:
        init_ds_db()
        with get_connection() as conn:
            try:
                conn.execute("""
                    INSERT INTO data_sources
                    (source_id, name, source_type, connection_config, credentials_ref,
                     status, auto_monitor, scan_interval_minutes, created_by)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    source["source_id"],
                    source["name"],
                    source["source_type"],
                    source["connection_config"],
                    source.get("credentials_ref"),
                    source.get("status", "active"),
                    int(source.get("auto_monitor", False)),
                    source.get("scan_interval_minutes", 60),
                    source.get("created_by"),
                ))
                conn.commit()
                return True
            except Exception:
                return False

    @staticmethod
    def get_source(source_id: str) -> dict | None:
        init_ds_db()
        with get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM data_sources WHERE source_id = ?", (source_id,)
            ).fetchone()
        return dict(row) if row else None

    @staticmethod
    def get_all_sources() -> list:
        init_ds_db()
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM data_sources ORDER BY created_at DESC"
            ).fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def update_source_status(source_id: str, status: str, last_connected_at: str = None):
        with get_connection() as conn:
            conn.execute(
                "UPDATE data_sources SET status = ?, last_connected_at = ? WHERE source_id = ?",
                (status, last_connected_at or datetime.utcnow().isoformat(), source_id)
            )
            conn.commit()

    @staticmethod
    def delete_source(source_id: str) -> bool:
        with get_connection() as conn:
            cursor = conn.execute("DELETE FROM data_sources WHERE source_id = ?", (source_id,))
            conn.commit()
            return cursor.rowcount > 0

    # ── Metadata Snapshots ────────────────────────────────────────────────

    @staticmethod
    def save_snapshot(snapshot: dict) -> bool:
        init_ds_db()
        with get_connection() as conn:
            try:
                conn.execute("""
                    INSERT INTO metadata_snapshots
                    (snapshot_id, source_id, snapshot_type, snapshot_json,
                     schema_hash, table_count, column_count, captured_at, agent_run_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    snapshot["snapshot_id"],
                    snapshot["source_id"],
                    snapshot.get("snapshot_type", "schema"),
                    snapshot["snapshot_json"],
                    snapshot["schema_hash"],
                    snapshot.get("table_count", 0),
                    snapshot.get("column_count", 0),
                    snapshot.get("captured_at", datetime.utcnow().isoformat()),
                    snapshot.get("agent_run_id"),
                ))
                conn.commit()
                return True
            except Exception:
                return False

    @staticmethod
    def get_latest_snapshot(source_id: str) -> dict | None:
        init_ds_db()
        with get_connection() as conn:
            row = conn.execute("""
                SELECT * FROM metadata_snapshots
                WHERE source_id = ?
                ORDER BY captured_at DESC LIMIT 1
            """, (source_id,)).fetchone()
        return dict(row) if row else None

    @staticmethod
    def get_snapshot_history(source_id: str, limit: int = 10) -> list:
        init_ds_db()
        with get_connection() as conn:
            rows = conn.execute("""
                SELECT snapshot_id, schema_hash, table_count, column_count, captured_at
                FROM metadata_snapshots
                WHERE source_id = ?
                ORDER BY captured_at DESC LIMIT ?
            """, (source_id, limit)).fetchall()
        return [dict(r) for r in rows]

    # ── Detected Changes ──────────────────────────────────────────────────

    @staticmethod
    def save_changes(changes: list) -> int:
        """Batch-insert detected changes. Returns number inserted."""
        init_ds_db()
        inserted = 0
        with get_connection() as conn:
            for change in changes:
                try:
                    conn.execute("""
                        INSERT OR IGNORE INTO detected_changes
                        (change_id, source_id, snapshot_before, snapshot_after,
                         change_type, entity_type, entity_name, change_detail,
                         severity, triggered_scan, detected_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        change["change_id"],
                        change["source_id"],
                        change.get("snapshot_before"),
                        change.get("snapshot_after"),
                        change["change_type"],
                        change["entity_type"],
                        change["entity_name"],
                        json.dumps(change.get("change_detail", {})),
                        change.get("severity", "medium"),
                        int(change.get("triggered_scan", False)),
                        change.get("detected_at", datetime.utcnow().isoformat()),
                    ))
                    inserted += 1
                except Exception:
                    pass
            conn.commit()
        return inserted

    @staticmethod
    def get_changes(source_id: str, limit: int = 50) -> list:
        init_ds_db()
        with get_connection() as conn:
            rows = conn.execute("""
                SELECT * FROM detected_changes
                WHERE source_id = ?
                ORDER BY detected_at DESC LIMIT ?
            """, (source_id, limit)).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            if d.get("change_detail"):
                try:
                    d["change_detail"] = json.loads(d["change_detail"])
                except Exception:
                    pass
            result.append(d)
        return result

    # ── DS Scan Runs ──────────────────────────────────────────────────────

    @staticmethod
    def create_scan_run(scan: dict) -> bool:
        init_ds_db()
        with get_connection() as conn:
            try:
                conn.execute("""
                    INSERT INTO ds_scan_runs
                    (scan_id, source_id, scan_type, trigger_change_id, status,
                     started_at, initiated_by)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    scan["scan_id"],
                    scan.get("source_id"),
                    scan.get("scan_type", "manual"),
                    scan.get("trigger_change_id"),
                    "running",
                    scan.get("started_at", datetime.utcnow().isoformat()),
                    scan.get("initiated_by", "user"),
                ))
                conn.commit()
                return True
            except Exception:
                return False

    @staticmethod
    def complete_scan_run(scan_id: str, result: dict):
        with get_connection() as conn:
            conn.execute("""
                UPDATE ds_scan_runs
                SET status = ?, total_tables = ?, total_columns = ?,
                    total_flags = ?, risk_score = ?, highest_risk = ?,
                    completed_at = ?, result_json = ?, error_detail = ?
                WHERE scan_id = ?
            """, (
                result.get("status", "completed"),
                result.get("total_tables", 0),
                result.get("total_columns", 0),
                result.get("total_flags", 0),
                result.get("risk_score", 0.0),
                result.get("highest_risk", "low"),
                datetime.utcnow().isoformat(),
                json.dumps(result.get("result_data", {})),
                result.get("error_detail"),
                scan_id,
            ))
            conn.commit()

    @staticmethod
    def get_scan_runs(source_id: str = None, limit: int = 30) -> list:
        init_ds_db()
        with get_connection() as conn:
            if source_id:
                rows = conn.execute("""
                    SELECT * FROM ds_scan_runs WHERE source_id = ?
                    ORDER BY started_at DESC LIMIT ?
                """, (source_id, limit)).fetchall()
            else:
                rows = conn.execute("""
                    SELECT * FROM ds_scan_runs
                    ORDER BY started_at DESC LIMIT ?
                """, (limit,)).fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def get_scan_run(scan_id: str) -> dict | None:
        init_ds_db()
        with get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM ds_scan_runs WHERE scan_id = ?", (scan_id,)
            ).fetchone()
        if not row:
            return None
        d = dict(row)
        if d.get("result_json"):
            try:
                d["result_data"] = json.loads(d["result_json"])
            except Exception:
                pass
        return d

    # ── DS Scan Results ───────────────────────────────────────────────────

    @staticmethod
    def save_scan_results(results: list) -> int:
        init_ds_db()
        inserted = 0
        with get_connection() as conn:
            for r in results:
                try:
                    conn.execute("""
                        INSERT OR IGNORE INTO ds_scan_results
                        (result_id, scan_id, source_id, entity_type, entity_name,
                         check_type, flag_category, confidence, risk_level,
                         evidence, recommendation, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        r["result_id"],
                        r["scan_id"],
                        r["source_id"],
                        r.get("entity_type", "column"),
                        r["entity_name"],
                        r.get("check_type", "pii"),
                        r.get("flag_category"),
                        r.get("confidence"),
                        r.get("risk_level", "medium"),
                        r.get("evidence"),
                        r.get("recommendation"),
                        r.get("created_at", datetime.utcnow().isoformat()),
                    ))
                    inserted += 1
                except Exception:
                    pass
            conn.commit()
        return inserted

    @staticmethod
    def get_scan_results(scan_id: str) -> list:
        init_ds_db()
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM ds_scan_results WHERE scan_id = ? ORDER BY risk_level DESC",
                (scan_id,)
            ).fetchall()
        return [dict(r) for r in rows]

    # ── Risk Trends ───────────────────────────────────────────────────────

    @staticmethod
    def upsert_risk_trend(trend: dict):
        init_ds_db()
        with get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO risk_trends
                (source_id, trend_date, risk_score, pii_count, confidential_count,
                 abuse_count, custom_count, total_violations, compliance_pct)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                trend["source_id"],
                trend["trend_date"],
                trend.get("risk_score", 0.0),
                trend.get("pii_count", 0),
                trend.get("confidential_count", 0),
                trend.get("abuse_count", 0),
                trend.get("custom_count", 0),
                trend.get("total_violations", 0),
                trend.get("compliance_pct", 100.0),
            ))
            conn.commit()

    @staticmethod
    def get_risk_trends(source_id: str, days: int = 30) -> list:
        init_ds_db()
        with get_connection() as conn:
            rows = conn.execute("""
                SELECT * FROM risk_trends
                WHERE source_id = ?
                ORDER BY trend_date DESC LIMIT ?
            """, (source_id, days)).fetchall()
        return [dict(r) for r in reversed(rows)]  # Chronological order

    @staticmethod
    def get_all_latest_trends() -> list:
        """Get latest risk entry per source for overview dashboard."""
        init_ds_db()
        with get_connection() as conn:
            rows = conn.execute("""
                SELECT rt.* FROM risk_trends rt
                INNER JOIN (
                    SELECT source_id, MAX(trend_date) as max_date
                    FROM risk_trends GROUP BY source_id
                ) latest ON rt.source_id = latest.source_id
                    AND rt.trend_date = latest.max_date
            """).fetchall()
        return [dict(r) for r in rows]

    # ── Alert Configs ─────────────────────────────────────────────────────

    @staticmethod
    def save_alert_config(config: dict) -> bool:
        init_ds_db()
        with get_connection() as conn:
            try:
                conn.execute("""
                    INSERT OR REPLACE INTO alert_configs
                    (config_id, name, channel, channel_config, trigger_risk_levels,
                     is_active, cooldown_minutes)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    config["config_id"],
                    config["name"],
                    config["channel"],
                    json.dumps(config.get("channel_config", {})),
                    json.dumps(config.get("trigger_risk_levels", ["critical", "high"])),
                    int(config.get("is_active", True)),
                    config.get("cooldown_minutes", 30),
                ))
                conn.commit()
                return True
            except Exception:
                return False

    @staticmethod
    def get_alert_configs() -> list:
        init_ds_db()
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM alert_configs WHERE is_active = 1"
            ).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            for field in ["channel_config", "trigger_risk_levels"]:
                if d.get(field):
                    try:
                        d[field] = json.loads(d[field])
                    except Exception:
                        pass
            result.append(d)
        return result

    @staticmethod
    def log_alert(alert: dict):
        init_ds_db()
        with get_connection() as conn:
            conn.execute("""
                INSERT OR IGNORE INTO alert_history
                (alert_id, config_id, scan_id, channel, message_preview, status, sent_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                alert["alert_id"],
                alert.get("config_id"),
                alert.get("scan_id"),
                alert.get("channel"),
                alert.get("message_preview", "")[:200],
                alert.get("status", "sent"),
                alert.get("sent_at", datetime.utcnow().isoformat()),
            ))
            conn.commit()
