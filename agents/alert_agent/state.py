# agents/alert_agent/state.py
from typing import TypedDict, List, Optional, Dict


class AlertAgentState(TypedDict):
    source_id: str
    source_name: str
    scan_id: str
    highest_risk: str
    total_flags: int
    risk_score: float
    should_alert: bool
    triggered_configs: List[Dict]
    alerts_sent: List[Dict]
    alerts_failed: List[Dict]
    errors: List[str]
