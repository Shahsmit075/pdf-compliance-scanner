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


def run_pipeline(pdf_path: str, pdf_name: str, upload_id: str, compliance_rules: dict) -> dict:
    """
    Convenience function to run the full compliance pipeline.
    
    Args:
        pdf_path: Path to uploaded PDF file
        pdf_name: Original filename for display
        upload_id: Unique scan identifier
        compliance_rules: Rules dict from rules.json
    
    Returns:
        Final pipeline state with all results
    """
    pipeline = build_pipeline()

    initial_state = {
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
    }

    return pipeline.invoke(initial_state)
