# app/components/uploader.py
"""
Reusable PDF uploader component.
"""
import streamlit as st


def render_uploader(max_size_mb: int = 50) -> object:
    """Render a styled file uploader and return the uploaded file object."""
    return st.file_uploader(
        "Choose a PDF file",
        type=["pdf"],
        help=f"Maximum {max_size_mb}MB. Scans for PII, confidential data, encoding issues, and abusive content."
    )
