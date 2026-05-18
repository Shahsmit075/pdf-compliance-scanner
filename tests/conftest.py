# tests/conftest.py
import pytest
import json
from unittest.mock import MagicMock, patch


@pytest.fixture
def sample_state():
    return {
        "pdf_path": "/tmp/test.pdf",
        "pdf_name": "test.pdf",
        "upload_id": "test123",
        "total_pages": 2,
        "pages_text": [
            {
                "page_num": 1,
                "text": "Contact John Smith at john.smith@company.com or call +91-9876543210. Aadhaar: 1234 5678 9012",
                "char_count": 100,
                "detected_encoding": "utf-8",
                "encoding_confidence": 0.99,
                "image_count": 0,
            },
            {
                "page_num": 2,
                "text": "API Key: sk-prod-abc123def456xyz789. Password: SuperSecret@123",
                "char_count": 70,
                "detected_encoding": "utf-8",
                "encoding_confidence": 0.99,
                "image_count": 0,
            },
        ],
        "pii_results": [],
        "confidential_results": [],
        "encoding_results": [],
        "abuse_results": [],
        "page_results": [],
        "summary": {},
        "compliance_rules": {
            "pii": {"enabled": True, "min_confidence": 0.75},
            "confidentiality": {"enabled": True, "min_confidence": 0.70, "custom_keywords": []},
            "encoding": {"enabled": True, "allowed_languages": ["en"], "non_ascii_threshold": 5,
                        "min_encoding_confidence": 0.85, "flag_non_ascii": True},
            "abuse": {"enabled": True, "zero_tolerance_categories": ["child_safety", "terrorism"]},
        },
        "report_path": None,
        "processing_complete": False,
        "errors": [],
    }


@pytest.fixture
def mock_ai_pii_response():
    return json.dumps({
        "has_pii": True,
        "findings": [
            {
                "category": "EMAIL",
                "value": "john.smith@company.com",
                "context": "Contact John Smith at john.smith@company.com or call",
                "confidence": 0.99,
                "risk_level": "high"
            },
            {
                "category": "PHONE",
                "value": "+91-9876543210",
                "context": "john.smith@company.com or call +91-9876543210. Aadhaar",
                "confidence": 0.97,
                "risk_level": "high"
            }
        ],
        "page_risk": "high",
        "recommendation": "Redact all PII before sharing"
    })


@pytest.fixture
def mock_ai_clean_response():
    return json.dumps({
        "has_pii": False,
        "findings": [],
        "page_risk": "low",
        "recommendation": "No action required"
    })
