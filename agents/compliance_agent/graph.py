# agents/compliance_agent/graph.py
"""
Compliance Agent LangGraph DAG.

Flow: classify_columns → ai_enhance → compute_risk → save_results → END
"""
import uuid
from langgraph.graph import StateGraph, END
from agents.compliance_agent.state import ComplianceAgentState
from agents.compliance_agent.nodes import (
    classify_columns_node,
    ai_enhance_node,
    compute_risk_summary_node,
    save_results_node,
)
from storage.database import DataSourceDB
from datetime import datetime


def build_compliance_agent():
    graph = StateGraph(ComplianceAgentState)

    graph.add_node("classify_columns",    classify_columns_node)
    graph.add_node("ai_enhance",          ai_enhance_node)
    graph.add_node("compute_risk",        compute_risk_summary_node)
    graph.add_node("save_results",        save_results_node)

    graph.set_entry_point("classify_columns")
    graph.add_edge("classify_columns", "ai_enhance")
    graph.add_edge("ai_enhance",       "compute_risk")
    graph.add_edge("compute_risk",     "save_results")
    graph.add_edge("save_results",     END)

    return graph.compile()


def run_compliance_agent(source_id: str, metadata: dict, scan_scope: list = None) -> dict:
    """
    Run the compliance agent for a data source.

    Args:
        source_id: Data source ID
        metadata: SourceMetadata dict from metadata agent
        scan_scope: Optional list of table names to restrict scan

    Returns:
        Final state with scan_results, risk_score, highest_risk, etc.
    """
    scan_id = str(uuid.uuid4())[:16]

    # Create scan run record
    DataSourceDB.create_scan_run({
        "scan_id":      scan_id,
        "source_id":    source_id,
        "scan_type":    "manual",
        "initiated_by": "agent",
        "started_at":   datetime.utcnow().isoformat(),
    })

    agent = build_compliance_agent()

    initial_state: ComplianceAgentState = {
        "source_id":              source_id,
        "scan_id":                scan_id,
        "metadata":               metadata,
        "scan_scope":             scan_scope or [],
        "column_classifications": [],
        "ai_enhanced":            False,
        "scan_results":           [],
        "total_tables":           0,
        "total_columns":          0,
        "total_flags":            0,
        "highest_risk":           "low",
        "risk_score":             0.0,
        "errors":                 [],
        "completed":              False,
    }

    return agent.invoke(initial_state)
