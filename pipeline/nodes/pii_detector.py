# pipeline/nodes/pii_detector.py
"""
PII Detection Node — dual-engine: regex-first (always runs) + AI enhancement.
Regex catches obvious PII instantly; AI catches nuanced/contextual PII on top.
"""
import re
from pathlib import Path
from pipeline.state import PipelineState
from config.ai_provider import call_ai, parse_json_response

# Load system prompt
PROMPT_FILE = Path(__file__).parent.parent.parent / "config" / "prompts" / "pii_prompt.txt"
PII_SYSTEM_PROMPT = PROMPT_FILE.read_text() if PROMPT_FILE.exists() else "Detect PII and return JSON."

# ── Comprehensive regex patterns ─────────────────────────────────────────────
# Each entry: (category, compiled_regex, risk_level, confidence)
REGEX_PATTERNS = [
    (
        "EMAIL",
        re.compile(r'\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b'),
        "high", 0.97,
    ),
    (
        "PHONE_INDIA",
        re.compile(r'(?<!\d)(?:\+91[\s\-]?)?[6-9]\d{9}(?!\d)'),
        "high", 0.92,
    ),
    (
        "PHONE_US",
        re.compile(r'(?<!\d)(?:\+?1[\s\-]?)?\(?\d{3}\)?[\s\-\.]\d{3}[\s\-\.]\d{4}(?!\d)'),
        "high", 0.88,
    ),
    (
        "SSN",
        re.compile(r'\b\d{3}[-\s]\d{2}[-\s]\d{4}\b'),
        "critical", 0.95,
    ),
    (
        "AADHAAR",
        re.compile(r'\b\d{4}[\s\-]\d{4}[\s\-]\d{4}\b'),
        "critical", 0.95,
    ),
    (
        "PAN_CARD",
        re.compile(r'\b[A-Z]{5}[0-9]{4}[A-Z]\b'),
        "high", 0.95,
    ),
    (
        "PASSPORT",
        re.compile(r'\b[A-Z][0-9]{7}\b|\b[A-Z]{2}[0-9]{6,7}\b'),
        "critical", 0.82,
    ),
    (
        "CREDIT_CARD",
        re.compile(
            r'\b(?:4\d{3}|5[1-5]\d{2}|6011|3[47]\d{2})[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b'
        ),
        "critical", 0.93,
    ),
    (
        "BANK_ACCOUNT",
        re.compile(
            r'(?:account\s*(?:no\.?|number|#)?\s*[:\-]?\s*)([\d\s]{9,18})',
            re.IGNORECASE,
        ),
        "high", 0.80,
    ),
    (
        "IBAN",
        re.compile(r'\b[A-Z]{2}\d{2}[A-Z0-9]{4}\d{7}(?:[A-Z0-9]{0,16})\b'),
        "high", 0.92,
    ),
    (
        "IP_ADDRESS",
        re.compile(
            r'\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}'
            r'(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b'
        ),
        "medium", 0.90,
    ),
    (
        "DATE_OF_BIRTH",
        re.compile(
            r'(?:DOB|[Dd]ate\s+of\s+[Bb]irth|[Bb]orn)[:\s]+(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})',
            re.IGNORECASE,
        ),
        "high", 0.88,
    ),
]


def _get_context(text: str, match_start: int, match_end: int, window: int = 60) -> str:
    """Return surrounding text as context snippet."""
    start = max(0, match_start - window)
    end = min(len(text), match_end + window)
    snippet = text[start:end].replace("\n", " ").strip()
    if start > 0:
        snippet = "…" + snippet
    if end < len(text):
        snippet = snippet + "…"
    return snippet


def _run_regex_detection(text: str, min_confidence: float) -> list:
    """
    Run all regex patterns against the text.
    Returns a list of finding dicts compatible with the AI response schema.
    """
    findings = []
    seen_values = set()  # deduplicate by matched value

    for category, pattern, risk_level, confidence in REGEX_PATTERNS:
        if confidence < min_confidence:
            continue
        for match in pattern.finditer(text):
            value = match.group().strip()
            if not value or value in seen_values:
                continue
            seen_values.add(value)
            findings.append({
                "category": category,
                "value": value[:80],  # truncate long values
                "context": _get_context(text, match.start(), match.end()),
                "confidence": confidence,
                "risk_level": risk_level,
                "detection_method": "regex",
            })

    return findings


def _merge_findings(regex_findings: list, ai_findings: list) -> list:
    """
    Merge regex and AI findings, deduplicating by value substring matching.
    AI findings that duplicate a regex finding are dropped; novel AI findings kept.
    """
    merged = list(regex_findings)
    regex_values = {f["value"].lower() for f in regex_findings}

    for ai_f in ai_findings:
        ai_val = ai_f.get("value", "").lower().strip()
        # Check if AI finding substantially overlaps with an existing regex finding
        is_duplicate = any(
            ai_val in rv or rv in ai_val
            for rv in regex_values
            if rv
        )
        if not is_duplicate and ai_val:
            ai_f["detection_method"] = "ai"
            merged.append(ai_f)
            regex_values.add(ai_val)

    return merged


def _risk_from_flags(findings: list) -> str:
    """Derive page risk from the findings list."""
    if not findings:
        return "low"
    risk_rank = {"low": 0, "medium": 1, "high": 2, "critical": 3}
    highest = max(
        findings,
        key=lambda f: risk_rank.get(f.get("risk_level", "low"), 0)
    )
    return highest.get("risk_level", "low")


def pii_node(state: PipelineState) -> dict:
    """
    Dual-engine PII detection:
      1. Regex engine runs on EVERY non-empty page (guaranteed detections)
      2. AI engine enhances with contextual/nuanced findings (best-effort)
      3. Results are merged and deduplicated
    """
    rules = state.get("compliance_rules", {}).get("pii", {})
    if not rules.get("enabled", True):
        return {"pii_results": []}

    min_confidence = rules.get("min_confidence", 0.75)
    page_results = []

    for page_data in state["pages_text"]:
        text = page_data["text"].strip()

        if not text or text.startswith("[PAGE"):
            page_results.append({
                "page_num": page_data["page_num"],
                "pii_flags": [],
                "pii_risk": "low",
            })
            continue

        # ── Step 1: Regex detection (always runs, never fails) ────────────
        regex_findings = _run_regex_detection(text, min_confidence)

        # ── Step 2: AI enhancement (best-effort) ─────────────────────────
        ai_findings = []
        text_for_ai = text[:4000]
        try:
            raw_response = call_ai(
                system_prompt=PII_SYSTEM_PROMPT,
                user_message=f"Analyse page {page_data['page_num']}:\n\n{text_for_ai}",
                max_tokens=1024,
            )
            result = parse_json_response(raw_response)
            ai_findings = [
                f for f in result.get("findings", [])
                if f.get("confidence", 0) >= min_confidence
            ]
        except Exception:
            pass  # AI failure is non-fatal — regex results still saved

        # ── Step 3: Merge ─────────────────────────────────────────────────
        all_findings = _merge_findings(regex_findings, ai_findings)
        page_risk = _risk_from_flags(all_findings)

        page_results.append({
            "page_num": page_data["page_num"],
            "pii_flags": all_findings,
            "pii_risk": page_risk,
        })

    return {"pii_results": page_results}
