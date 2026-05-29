# intelligence/rules_engine.py
"""
Rules Engine — classifies column names and sampled values for PII/PHI/PCI/confidential categories.

Strategy:
  1. Column-name pattern matching (fast, high precision)
  2. Data-type based heuristics (medium confidence)
  3. AI-assisted classification for ambiguous cases (slow, only when names are unclear)

Returns classification + confidence for each column.
"""
import re
from typing import Optional

# ── Column-name regex patterns ─────────────────────────────────────────────────
# Each entry: (classification, [patterns], confidence, risk_level, recommendation)
COLUMN_CLASSIFICATION_RULES = [
    # ── PII ──────────────────────────────────────────────────────────────────
    ("PII_EMAIL",       [r"email", r"e_mail", r"mail_addr"],                    0.96, "high",
     "Encrypt at rest; apply column-level masking in BI tools."),

    ("PII_PHONE",       [r"phone", r"mobile", r"cell", r"tel\b", r"telephone"], 0.93, "high",
     "Apply tokenization; restrict SELECT to authorized roles."),

    ("PII_NAME",        [r"\bfirst.?name\b", r"\blast.?name\b", r"\bfull.?name\b",
                         r"\bfname\b", r"\blname\b",
                         r"\bcust.?name\b", r"\bcustomer.?name\b",
                         r"\bperson.?name\b", r"\bcontact.?name\b",
                         r"\bemployee.?name\b", r"\bstaff.?name\b",
                         r"\bdisplay.?name\b", r"\buser.?name\b"],              0.85, "medium",
     "Mask in non-production environments; audit SELECT logs."),

    ("PII_ADDRESS",     [r"\baddress\b", r"\bstreet\b", r"\bzip.?code\b", r"\bpostal.?code\b",
                         r"\bcity\b", r"\bstate\b", r"\bcountry\b", r"\bprovince\b"],
                                                                                0.88, "medium",
     "Restrict to need-to-know; anonymize in analytics exports."),


    ("PII_DOB",         [r"\bdob\b", r"date.?of.?birth", r"birth.?date",
                         r"birthdate"],                                          0.95, "high",
     "Encrypt; purge after retention period; limit to HR/legal."),

    ("PII_SSN",         [r"\bssn\b", r"social.?sec", r"national.?id",
                         r"aadhaar", r"aadhar", r"sin\b"],                      0.98, "critical",
     "CRITICAL: Encrypt with AES-256; strict RBAC; audit all access."),

    ("PII_PASSPORT",    [r"passport"],                                          0.97, "critical",
     "CRITICAL: Encrypt; restrict; include in breach notification scope."),

    ("PII_IP",          [r"\bip.?addr", r"ip_address"],                        0.90, "medium",
     "Anonymize for analytics; log retention policy applies."),

    ("PII_GENDER",      [r"\bgender\b", r"\bsex\b"],                           0.80, "medium",
     "Sensitive attribute — restrict access; anonymize in exports."),

    ("PII_RACE",        [r"\brace\b", r"ethnicity"],                           0.82, "high",
     "Sensitive category — encrypt; restrict; GDPR Article 9 applies."),

    # ── PCI DSS ───────────────────────────────────────────────────────────────
    ("PCI_CARD_NUMBER", [r"card.?num", r"cc.?num", r"pan\b", r"credit.?card",
                         r"debit.?card"],                                        0.99, "critical",
     "CRITICAL: Must be masked (PAN) per PCI DSS 3.x; never store CVV."),

    ("PCI_CVV",         [r"\bcvv\b", r"\bcvc\b", r"\bcv2\b"],                  0.99, "critical",
     "CRITICAL: PCI DSS prohibits storing CVV after authorization."),

    ("PCI_EXPIRY",      [r"card.?exp", r"expiry", r"expiration"],              0.90, "high",
     "Restrict alongside PAN; apply PCI DSS controls."),

    # ── PHI (HIPAA) ───────────────────────────────────────────────────────────
    ("PHI_DIAGNOSIS",   [r"diagnos", r"icd.?code", r"condition", r"disease",
                         r"disorder"],                                           0.88, "critical",
     "CRITICAL: HIPAA PHI — encrypt; strict minimum-necessary access."),

    ("PHI_MEDICATION",  [r"medication", r"prescription", r"drug", r"dosage",
                         r"rx\b"],                                               0.87, "critical",
     "CRITICAL: HIPAA PHI — encrypt; audit all access."),

    ("PHI_LAB_RESULT",  [r"lab.?result", r"test.?result", r"glucose",
                         r"cholesterol", r"bmi\b"],                             0.85, "critical",
     "CRITICAL: HIPAA PHI — de-identify per Safe Harbor or Expert Determination."),

    ("PHI_MRN",         [r"\bmrn\b", r"medical.?rec", r"patient.?id",
                         r"member.?id"],                                         0.94, "critical",
     "CRITICAL: HIPAA PHI — treat as SSN-equivalent."),

    # ── Confidential / Financial ───────────────────────────────────────────────
    ("CONFIDENTIAL_SALARY",   [r"salary", r"compensation", r"wage", r"pay\b",
                                r"bonus", r"commission"],                        0.92, "high",
     "HR-sensitive; restrict to payroll/HR roles; encrypt exports."),

    ("CONFIDENTIAL_FINANCIAL",[r"revenue", r"profit", r"margin", r"forecast",
                                r"budget", r"financial"],                       0.82, "high",
     "Restrict to finance roles; watermark reports."),

    ("CONFIDENTIAL_PASSWORD", [r"password", r"passwd", r"pwd", r"\bhash\b",
                                r"secret\b"],                                   0.99, "critical",
     "CRITICAL: Must be salted + hashed (bcrypt/Argon2); never plaintext."),

    ("CONFIDENTIAL_API_KEY",  [r"api.?key", r"api.?secret", r"access.?token",
                                r"auth.?token", r"bearer"],                     0.99, "critical",
     "CRITICAL: Rotate immediately; use secret manager; never in DB."),

    ("CONFIDENTIAL_CREDENTIALS", [r"credential", r"private.?key", r"secret.?key",
                                   r"signing.?key"],                            0.97, "critical",
     "CRITICAL: Should never be in a database column; use secret manager."),

    # ── Internal ──────────────────────────────────────────────────────────────
    ("INTERNAL_EMPLOYEE_ID",  [r"emp.?id", r"employee.?id", r"staff.?id",
                                r"worker.?id"],                                 0.90, "medium",
     "Internal PII — restrict to HR; anonymize in analytics."),

    ("INTERNAL_USER_ID",      [r"\buser.?id\b", r"account.?id", r"member.?num"],
                                                                                0.70, "low",
     "Pseudonymize for cross-system correlation control."),
]


def classify_column(column_name: str, data_type: str = "",
                    sample_values: list = None) -> dict:
    """
    Classify a column by name pattern matching + optional sample value analysis.

    Returns:
        {
            "classification": "PII_EMAIL" | "PCI_CARD_NUMBER" | ... | "unclassified",
            "confidence": 0.0 - 1.0,
            "risk_level": "low" | "medium" | "high" | "critical",
            "recommendation": str,
            "match_method": "name_pattern" | "data_type" | "unclassified",
        }
    """
    col_lower = column_name.lower()

    for classification, patterns, confidence, risk_level, recommendation in COLUMN_CLASSIFICATION_RULES:
        for pattern in patterns:
            if re.search(pattern, col_lower, re.IGNORECASE):
                return {
                    "classification": classification,
                    "confidence": confidence,
                    "risk_level": risk_level,
                    "recommendation": recommendation,
                    "match_method": "name_pattern",
                }

    # Fallback: data type heuristics
    dt_lower = (data_type or "").lower()
    if sample_values:
        # Quick value-based hints
        sample_str = " ".join(str(v) for v in sample_values[:10])
        if re.search(r'\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b', sample_str):
            return {
                "classification": "PII_EMAIL",
                "confidence": 0.80,
                "risk_level": "high",
                "recommendation": "Encrypt at rest; apply column-level masking in BI tools.",
                "match_method": "value_pattern",
            }
        if re.search(r'\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b', sample_str):
            return {
                "classification": "PCI_CARD_NUMBER",
                "confidence": 0.85,
                "risk_level": "critical",
                "recommendation": "CRITICAL: Must be masked per PCI DSS.",
                "match_method": "value_pattern",
            }

    return {
        "classification": "unclassified",
        "confidence": 0.0,
        "risk_level": "low",
        "recommendation": "No sensitive patterns detected.",
        "match_method": "unclassified",
    }


def classify_table(table_name: str, columns: list) -> dict:
    """
    Classify a table based on its columns.
    Returns overall risk + per-column classifications.
    """
    RISK_RANK = {"low": 0, "medium": 1, "high": 2, "critical": 3}
    col_classifications = []
    highest_risk = "low"
    pii_count = 0
    sensitive_count = 0

    for col in columns:
        result = classify_column(
            col.get("name") or col.name if hasattr(col, "name") else str(col),
            col.get("data_type") or (col.data_type if hasattr(col, "data_type") else ""),
        )
        col_classifications.append({
            "column": col.get("name") if isinstance(col, dict) else col.name,
            **result,
        })
        if result["classification"] != "unclassified":
            sensitive_count += 1
        if result["classification"].startswith("PII"):
            pii_count += 1
        if RISK_RANK.get(result["risk_level"], 0) > RISK_RANK.get(highest_risk, 0):
            highest_risk = result["risk_level"]

    return {
        "table": table_name,
        "highest_risk": highest_risk,
        "pii_columns": pii_count,
        "sensitive_columns": sensitive_count,
        "total_columns": len(columns),
        "compliance_score": round(
            (1 - sensitive_count / max(len(columns), 1)) * 100, 1
        ),
        "columns": col_classifications,
    }
