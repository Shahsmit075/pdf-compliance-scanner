# pipeline/nodes/encoding_guard.py
"""
Encoding Guard Node — rule-based encoding compliance checker.
Detects: NON_ASCII, MULTILINGUAL, OCR_CORRUPTION, INVALID_UTF8,
         LOW_ENCODING_CONFIDENCE, IMAGE_ONLY_PAGE.
No AI calls — pure deterministic rules.
"""
import re
import unicodedata
from langdetect import detect, LangDetectException
from pipeline.state import PipelineState

# ── OCR corruption indicators ─────────────────────────────────────────────────
# These patterns appear when OCR misreads scanned text
OCR_CORRUPTION_PATTERNS = [
    re.compile(r'[^\x00-\x7F]{3,}\s+[^\x00-\x7F]{3,}'),      # clusters of non-ASCII
    re.compile(r'\b[A-Za-z]+[|\\\/]{2,}[A-Za-z]+\b'),          # slashes/pipes mid-word
    re.compile(r'\b\w{0,2}\s{3,}\w{0,2}\b'),                    # isolated chars with big gaps
    re.compile(r'[lI1]{4,}|[O0]{4,}'),                          # repeated OCR confusion chars
    re.compile(r'(?:[^\w\s.,;:!?\-\'\"()]){4,}'),               # 4+ consecutive garbage chars
    re.compile(r'\uFFFD'),                                        # Unicode replacement char
    re.compile(r'\x00'),                                          # null bytes
]

# ── Script/alphabet detection for multilingual ────────────────────────────────
SCRIPT_RANGES = {
    "Devanagari": (0x0900, 0x097F),       # Hindi, Marathi, Sanskrit
    "Bengali": (0x0980, 0x09FF),
    "Tamil": (0x0B80, 0x0BFF),
    "Telugu": (0x0C00, 0x0C7F),
    "Kannada": (0x0C80, 0x0CFF),
    "Malayalam": (0x0D00, 0x0D7F),
    "Arabic": (0x0600, 0x06FF),
    "Chinese/Japanese/Korean": (0x4E00, 0x9FFF),
    "Cyrillic": (0x0400, 0x04FF),
    "Greek": (0x0370, 0x03FF),
    "Hebrew": (0x0590, 0x05FF),
    "Thai": (0x0E00, 0x0E7F),
}

# Characters allowed without flagging as NON_ASCII (common typographic chars)
ALLOWED_NON_ASCII = set(
    "\u2018\u2019\u201c\u201d"   # smart quotes
    "\u2013\u2014"               # en/em dash
    "\u2026"                     # ellipsis
    "\u20ac\u00a3\u00a5\u20b9"  # currency symbols
    "\u00b0"                     # degree
    "\u00a9\u00ae\u2122"         # copyright/trademark
    "\u00bd\u00bc\u00be"         # fractions
    "\u00e0\u00e1\u00e2\u00e3\u00e4\u00e5\u00e6"  # accented Latin
    "\u00e7\u00e8\u00e9\u00ea\u00eb"
    "\u00ec\u00ed\u00ee\u00ef"
    "\u00f0\u00f1\u00f2\u00f3\u00f4\u00f5\u00f6"
    "\u00f8\u00f9\u00fa\u00fb\u00fc\u00fd\u00fe"
    "\u00c0\u00c1\u00c2\u00c3\u00c4\u00c5\u00c6"
)


def _detect_scripts(text: str) -> list[str]:
    """Identify non-Latin scripts present in the text."""
    found = []
    for script_name, (low, high) in SCRIPT_RANGES.items():
        count = sum(1 for ch in text if low <= ord(ch) <= high)
        if count >= 3:  # at least 3 chars of that script
            found.append(script_name)
    return found


def _detect_ocr_corruption(text: str) -> list[str]:
    """Return list of corruption pattern names found."""
    issues = []
    labels = [
        "Non-ASCII clusters", "Slashes mid-word", "Isolated chars",
        "OCR confusion chars (l/1/0/O)", "Garbage char sequences",
        "Unicode replacement char (U+FFFD)", "Null bytes",
    ]
    for pattern, label in zip(OCR_CORRUPTION_PATTERNS, labels):
        if pattern.search(text):
            issues.append(label)
    return issues


def _non_ascii_count(text: str) -> tuple[int, list[str]]:
    """Return (count, sample_chars) of unexpected non-ASCII characters."""
    chars = [
        ch for ch in text
        if ord(ch) > 127 and ch not in ALLOWED_NON_ASCII
    ]
    samples = list(dict.fromkeys(chars))[:8]  # unique, up to 8
    return len(chars), [repr(c) for c in samples]


def encoding_node(state: PipelineState) -> dict:
    """
    Rule-based encoding compliance checker.
    Checks per page:
      - NON_ASCII: unexpected high-codepoint characters
      - MULTILINGUAL: non-Latin scripts detected (with script name)
      - OCR_CORRUPTION: garbled text patterns from bad scans
      - LOW_ENCODING_CONFIDENCE: chardet confidence below threshold
      - INVALID_UTF8: non-decodable byte sequences (detected via chardet)
      - IMAGE_ONLY_PAGE: no text, only images
    """
    rules = state.get("compliance_rules", {}).get("encoding", {})
    if not rules.get("enabled", True):
        return {"encoding_results": []}

    allowed_languages    = rules.get("allowed_languages", ["en"])
    non_ascii_threshold  = rules.get("non_ascii_threshold", 5)
    min_enc_confidence   = rules.get("min_encoding_confidence", 0.85)
    encoding_results     = []

    for page_data in state["pages_text"]:
        flags = []
        text  = page_data["text"]

        # ── Image-only page ───────────────────────────────────────────────
        if text.strip().startswith("[PAGE") and "Image-only" in text:
            encoding_results.append({
                "page_num": page_data["page_num"],
                "encoding_flags": [{
                    "type": "IMAGE_ONLY_PAGE",
                    "severity": "info",
                    "confidence": 1.0,
                    "note": "No extractable text — OCR required for compliance scan",
                }],
                "encoding_risk": "low",
            })
            continue

        # ── Check 1: NON_ASCII characters ─────────────────────────────────
        count, samples = _non_ascii_count(text)
        if count > non_ascii_threshold:
            flags.append({
                "type": "NON_ASCII_CHARS",
                "count": count,
                "sample_chars": samples,
                "severity": "high" if count > 50 else "medium",
                "confidence": 0.97,
                "note": f"{count} unexpected non-ASCII characters found",
            })

        # ── Check 2: Multilingual / non-Latin scripts ─────────────────────
        detected_scripts = _detect_scripts(text)
        if detected_scripts:
            flags.append({
                "type": "MULTILINGUAL_CONTENT",
                "scripts_detected": detected_scripts,
                "severity": "medium",
                "confidence": 0.93,
                "note": f"Non-Latin scripts detected: {', '.join(detected_scripts)}",
            })

        # ── Check 3: OCR corruption ───────────────────────────────────────
        ocr_issues = _detect_ocr_corruption(text)
        if ocr_issues:
            flags.append({
                "type": "OCR_CORRUPTION",
                "patterns_found": ocr_issues,
                "severity": "high" if len(ocr_issues) >= 2 else "medium",
                "confidence": 0.85,
                "note": f"OCR corruption patterns: {', '.join(ocr_issues[:3])}",
            })

        # ── Check 4: Low encoding confidence ─────────────────────────────
        enc_confidence = page_data.get("encoding_confidence", 1.0)
        enc_detected   = page_data.get("detected_encoding", "utf-8")
        if enc_confidence < min_enc_confidence:
            flags.append({
                "type": "LOW_ENCODING_CONFIDENCE",
                "detected_encoding": enc_detected,
                "confidence_score": round(enc_confidence, 2),
                "severity": "high" if enc_confidence < 0.60 else "medium",
                "confidence": 0.90,
                "note": f"chardet detected '{enc_detected}' with {enc_confidence:.0%} confidence",
            })

        # ── Check 5: INVALID_UTF8 proxy (non-UTF-8 encoding detected) ────
        if enc_detected and enc_detected.lower() not in ("utf-8", "ascii", "utf-8-sig", "utf_8"):
            flags.append({
                "type": "NON_UTF8_ENCODING",
                "detected_encoding": enc_detected,
                "severity": "high",
                "confidence": 0.88,
                "note": f"Expected UTF-8, detected '{enc_detected}'",
            })

        # ── Check 6: Language detection ───────────────────────────────────
        clean_text = re.sub(r'\s+', ' ', text.strip())
        if len(clean_text) > 80:
            try:
                detected_lang = detect(clean_text)
                if detected_lang not in allowed_languages:
                    flags.append({
                        "type": "NON_ALLOWED_LANGUAGE",
                        "detected_lang": detected_lang,
                        "allowed": allowed_languages,
                        "severity": "medium",
                        "confidence": 0.80,
                        "note": f"Language '{detected_lang}' detected; allowed: {allowed_languages}",
                    })
            except LangDetectException:
                pass  # too short or mixed — not a flag

        # ── Compute page encoding risk ────────────────────────────────────
        severities = [f.get("severity", "low") for f in flags]
        if "high" in severities:
            risk = "high"
        elif "medium" in severities:
            risk = "medium"
        elif flags:
            risk = "low"
        else:
            risk = "low"

        encoding_results.append({
            "page_num": page_data["page_num"],
            "encoding_flags": flags,
            "encoding_risk": risk,
        })

    return {"encoding_results": encoding_results}
