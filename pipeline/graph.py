# pipeline/graph.py
"""
LangGraph pipeline builder — creates the compliance scanning DAG.
Architecture: ingest → 4 parallel compliance nodes → aggregator → report
"""
from langgraph.graph import StateGraph, END
from pipeline.state import PipelineState
from pipeline.nodes.ingest import ingest_node
from pipeline.nodes.pii_detector import pii_node
from pipeline.nodes.confidentiality import confidentiality_node
from pipeline.nodes.encoding_guard import encoding_node
from pipeline.nodes.abuse_detector import abuse_node
from pipeline.nodes.aggregator import aggregator_node
from pipeline.nodes.report_builder import report_node
from langfuse import observe, get_client, propagate_attributes



def build_pipeline() -> StateGraph:
    """
    Build and compile the LangGraph compliance pipeline.
    
    Graph structure:
        ingest → [pii_check, confidentiality, encoding_check, abuse_check] (parallel)
              → aggregate → build_report → END
    """
    graph = StateGraph(PipelineState)

    # Register all nodes
    graph.add_node("ingest", ingest_node)
    graph.add_node("pii_check", pii_node)
    graph.add_node("confidentiality", confidentiality_node)
    graph.add_node("encoding_check", encoding_node)
    graph.add_node("abuse_check", abuse_node)
    graph.add_node("aggregate", aggregator_node)
    graph.add_node("build_report", report_node)

    # Entry point
    graph.set_entry_point("ingest")

    # After ingestion, run all 4 compliance checks in parallel
    graph.add_edge("ingest", "pii_check")
    graph.add_edge("ingest", "confidentiality")
    graph.add_edge("ingest", "encoding_check")
    graph.add_edge("ingest", "abuse_check")

    # All compliance nodes feed into aggregator
    graph.add_edge("pii_check", "aggregate")
    graph.add_edge("confidentiality", "aggregate")
    graph.add_edge("encoding_check", "aggregate")
    graph.add_edge("abuse_check", "aggregate")

    # After aggregation, build report
    graph.add_conditional_edges(
        "aggregate",
        lambda s: "build_report" if s.get("processing_complete") else "aggregate",
        {"build_report": "build_report", "aggregate": "aggregate"}
    )

    graph.add_edge("build_report", END)

    return graph.compile()


@observe(name="pdf-compliance-scan", capture_input=False, capture_output=False)
def run_pipeline(pdf_path: str, pdf_name: str, upload_id: str, compliance_rules: dict):
    """
    Convenience function to run the full compliance pipeline and yield iterative updates.
    
    Args:
        pdf_path: Path to uploaded PDF file
        pdf_name: Original filename for display
        upload_id: Unique scan identifier
        compliance_rules: Rules dict from rules.json
    
    Yields:
        (node_name, current_state) tuples as each node completes.
    """
    import time
    import os
    pipeline = build_pipeline()

    current_state = {
        "pdf_path": pdf_path,
        "pdf_name": pdf_name,
        "upload_id": upload_id,
        "total_pages": 0,
        "pages_text": [],
        "pii_results": [],
        "confidential_results": [],
        "encoding_results": [],
        "abuse_results": [],
        "page_results": [],
        "summary": {},
        "compliance_rules": compliance_rules,
        "report_path": None,
        "processing_complete": False,
        "errors": [],
        
        # Telemetry & Observability (NEW)
        "start_time": time.time(),
        "total_tokens_used": 0,
        "scan_duration_seconds": 0.0,
        "ai_provider_used": os.getenv("AI_PROVIDER", "groq"),
    }

    # Propagate trace attributes like upload_id and metadata through context
    with propagate_attributes(
        session_id=upload_id,
        metadata={"pdf_name": pdf_name},
        tags=["compliance-scan"]
    ):
        # Stream yields a dict where the key is the node name and value is the state output
        for output in pipeline.stream(current_state):
            for node_name, state_update in output.items():
                # Extract and sum up token counts from nodes
                pii_tokens = state_update.pop("pii_tokens_used", 0)
                conf_tokens = state_update.pop("confidential_tokens_used", 0)
                abuse_tokens = state_update.pop("abuse_tokens_used", 0)
                current_state["total_tokens_used"] += (pii_tokens + conf_tokens + abuse_tokens)
                
                current_state.update(state_update)
                yield node_name, current_state

    # Force flush events to ensure trace is sent immediately
    try:
        get_client().flush()
    except Exception:
        pass

