# pipeline/nodes/confidentiality.py
"""
Confidentiality Node — dual-engine: regex-first + AI enhancement.
Regex catches API keys, passwords, AWS creds, GitHub tokens with high confidence.
AI catches semantic confidential data (salary, M&A, trade secrets) on top.
"""
import re
from pathlib import Path
from pipeline.state import PipelineState
from config.ai_provider import call_ai, parse_json_response

PROMPT_FILE = Path(__file__).parent.parent.parent / "config" / "prompts" / "confidential_prompt.txt"
BASE_PROMPT = PROMPT_FILE.read_text() if PROMPT_FILE.exists() else "Detect confidential data and return JSON."

# ── Comprehensive credential regex patterns ───────────────────────────────────
# Each: (category, compiled_regex, risk_level, confidence)
CREDENTIAL_PATTERNS = [
    (
        "API_KEY_OPENAI",
        re.compile(r'\bsk-[a-zA-Z0-9]{32,}\b'),
        "critical", 0.98,
    ),
    (
        "API_KEY_ANTHROPIC",
        re.compile(r'\bsk-ant-[a-zA-Z0-9\-]{32,}\b'),
        "critical", 0.98,
    ),
    (
        "API_KEY_GROQ",
        re.compile(r'\bgsk_[a-zA-Z0-9]{32,}\b'),
        "critical", 0.98,
    ),
    (
        "AWS_ACCESS_KEY",
        re.compile(r'\bAKIA[A-Z0-9]{16}\b'),
        "critical", 0.99,
    ),
    (
        "AWS_SECRET_KEY",
        re.compile(
            r'(?:aws_secret_access_key|AWS_SECRET)[^\n]*?[=:]\s*([a-zA-Z0-9/+]{40})',
            re.IGNORECASE,
        ),
        "critical", 0.97,
    ),
    (
        "GITHUB_TOKEN",
        re.compile(r'\bgh[pousr]_[a-zA-Z0-9]{36}\b'),
        "critical", 0.98,
    ),
    (
        "GOOGLE_API_KEY",
        re.compile(r'\bAIza[a-zA-Z0-9\-_]{35}\b'),
        "critical", 0.97,
    ),
    (
        "STRIPE_KEY",
        re.compile(r'\b(?:sk|pk)_(?:live|test)_[a-zA-Z0-9]{24,}\b'),
        "critical", 0.98,
    ),
    (
        "JWT_TOKEN",
        re.compile(r'\beyJ[a-zA-Z0-9\-_]{20,}\.[a-zA-Z0-9\-_]{20,}\.[a-zA-Z0-9\-_]{20,}\b'),
        "critical", 0.95,
    ),
    (
        "PASSWORD_INLINE",
        re.compile(
            r'(?:password|passwd|pwd|pass)\s*[=:]\s*["\']?([^\s"\'<>]{6,})["\']?',
            re.IGNORECASE,
        ),
        "critical", 0.91,
    ),
    (
        "SECRET_INLINE",
        re.compile(
            r'(?:secret|private_key|client_secret)\s*[=:]\s*["\']?([^\s"\'<>]{6,})["\']?',
            re.IGNORECASE,
        ),
        "high", 0.89,
    ),
    (
        "DB_CONNECTION_STRING",
        re.compile(
            r'(?:mongodb|postgresql|mysql|redis|sqlite)://[^\s<>]{10,}',
            re.IGNORECASE,
        ),
        "critical", 0.95,
    ),
    (
        "PRIVATE_KEY_BLOCK",
        re.compile(r'-----BEGIN\s+(?:RSA\s+)?PRIVATE\s+KEY-----', re.IGNORECASE),
        "critical", 0.99,
    ),
    (
        "SALARY_DATA",
        re.compile(
            r'(?:salary|compensation|ctc|annual\s+pay(?:ment)?)\s*[:\-]?\s*'
            r'(?:USD|INR|GBP|€|\$|£|₹)?\s*[\d,]{4,}',
            re.IGNORECASE,
        ),
        "high", 0.82,
    ),
]


def _get_context(text: str, start: int, end: int, window: int = 60) -> str:
    s = max(0, start - window)
    e = min(len(text), end + window)
    snippet = text[s:e].replace("\n", " ").strip()
    return ("…" if s > 0 else "") + snippet + ("…" if e < len(text) else "")


def _run_regex_detection(text: str, min_confidence: float) -> list:
    findings = []
    seen = set()

    for category, pattern, risk_level, confidence in CREDENTIAL_PATTERNS:
        if confidence < min_confidence:
            continue
        for match in pattern.finditer(text):
            value = match.group().strip()
            # Mask the actual secret value for security
            if len(value) > 12:
                masked = value[:6] + "…" + value[-4:]
            else:
                masked = value[:4] + "…"
            if masked in seen:
                continue
            seen.add(masked)
            findings.append({
                "category": category,
                "value": masked,
                "context": _get_context(text, match.start(), match.end()),
                "confidence": confidence,
                "risk_level": risk_level,
                "detection_method": "regex",
            })

    return findings


def _build_prompt_with_keywords(rules: dict) -> str:
    custom_keywords = rules.get("confidentiality", {}).get("custom_keywords", [])
    if not custom_keywords:
        return BASE_PROMPT
    keywords_section = "\n\nAdditional custom keywords to flag as CUSTOM_KEYWORD:\n"
    keywords_section += "\n".join(f"- {kw}" for kw in custom_keywords if kw.strip())
    return BASE_PROMPT + keywords_section


def _merge_findings(regex_findings: list, ai_findings: list) -> list:
    merged = list(regex_findings)
    regex_cats = {f["category"] for f in regex_findings}
    for ai_f in ai_findings:
        cat = ai_f.get("category", "")
        # Keep AI findings for semantic categories regex can't catch
        semantic_only = {"TRADE_SECRET", "MERGER_ACQUISITION", "FINANCIAL_FORECAST",
                         "CUSTOMER_LIST", "SOURCE_CODE", "INTERNAL_CODENAME", "CUSTOM_KEYWORD"}
        if cat in semantic_only and cat not in regex_cats:
            ai_f["detection_method"] = "ai"
            merged.append(ai_f)
    return merged


def _risk_from_flags(findings: list) -> str:
    if not findings:
        return "low"
    rank = {"low": 0, "medium": 1, "high": 2, "critical": 3}
    return max(findings, key=lambda f: rank.get(f.get("risk_level", "low"), 0)).get(
        "risk_level", "low"
    )


def confidentiality_node(state: PipelineState) -> dict:
    """
    Dual-engine confidentiality detection:
      1. Regex catches API keys, passwords, AWS creds, GitHub tokens (always runs)
      2. AI catches semantic data: trade secrets, M&A, salary, custom keywords (best-effort)
    """
    rules = state.get("compliance_rules", {})
    conf_rules = rules.get("confidentiality", {})

    if not conf_rules.get("enabled", True):
        return {"confidential_results": []}

    system_prompt = _build_prompt_with_keywords(rules)
    min_confidence = conf_rules.get("min_confidence", 0.70)
    page_results = []

    for page_data in state["pages_text"]:
        text = page_data["text"].strip()

        if not text or text.startswith("[PAGE"):
            page_results.append({
                "page_num": page_data["page_num"],
                "confidential_flags": [],
                "confidential_risk": "low",
            })
            continue

        # ── Step 1: Regex credential detection (always runs) ─────────────
        regex_findings = _run_regex_detection(text, min_confidence)

        # ── Step 2: AI semantic detection (best-effort) ───────────────────
        ai_findings = []
        try:
            raw_response = call_ai(
                system_prompt=system_prompt,
                user_message=f"Analyse page {page_data['page_num']}:\n\n{text[:4000]}",
                max_tokens=1024,
            )
            result = parse_json_response(raw_response)
            ai_findings = [
                f for f in result.get("findings", [])
                if f.get("confidence", 0) >= min_confidence
            ]
        except Exception:
            pass

        all_findings = _merge_findings(regex_findings, ai_findings)
        page_risk = _risk_from_flags(all_findings)

        page_results.append({
            "page_num": page_data["page_num"],
            "confidential_flags": all_findings,
            "confidential_risk": page_risk,
        })

    return {"confidential_results": page_results}
