# agents/metadata_agent/state.py
"""LangGraph State Schema for the Metadata + Change Detection Agent."""
from typing import TypedDict, List, Optional, Dict, Any


class MetadataAgentState(TypedDict):
    """State flowing through the metadata collection and change detection graph."""

    # Input
    source_id: str
    run_id: str
    triggered_by: str              # 'scheduler'|'manual'|'webhook'

    # After connection
    connection_status: str         # 'connected'|'failed'
    connector_type: str

    # After metadata collection
    current_metadata: Optional[Dict]      # Full SourceMetadata as dict
    current_schema_hash: Optional[str]

    # After comparison
    previous_snapshot_id: Optional[str]
    previous_schema_hash: Optional[str]
    has_changes: bool
    changes: List[Dict]            # Detected change dicts

    # After compliance decision
    should_scan: bool
    scan_scope: List[str]          # Table names to scan

    # Results
    snapshot_id: Optional[str]    # Newly saved snapshot ID
    change_ids: List[str]          # IDs of saved changes

    # Control flow
    errors: List[str]
    completed_at: Optional[str]
