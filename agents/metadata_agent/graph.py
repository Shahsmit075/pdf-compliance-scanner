# agents/metadata_agent/graph.py
"""
Metadata Agent LangGraph DAG.

Flow:
  connect_source
    ↓
  collect_metadata
    ↓
  compare_snapshots
    ↓
  [has_changes?] ──No──→ log_no_change → END
       ↓ Yes
  classify_changes
    ↓
  save_snapshot → END
"""
from langgraph.graph import StateGraph, END
from agents.metadata_agent.state import MetadataAgentState
from agents.metadata_agent.nodes import (
    connect_source_node,
    collect_metadata_node,
    compare_snapshots_node,
    classify_changes_node,
    save_snapshot_node,
    log_no_change_node,
)


def _route_after_comparison(state: MetadataAgentState) -> str:
    if state.get("connection_status") != "connected":
        return "end_error"
    if not state.get("current_metadata"):
        return "end_error"
    return "classify_changes" if state.get("has_changes") else "log_no_change"


def build_metadata_agent():
    """Build and compile the metadata agent graph."""
    graph = StateGraph(MetadataAgentState)

    graph.add_node("connect_source",     connect_source_node)
    graph.add_node("collect_metadata",   collect_metadata_node)
    graph.add_node("compare_snapshots",  compare_snapshots_node)
    graph.add_node("classify_changes",   classify_changes_node)
    graph.add_node("save_snapshot",      save_snapshot_node)
    graph.add_node("log_no_change",      log_no_change_node)

    graph.set_entry_point("connect_source")

    graph.add_edge("connect_source",    "collect_metadata")
    graph.add_edge("collect_metadata",  "compare_snapshots")

    graph.add_conditional_edges(
        "compare_snapshots",
        _route_after_comparison,
        {
            "classify_changes": "classify_changes",
            "log_no_change":    "log_no_change",
            "end_error":        END,
        }
    )

    graph.add_edge("classify_changes",  "save_snapshot")
    graph.add_edge("save_snapshot",     END)
    graph.add_edge("log_no_change",     END)

    return graph.compile()


def run_metadata_agent(source_id: str, triggered_by: str = "manual") -> dict:
    """
    Convenience function to run the metadata agent for a given source.

    Returns the final state dict including has_changes, changes, snapshot_id.
    """
    import uuid
    agent = build_metadata_agent()

    initial_state = {
        "source_id":            source_id,
        "run_id":               str(uuid.uuid4())[:12],
        "triggered_by":         triggered_by,
        "connection_status":    "",
        "connector_type":       "",
        "current_metadata":     None,
        "current_schema_hash":  None,
        "previous_snapshot_id": None,
        "previous_schema_hash": None,
        "has_changes":          False,
        "changes":              [],
        "should_scan":          False,
        "scan_scope":           [],
        "snapshot_id":          None,
        "change_ids":           [],
        "errors":               [],
        "completed_at":         None,
    }

    return agent.invoke(initial_state)
