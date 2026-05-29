# connectors/base/base_connector.py
"""
Abstract base class for all data source connectors.
Every connector MUST implement these methods — enforced by Python ABC.

Design decisions:
- Metadata-first: get_metadata() always returns schema without touching data
- Sampling is opt-in: sample_data() exists but is called only when schema change detected
- Connection pooling is connector-managed — base class provides the interface
- Secrets never logged: __repr__ redacts credentials
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime
import hashlib
import json


@dataclass
class ColumnMeta:
    """Metadata about a single column — never contains actual data."""
    name: str
    data_type: str
    is_nullable: bool
    is_primary_key: bool = False
    max_length: Optional[int] = None
    tags: List[str] = field(default_factory=list)
    description: Optional[str] = None


@dataclass
class TableMeta:
    """Metadata about a table/collection/object."""
    name: str
    schema: str
    columns: List[ColumnMeta]
    row_count: Optional[int] = None    # Approximate — from stats, not COUNT(*)
    size_bytes: Optional[int] = None
    last_modified: Optional[datetime] = None
    owner: Optional[str] = None
    tags: List[str] = field(default_factory=list)

    def to_schema_hash(self) -> str:
        """Deterministic hash of schema structure (not data)."""
        schema_repr = {
            "name": self.name,
            "columns": [
                {"name": c.name, "type": c.data_type, "nullable": c.is_nullable}
                for c in sorted(self.columns, key=lambda x: x.name)
            ]
        }
        return hashlib.sha256(
            json.dumps(schema_repr, sort_keys=True).encode()
        ).hexdigest()[:16]


@dataclass
class SourceMetadata:
    """Complete metadata snapshot of a data source."""
    source_id: str
    source_type: str
    tables: List[TableMeta]
    captured_at: datetime = field(default_factory=datetime.utcnow)
    database_version: Optional[str] = None

    def to_schema_hash(self) -> str:
        """Hash representing the complete schema state."""
        table_hashes = sorted([t.to_schema_hash() for t in self.tables])
        return hashlib.sha256("|".join(table_hashes).encode()).hexdigest()[:24]

    def to_dict(self) -> dict:
        """Serialize to JSON-compatible dict for storage."""
        return {
            "source_id": self.source_id,
            "source_type": self.source_type,
            "captured_at": self.captured_at.isoformat(),
            "schema_hash": self.to_schema_hash(),
            "table_count": len(self.tables),
            "column_count": sum(len(t.columns) for t in self.tables),
            "database_version": self.database_version,
            "tables": [
                {
                    "name": t.name,
                    "schema": t.schema,
                    "row_count": t.row_count,
                    "size_bytes": t.size_bytes,
                    "last_modified": t.last_modified.isoformat() if t.last_modified else None,
                    "owner": t.owner,
                    "schema_hash": t.to_schema_hash(),
                    "columns": [
                        {
                            "name": c.name,
                            "data_type": c.data_type,
                            "is_nullable": c.is_nullable,
                            "is_primary_key": c.is_primary_key,
                            "max_length": c.max_length,
                            "tags": c.tags,
                            "description": c.description,
                        }
                        for c in t.columns
                    ]
                }
                for t in self.tables
            ]
        }


class BaseConnector(ABC):
    """
    Abstract base for all data source connectors.
    Subclasses implement source-specific logic; base handles retry, logging, pooling interface.
    """

    def __init__(self, source_id: str, config: dict):
        self.source_id = source_id
        self.config = config
        self._connection = None

    # ── Required interface ─────────────────────────────────────────────

    @abstractmethod
    def connect(self) -> bool:
        """Establish connection. Return True on success."""
        ...

    @abstractmethod
    def disconnect(self) -> None:
        """Close and clean up connection."""
        ...

    @abstractmethod
    def test_connection(self) -> tuple:
        """Test connectivity. Returns (success: bool, message: str)."""
        ...

    @abstractmethod
    def get_metadata(self) -> SourceMetadata:
        """
        Return full schema metadata WITHOUT reading actual row data.
        This is the primary method — called on every monitoring cycle.
        """
        ...

    @abstractmethod
    def sample_data(self, table: str, column: str, n: int = 100) -> List[str]:
        """
        Sample n values from a specific column for compliance analysis.
        ONLY called when schema change detected — never on every cycle.
        Values are returned as strings; caller handles compliance scanning.
        """
        ...

    # ── Optional overrides ─────────────────────────────────────────────

    def get_table_stats(self, table: str) -> dict:
        """Get statistical profile: row count, null %, cardinality. Override if cheap."""
        return {}

    def supports_incremental(self) -> bool:
        """Return True if this connector supports CDC or watermark-based incremental."""
        return False

    # ── Context manager ────────────────────────────────────────────────

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
        return False

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(source_id={self.source_id}, type={self.config.get('type')})"
