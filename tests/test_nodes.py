# tests/test_nodes.py
import pytest
import json
from unittest.mock import patch, MagicMock

from pipeline.nodes.encoding_guard import encoding_node
from pipeline.nodes.aggregator import aggregator_node


class TestEncodingNode:
    """Tests for the rule-based encoding guard (no AI calls)."""

    def test_clean_english_text_is_low_risk(self, sample_state):
        result = encoding_node(sample_state)
        assert "encoding_results" in result
        assert len(result["encoding_results"]) == 2

    def test_non_ascii_chars_flagged(self, sample_state):
        sample_state["pages_text"][0]["text"] = "Hello " + "こんにちは" * 10 + " world"
        result = encoding_node(sample_state)
        flags = result["encoding_results"][0]["encoding_flags"]
        flag_types = [f["type"] for f in flags]
        assert "NON_ASCII_CHARS" in flag_types

    def test_low_encoding_confidence_flagged(self, sample_state):
        sample_state["pages_text"][0]["encoding_confidence"] = 0.5
        result = encoding_node(sample_state)
        flags = result["encoding_results"][0]["encoding_flags"]
        flag_types = [f["type"] for f in flags]
        assert "LOW_ENCODING_CONFIDENCE" in flag_types

    def test_disabled_encoding_returns_empty(self, sample_state):
        sample_state["compliance_rules"]["encoding"]["enabled"] = False
        result = encoding_node(sample_state)
        assert result["encoding_results"] == []


class TestAggregatorNode:
    """Tests for the aggregator node."""

    def test_aggregator_combines_results_correctly(self, sample_state):
        sample_state["pii_results"] = [
            {"page_num": 1, "pii_flags": [{"type": "EMAIL", "confidence": 0.99, "risk_level": "high"}], "pii_risk": "high"},
            {"page_num": 2, "pii_flags": [], "pii_risk": "low"},
        ]
        sample_state["confidential_results"] = [
            {"page_num": 1, "confidential_flags": [], "confidential_risk": "low"},
            {"page_num": 2, "confidential_flags": [{"type": "API_KEY", "confidence": 0.98, "risk_level": "critical"}], "confidential_risk": "critical"},
        ]
        sample_state["encoding_results"] = [
            {"page_num": 1, "encoding_flags": [], "encoding_risk": "low"},
            {"page_num": 2, "encoding_flags": [], "encoding_risk": "low"},
        ]
        sample_state["abuse_results"] = [
            {"page_num": 1, "abuse_flags": [], "abuse_risk": "low"},
            {"page_num": 2, "abuse_flags": [], "abuse_risk": "low"},
        ]

        result = aggregator_node(sample_state)

        assert "page_results" in result
        assert "summary" in result
        assert result["processing_complete"] is True

        # Page 1 should have high risk (PII)
        page1 = next(p for p in result["page_results"] if p["page_num"] == 1)
        assert page1["overall_risk"] == "high"

        # Page 2 should have critical risk (API key)
        page2 = next(p for p in result["page_results"] if p["page_num"] == 2)
        assert page2["overall_risk"] == "critical"

        # Summary
        assert result["summary"]["total_flags"] == 2
        assert result["summary"]["highest_risk"] == "critical"

    def test_empty_results_give_low_risk(self, sample_state):
        sample_state["pii_results"] = [
            {"page_num": 1, "pii_flags": [], "pii_risk": "low"},
            {"page_num": 2, "pii_flags": [], "pii_risk": "low"},
        ]
        sample_state["confidential_results"] = [
            {"page_num": 1, "confidential_flags": [], "confidential_risk": "low"},
            {"page_num": 2, "confidential_flags": [], "confidential_risk": "low"},
        ]
        sample_state["encoding_results"] = [
            {"page_num": 1, "encoding_flags": [], "encoding_risk": "low"},
            {"page_num": 2, "encoding_flags": [], "encoding_risk": "low"},
        ]
        sample_state["abuse_results"] = [
            {"page_num": 1, "abuse_flags": [], "abuse_risk": "low"},
            {"page_num": 2, "abuse_flags": [], "abuse_risk": "low"},
        ]

        result = aggregator_node(sample_state)
        assert result["summary"]["total_flags"] == 0
        assert result["summary"]["highest_risk"] == "low"


class TestPIINodeWithMockedAI:
    """Tests for PII node using mocked AI calls."""

    def test_pii_node_detects_email_and_phone(self, sample_state, mock_ai_pii_response):
        with patch("pipeline.nodes.pii_detector.call_ai", return_value={"content": mock_ai_pii_response, "tokens": 150}):
            from pipeline.nodes.pii_detector import pii_node
            result = pii_node(sample_state)

        assert "pii_results" in result
        page1_flags = result["pii_results"][0]["pii_flags"]
        categories = [f["category"] for f in page1_flags]
        assert "EMAIL" in categories
        assert "PHONE" in categories or "PHONE_INDIA" in categories

    def test_pii_node_handles_empty_page(self, sample_state, mock_ai_clean_response):
        sample_state["pages_text"][0]["text"] = ""
        with patch("pipeline.nodes.pii_detector.call_ai", return_value={"content": mock_ai_clean_response, "tokens": 0}):
            from pipeline.nodes.pii_detector import pii_node
            result = pii_node(sample_state)

        # Empty page should not call AI
        assert result["pii_results"][0]["pii_flags"] == []

    def test_pii_disabled_returns_empty(self, sample_state):
        sample_state["compliance_rules"]["pii"]["enabled"] = False
        from pipeline.nodes.pii_detector import pii_node
        result = pii_node(sample_state)
        assert result["pii_results"] == []
