# app/utils/redaction.py
"""
PII Redaction Utility — masks detected PII entities in text.
Supports partial masking (show first/last chars) and full masking.
"""
import re

# Mask patterns by PII category
MASKING_RULES = {
    "EMAIL": lambda v: _mask_email(v),
    "PHONE_INDIA": lambda v: _mask_partial(v, keep_last=2),
    "PHONE_US": lambda v: _mask_partial(v, keep_last=4),
    "SSN": lambda v: "***-**-" + v.replace(" ", "").replace("-", "")[-4:] if len(v) >= 4 else "***-**-****",
    "AADHAAR": lambda v: "XXXX XXXX " + v.replace(" ", "").replace("-", "")[-4:] if len(v) >= 4 else "XXXX XXXX XXXX",
    "PAN_CARD": lambda v: v[0] + "XXXX" + v[5:] if len(v) >= 10 else "XXXXX****X",
    "PASSPORT": lambda v: v[0] + "XXXXXX" if len(v) >= 2 else "XXXXXXX",
    "CREDIT_CARD": lambda v: "XXXX-XXXX-XXXX-" + re.sub(r'\D', '', v)[-4:] if len(re.sub(r'\D', '', v)) >= 4 else "XXXX-XXXX-XXXX-XXXX",
    "BANK_ACCOUNT": lambda v: _mask_partial(re.sub(r'\D', '', v), keep_last=4, fill="X"),
    "IP_ADDRESS": lambda v: ".".join(v.split(".")[:2]) + ".XXX.XXX" if "." in v else "X.X.X.X",
    "DATE_OF_BIRTH": lambda v: "XX/XX/" + v.replace("/", "-").replace("-", "/").split("/")[-1] if "/" in v or "-" in v else "XX/XX/XXXX",
    "IBAN": lambda v: v[:4] + "X" * (len(v) - 8) + v[-4:] if len(v) > 8 else "XXXXXXXX",
}

CATEGORY_COLORS = {
    "EMAIL": "#FF6B6B",
    "PHONE_INDIA": "#FF8E53",
    "PHONE_US": "#FF8E53",
    "SSN": "#C0392B",
    "AADHAAR": "#C0392B",
    "PAN_CARD": "#E74C3C",
    "PASSPORT": "#C0392B",
    "CREDIT_CARD": "#8E44AD",
    "BANK_ACCOUNT": "#8E44AD",
    "IP_ADDRESS": "#2980B9",
    "DATE_OF_BIRTH": "#E67E22",
}


def _mask_email(email: str) -> str:
    if "@" not in email:
        return "***@***.***"
    local, domain = email.split("@", 1)
    masked_local = local[0] + "***" if local else "***"
    domain_parts = domain.split(".")
    masked_domain = domain_parts[0][0] + "***" + "." + ".".join(domain_parts[1:]) if domain_parts else "***"
    return f"{masked_local}@{masked_domain}"


def _mask_partial(value: str, keep_last: int = 4, fill: str = "*") -> str:
    digits = re.sub(r'\D', '', value)
    if len(digits) <= keep_last:
        return fill * len(digits)
    return fill * (len(digits) - keep_last) + digits[-keep_last:]


def mask_value(category: str, value: str) -> str:
    """Apply appropriate masking for the given PII category."""
    if not value or value in ("[REDACTED]", "[REDACTED — abuse content]"):
        return "[REDACTED]"
    rule = MASKING_RULES.get(category)
    if rule:
        try:
            return rule(value)
        except Exception:
            pass
    # Generic fallback: keep first 3 chars + asterisks + last 2
    if len(value) > 6:
        return value[:3] + "*" * (len(value) - 5) + value[-2:]
    return "*" * len(value)


def build_redaction_table(page_results: list) -> list[dict]:
    """
    Build a flat list of redaction records for display.
    Returns list of: {page, type, category, original, masked, confidence, severity}
    """
    records = []
    for pr in page_results:
        all_flags = (
            [(f, "PII")          for f in pr.get("pii_flags", [])] +
            [(f, "CONFIDENTIAL") for f in pr.get("confidential_flags", [])] +
            [(f, "ENCODING")     for f in pr.get("encoding_flags", [])] +
            [(f, "ABUSE")        for f in pr.get("abuse_flags", [])]
        )
        for flag, check_type in all_flags:
            category = flag.get("category") or flag.get("type") or "UNKNOWN"
            value    = flag.get("value", "")
            masked   = mask_value(category, value)
            conf     = flag.get("confidence")
            records.append({
                "Page":         pr["page_num"],
                "Type":         check_type,
                "Category":     category,
                "Matched Value": value if value not in ("[REDACTED]", "[REDACTED — abuse content]") else "—",
                "Masked Value": masked,
                "Confidence":   f"{conf:.0%}" if isinstance(conf, (int, float)) else "N/A",
                "Severity":     (flag.get("risk_level") or flag.get("severity") or "medium").upper(),
                "Context":      (flag.get("context") or flag.get("note") or "")[:80],
                "Method":       flag.get("detection_method", "ai").title(),
            })
    return records
