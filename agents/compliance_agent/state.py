# agents/compliance_agent/state.py
"""LangGraph State for the Compliance Agent."""
from typing import TypedDict, List, Optional, Dict


class ComplianceAgentState(TypedDict):
    """State for the compliance scanning agent."""

    # Input
    source_id: str
    scan_id: str
    metadata: Dict                     # SourceMetadata as dict
    scan_scope: List[str]              # Table names to check (empty = all)

    # After rules engine pass
    column_classifications: List[Dict] # {table, column, classification, risk_level, confidence, recommendation}

    # After AI enhancement
    ai_enhanced: bool
    scan_results: List[Dict]           # Final scan result dicts

    # Summary
    total_tables: int
    total_columns: int
    total_flags: int
    highest_risk: str
    risk_score: float

    # Control
    errors: List[str]
    completed: bool
