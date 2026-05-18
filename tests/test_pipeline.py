# tests/test_pipeline.py
"""
Integration tests for the full pipeline.
"""
import pytest
from unittest.mock import patch, MagicMock


class TestPipelineIntegration:
    """Integration tests for the LangGraph pipeline."""

    def test_run_pipeline_returns_correct_keys(self, sample_state):
        """Verify the pipeline returns the expected state keys."""
        import json

        clean_ai_response = json.dumps({
            "has_pii": False, "findings": [], "page_risk": "low",
            "recommendation": "No action required"
        })

        with patch("pipeline.nodes.pii_detector.call_ai", return_value=clean_ai_response), \
             patch("pipeline.nodes.confidentiality.call_ai", return_value=json.dumps({
                 "has_confidential": False, "findings": [], "page_risk": "low",
                 "recommendation": "No action required"
             })), \
             patch("pipeline.nodes.abuse_detector.call_ai", return_value=json.dumps({
                 "has_abuse": False, "findings": [], "page_risk": "low",
                 "recommendation": "No action required"
             })):
            from pipeline.nodes.aggregator import aggregator_node
            from pipeline.nodes.encoding_guard import encoding_node

            # Simulate a minimal pipeline run
            pii_state = {"pii_results": [
                {"page_num": 1, "pii_flags": [], "pii_risk": "low"},
                {"page_num": 2, "pii_flags": [], "pii_risk": "low"},
            ]}
            sample_state.update(pii_state)
            sample_state["confidential_results"] = [
                {"page_num": 1, "confidential_flags": [], "confidential_risk": "low"},
                {"page_num": 2, "confidential_flags": [], "confidential_risk": "low"},
            ]
            enc_result = encoding_node(sample_state)
            sample_state.update(enc_result)
            sample_state["abuse_results"] = [
                {"page_num": 1, "abuse_flags": [], "abuse_risk": "low"},
                {"page_num": 2, "abuse_flags": [], "abuse_risk": "low"},
            ]

            agg_result = aggregator_node(sample_state)

            assert "page_results" in agg_result
            assert "summary" in agg_result
            assert agg_result["processing_complete"] is True
