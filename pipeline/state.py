# pipeline/state.py
"""
LangGraph State Schema — typed state object that flows through every pipeline node.
"""
from typing import TypedDict, List, Optional, Dict, Any


class Flag(TypedDict):
    """A single compliance violation flag."""
    type: str           # e.g., "EMAIL", "API_KEY", "HATE_SPEECH"
    value: str          # The actual flagged content (truncated for privacy)
    context: str        # Surrounding text for context (50-150 chars)
    confidence: float   # 0.0 to 1.0
    risk_level: str     # "low" | "medium" | "high" | "critical"
    position: Optional[str]  # Page location hint


class PageResult(TypedDict):
    """Compliance results for a single PDF page."""
    page_num: int
    text_preview: str       # First 200 chars of extracted text
    char_count: int
    pii_flags: List[Flag]
    confidential_flags: List[Flag]
    encoding_flags: List[Flag]
    abuse_flags: List[Flag]
    pii_risk: str
    confidential_risk: str
    encoding_risk: str
    abuse_risk: str
    overall_risk: str       # "low" | "medium" | "high" | "critical"


class PageText(TypedDict):
    """Raw extracted text data for a single page."""
    page_num: int
    text: str
    char_count: int
    detected_encoding: str
    encoding_confidence: float
    image_count: int


class PipelineState(TypedDict):
    """
    Complete pipeline state — passed through every LangGraph node.
    Nodes return partial dicts that update specific keys only.
    """
    # Input
    pdf_path: str
    pdf_name: str
    upload_id: str

    # After ingestion
    total_pages: int
    pages_text: List[PageText]

    # After compliance checks
    pii_results: List[Dict]
    confidential_results: List[Dict]
    encoding_results: List[Dict]
    abuse_results: List[Dict]

    # After aggregation
    page_results: List[PageResult]
    summary: Dict[str, Any]

    # Config
    compliance_rules: Dict[str, Any]

    # Output
    report_path: Optional[str]
    processing_complete: bool
    errors: List[str]
