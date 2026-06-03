# pipeline/nodes/ingest.py
"""
PDF ingestion node — extracts text from every page using PyMuPDF.
Handles text PDFs, detects image-only pages, captures encoding metadata.
"""
import fitz  # PyMuPDF
import chardet
from pipeline.state import PipelineState
from langfuse import observe


@observe(capture_input=False, capture_output=False)
def ingest_node(state: PipelineState) -> dict:
    """
    Extract text page-by-page from uploaded PDF.
    
    Returns:
        Partial state update with 'total_pages' and 'pages_text'.
    """
    pages_text = []
    errors = list(state.get("errors", []))

    try:
        doc = fitz.open(state["pdf_path"])

        for page_num in range(len(doc)):
            page = doc[page_num]

            # Primary extraction: direct text (fast, accurate for text PDFs)
            text = page.get_text(
                "text",
                flags=fitz.TEXT_PRESERVE_WHITESPACE | fitz.TEXT_MEDIABOX_CLIP
            )

            # Fallback: image-only page detection
            if not text.strip() and len(page.get_images()) > 0:
                text = (
                    f"[PAGE {page_num+1}: Image-only page detected. "
                    f"Contains {len(page.get_images())} image(s). "
                    f"OCR required for full compliance scan.]"
                )

            # Detect encoding metadata for the encoding compliance node
            if text.strip():
                raw_bytes = text.encode("utf-8", errors="replace")
                detected = chardet.detect(raw_bytes)
            else:
                detected = {"encoding": "unknown", "confidence": 0}

            pages_text.append({
                "page_num": page_num + 1,
                "text": text,
                "char_count": len(text),
                "detected_encoding": detected.get("encoding", "unknown"),
                "encoding_confidence": detected.get("confidence", 0.0),
                "image_count": len(page.get_images()),
            })

        doc.close()
        total = len(pages_text)

    except Exception as e:
        errors.append(f"PDF ingestion error: {str(e)}")
        total = 0

    return {
        "total_pages": total,
        "pages_text": pages_text,
        "errors": errors,
    }
