# pipeline/nodes/abuse_detector.py
"""
Abuse Detection Node — three-layer detection:
  Layer 1: Phrase-level regex (high-confidence, exact patterns)
  Layer 2: Contextual keyword matching (broad, catches general threats)
  Layer 3: AI semantic moderation (catches nuanced/implied abuse)
"""
import re
from pathlib import Path
from pipeline.state import PipelineState
from config.ai_provider import call_ai, parse_json_response

PROMPT_FILE = Path(__file__).parent.parent.parent / "config" / "prompts" / "abuse_prompt.txt"
ABUSE_SYSTEM_PROMPT = (
    PROMPT_FILE.read_text() if PROMPT_FILE.exists()
    else "Detect abusive content and return JSON."
)

# ── Layer 1: High-confidence phrase patterns ──────────────────────────────────
PHRASE_PATTERNS = [
    (
        "THREAT",
        re.compile(
            r'\b(?:'
            r'i\s+will\s+kill|kill\s+(?:you|them|him|her|all)|you\s+(?:will|gonna|going\s+to)\s+die'
            r'|bomb\s+(?:threat|attack|you|this)|shoot\s+(?:you|them|him|her)'
            r'|murder\s+(?:you|them)|destroy\s+you|hunt\s+you\s+down'
            r'|watch\s+your\s+back|you(?:\'re|r)\s+(?:dead|finished|done)'
            r'|make\s+you\s+pay|find\s+you\s+and|i\s+know\s+where\s+you'
            r'|you\s+will\s+regret|come\s+after\s+you|end\s+you'
            r')\b',
            re.IGNORECASE,
        ),
        "critical", 0.93,
    ),
    (
        "HATE_SPEECH",
        re.compile(
            r'\b(?:'
            r'hate\s+(?:you\s+people|all\s+\w+s|immigrants|minorities)'
            r'|racial\s+slur|go\s+back\s+to\s+your\s+country'
            r'|inferior\s+(?:race|people|beings?)'
            r'|should\s+be\s+exterminated|not\s+fully\s+human'
            r'|ethnic\s+cleansing|white\s+supremac'
            r'|(?:blacks|jews|muslims|hindus|christians)\s+(?:are\s+(?:all|inferior|evil)|should|must\s+be)'
            r')\b',
            re.IGNORECASE,
        ),
        "critical", 0.91,
    ),
    (
        "HARASSMENT",
        re.compile(
            r'\b(?:'
            r'i\s+know\s+where\s+you\s+(?:live|work|stay)'
            r'|we\s+know\s+your\s+address|stalk(?:ing|ed)\s+(?:you|her|him)'
            r'|following\s+(?:you|her|him)\s+everywhere'
            r'|spread\s+(?:your|her|his)\s+(?:photos?|pictures?|info)'
            r'|expose\s+(?:you|your\s+secrets?|her|him)'
            r'|ruin\s+your\s+(?:life|career|reputation|marriage)'
            r'|make\s+your\s+life\s+(?:hell|miserable|a\s+living\s+nightmare)'
            r')\b',
            re.IGNORECASE,
        ),
        "high", 0.89,
    ),
    (
        "VIOLENCE_INCITEMENT",
        re.compile(
            r'\b(?:'
            r'incite\s+(?:violence|riot|mob\s+rule)|call\s+to\s+(?:arms|violence|action\s+against)'
            r'|attack\s+(?:the|them|those)\s+\w+|rise\s+up\s+and\s+(?:fight|attack|destroy)'
            r'|burn\s+(?:it\s+down|them\s+out|the\s+building)'
            r'|take\s+them\s+down\s+by\s+force|lynch\s+(?:the|them)'
            r'|storm\s+the|violent\s+uprising'
            r')\b',
            re.IGNORECASE,
        ),
        "critical", 0.90,
    ),
    (
        "ILLEGAL_CONTENT",
        re.compile(
            r'\b(?:'
            r'how\s+to\s+(?:make\s+(?:a\s+)?(?:bomb|weapon|poison|meth|fentanyl)'
            r'|synthesize\s+(?:drugs?|narcotics?)|hack\s+into|launder\s+money)'
            r'|drug\s+(?:trafficking|dealing|cartel|smuggling)'
            r'|money\s+laundering|human\s+trafficking'
            r'|illegal\s+(?:weapons?\s+(?:sale|trade)|firearms?\s+(?:sale|trade))'
            r')\b',
            re.IGNORECASE,
        ),
        "critical", 0.94,
    ),
    (
        "SLUR",
        re.compile(
            r'\b(?:'
            r'n[i1\*]{1,2}g(?:g[ae\*]r?|a)?s?'
            r'|f[a4\*]g(?:g[o0]t)?s?'
            r'|k[i1\*]k[e3\*]s?'
            r'|sp[i1\*]cs?'
            r'|w[e3\*]tb[a4\*]cks?'
            r'|ch[i1\*]nks?'
            r'|c[o0][o0]ns?'
            r')\b',
            re.IGNORECASE,
        ),
        "critical", 0.96,
    ),
]

# ── Layer 2: Contextual keyword signals (broader, lower confidence) ────────────
# These are individual trigger words that suggest abuse when found in context.
# Each: (category, word_pattern, risk_level, confidence)
KEYWORD_SIGNALS = [
    # Threat signals
    ("THREAT",    re.compile(r'\b(?:threaten(?:ing|ed)?|blackmail(?:ing)?|extort(?:ing|ion)?|intimidat(?:e|ing|ion))\b', re.I), "high", 0.78),
    ("THREAT",    re.compile(r'\b(?:assault(?:ing)?|attack(?:ing)?\s+(?:you|him|her|them)|harm\s+(?:you|your\s+family))\b', re.I), "high", 0.80),
    ("THREAT",    re.compile(r'\b(?:you\'?ll?\s+(?:pay|suffer|regret)|make\s+(?:you|them)\s+suffer|teach\s+you\s+a\s+lesson)\b', re.I), "high", 0.79),
    # Hate/discrimination signals
    ("HATE_SPEECH", re.compile(r'\b(?:you\s+people\s+are|(?:all|these)\s+\w+\s+are\s+(?:the\s+same|criminals|thieves|lazy))\b', re.I), "high", 0.75),
    ("HATE_SPEECH", re.compile(r'\b(?:discrimination|prejudice|bigotry|racist|sexist|xenophobic)\s+(?:policy|attitude|behavior|act)\b', re.I), "medium", 0.70),
    # Harassment signals
    ("HARASSMENT", re.compile(r'\b(?:harass(?:ing|ment|ed)|bully(?:ing)?|intimidat(?:e|ing)|cyberstalk(?:ing)?)\b', re.I), "high", 0.82),
    ("HARASSMENT", re.compile(r'\b(?:report\s+(?:you|him|her)\s+to\s+(?:your\s+boss|authorities|police)|get\s+you\s+fired|ruin\s+(?:you|your))\b', re.I), "high", 0.77),
    # Violence signals
    ("VIOLENCE_INCITEMENT", re.compile(r'\b(?:violence\s+against|violent\s+(?:act|attack|confrontation)|physical\s+harm)\b', re.I), "high", 0.80),
    ("VIOLENCE_INCITEMENT", re.compile(r'\b(?:fight\s+back|retaliat(?:e|ion|ing)|revenge\s+against)\b', re.I), "medium", 0.72),
    # Sexual harassment
    ("SEXUAL_HARASSMENT", re.compile(r'\b(?:sexual\s+(?:harassment|assault|coercion)|unwanted\s+(?:advances?|touching|contact))\b', re.I), "critical", 0.90),
    ("SEXUAL_HARASSMENT", re.compile(r'\b(?:quid\s+pro\s+quo|sleep\s+with\s+me|date\s+me\s+or|send\s+(?:me\s+)?(?:nudes?|photos?))\b', re.I), "critical", 0.88),
]


def _get_context(text: str, start: int, end: int, window: int = 80) -> str:
    s = max(0, start - window)
    e = min(len(text), end + window)
    snippet = text[s:e].replace("\n", " ").strip()
    return ("…" if s > 0 else "") + snippet + ("…" if e < len(text) else "")


def _run_phrase_detection(text: str) -> list:
    """Layer 1: high-confidence phrase patterns."""
    findings = []
    seen = set()

    for category, pattern, risk_level, confidence in PHRASE_PATTERNS:
        for match in pattern.finditer(text):
            key = (category, match.group().lower()[:30])
            if key in seen:
                continue
            seen.add(key)
            findings.append({
                "category": category,
                "value": "[REDACTED]",
                "context": _get_context(text, match.start(), match.end()),
                "confidence": confidence,
                "risk_level": risk_level,
                "detection_method": "regex",
            })

    return findings


def _run_keyword_detection(text: str) -> list:
    """Layer 2: contextual keyword signals — catches general threat language."""
    findings = []
    seen_contexts = set()

    for category, pattern, risk_level, confidence in KEYWORD_SIGNALS:
        for match in pattern.finditer(text):
            ctx = _get_context(text, match.start(), match.end(), window=40)
            ctx_key = ctx[:50]
            if ctx_key in seen_contexts:
                continue
            seen_contexts.add(ctx_key)
            findings.append({
                "category": category,
                "value": "[REDACTED]",
                "context": ctx,
                "confidence": confidence,
                "risk_level": risk_level,
                "detection_method": "keyword",
            })

    return findings


def _deduplicate(findings: list) -> list:
    """Remove duplicate findings with overlapping context."""
    unique = []
    seen_ctx = set()
    for f in sorted(findings, key=lambda x: -x["confidence"]):  # keep highest confidence
        ctx_key = f.get("context", "")[:40].strip()
        cat_ctx = (f["category"], ctx_key)
        if cat_ctx not in seen_ctx:
            seen_ctx.add(cat_ctx)
            unique.append(f)
    return unique


def _risk_from_flags(findings: list) -> str:
    if not findings:
        return "low"
    rank = {"low": 0, "medium": 1, "high": 2, "critical": 3}
    return max(
        findings, key=lambda f: rank.get(f.get("risk_level", "low"), 0)
    ).get("risk_level", "low")


def abuse_node(state: PipelineState) -> dict:
    """
    Three-layer abuse detection:
      Layer 1: Phrase regex (high confidence, exact)
      Layer 2: Keyword signals (broad, contextual)
      Layer 3: AI semantic moderation (nuanced)
    """
    rules = state.get("compliance_rules", {}).get("abuse", {})
    if not rules.get("enabled", True):
        return {"abuse_results": []}

    zero_tolerance = rules.get("zero_tolerance_categories", ["child_safety", "terrorism"])
    page_results = []

    for page_data in state["pages_text"]:
        text = page_data["text"].strip()

        if not text or text.startswith("[PAGE"):
            page_results.append({
                "page_num": page_data["page_num"],
                "abuse_flags": [],
                "abuse_risk": "low",
            })
            continue

        # Layer 1: Phrase patterns
        phrase_findings = _run_phrase_detection(text)

        # Layer 2: Keyword signals
        keyword_findings = _run_keyword_detection(text)

        # Layer 3: AI moderation (best-effort)
        ai_findings = []
        try:
            raw = call_ai(
                system_prompt=ABUSE_SYSTEM_PROMPT,
                user_message=f"Analyse page {page_data['page_num']}:\n\n{text[:4000]}",
                max_tokens=512,
            )
            result = parse_json_response(raw)
            for finding in result.get("findings", []):
                finding["detection_method"] = "ai"
                if any(zt in finding.get("category", "").lower() for zt in zero_tolerance):
                    finding["risk_level"] = "critical"
            ai_findings = result.get("findings", [])
        except Exception:
            pass

        # Merge all three layers, deduplicate
        combined = phrase_findings + keyword_findings + ai_findings

        # Apply zero-tolerance override
        for f in combined:
            if any(zt in f.get("category", "").lower() for zt in zero_tolerance):
                f["risk_level"] = "critical"

        all_findings = _deduplicate(combined)
        page_risk = _risk_from_flags(all_findings)

        page_results.append({
            "page_num": page_data["page_num"],
            "abuse_flags": all_findings,
            "abuse_risk": page_risk,
        })

    return {"abuse_results": page_results}
