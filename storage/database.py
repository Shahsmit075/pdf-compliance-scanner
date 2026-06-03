# storage/database.py
"""
SQLite-based persistence for scan results.
Each upload gets a UUID; results stored as JSON blobs.
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
