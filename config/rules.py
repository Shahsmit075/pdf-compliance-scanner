# config/rules.py
"""
Load and save compliance rules from config/rules.json.
"""
import json
import os
from pathlib import Path

RULES_FILE = Path(__file__).parent / "rules.json"


def load_rules() -> dict:
    """Load compliance rules from JSON file."""
    if not RULES_FILE.exists():
        return get_default_rules()
    with open(RULES_FILE, "r") as f:
        return json.load(f)


def save_rules(rules: dict) -> None:
    """Save updated compliance rules to JSON file."""
    with open(RULES_FILE, "w") as f:
        json.dump(rules, f, indent=2)


def get_default_rules() -> dict:
    """Return default compliance rules if no file exists."""
    return {
        "version": "1.0",
        "sensitivity": "high",
        "pii": {
            "enabled": True,
            "detect_email": True,
            "detect_phone": True,
            "detect_ssn_aadhaar": True,
            "detect_credit_card": True,
            "detect_address": True,
            "detect_dob": True,
            "min_confidence": 0.75,
            "risk_threshold": "medium"
        },
        "confidentiality": {
            "enabled": True,
            "detect_api_keys": True,
            "detect_passwords": True,
            "detect_trade_secrets": True,
            "detect_financial_data": True,
            "detect_merger_acquisition": True,
            "custom_keywords": [
                "PROJECT TITAN", "Operation Phoenix",
                "internal use only", "confidential"
            ],
            "min_confidence": 0.70
        },
        "encoding": {
            "enabled": True,
            "require_utf8": True,
            "allowed_languages": ["en"],
            "min_encoding_confidence": 0.85,
            "flag_non_ascii": True,
            "non_ascii_threshold": 5
        },
        "abuse": {
            "enabled": True,
            "detect_hate_speech": True,
            "detect_sexual_content": True,
            "detect_violence_incitement": True,
            "detect_illegal_content": True,
            "detect_harassment": True,
            "sensitivity_level": "high",
            "zero_tolerance_categories": ["child_safety", "terrorism"]
        },
        "reporting": {
            "include_text_context": True,
            "context_window_chars": 150,
            "generate_pdf_report": True,
            "generate_json_report": True
        }
    }
