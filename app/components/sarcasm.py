# app/components/sarcasm.py
"""
Witty, sarcastic loading messages and toast notifications for the compliance scan.
Dry, corporate-noir, self-aware humor.
"""
import random


SCAN_STAGE_MESSAGES = {
    "extracting": [
        "Extracting text... fingers crossed your PDF isn't just a scanned image of a fax.",
        "Reading your document. It's not judging you. Yet.",
        "Text extraction in progress. Please pretend to look busy.",
        "Pulling text from PDF... this is the easy part. The shame comes later.",
    ],
    "pii_scanning": [
        "Scanning for PII... we can already tell this is going to be awkward.",
        "Looking for personal data you definitely meant to remove. Definitely.",
        "PII detection active. Spoiler: there's always at least one email address.",
        "Checking for exposed identities. No judgment. Lots of flags.",
    ],
    "confidential_scanning": [
        "Scanning for credentials... who puts API keys in a PDF? You'd be surprised.",
        "Checking for secret data. If you hid it in Comic Sans, we'll still find it.",
        "Looking for things your security team would cry about. Professionally.",
        "Confidentiality check running. The auditors send their regards.",
    ],
    "encoding_check": [
        "Validating encoding... UTF-8 is a human right. Allegedly.",
        "Checking for encoding issues. OCR corruption is just the document expressing itself.",
        "Language detection active. We support multilingual documents. We just don't expect them.",
        "Encoding guard running. Your document's character set is being interrogated.",
    ],
    "abuse_detection": [
        "Running abuse detection... this is the part where it gets uncomfortable.",
        "Checking for threatening language. Three-layer detection, because once wasn't enough.",
        "Abuse scan in progress. The AI has seen things. It's fine. Probably.",
        "Moderation check active. Zero-tolerance policy, infinite sarcasm policy.",
    ],
    "aggregating": [
        "Aggregating results... tallying up the compliance debt.",
        "Merging findings... compiling your document's greatest hits.",
        "Building the full picture. It's not always pretty. That's the job.",
        "Risk scoring in progress. Numbers don't lie. Humans do, though.",
    ],
    "building_report": [
        "Generating your compliance report... preparing the receipt for your decisions.",
        "Building PDF report... the irony of a compliance PDF about a PDF is not lost on us.",
        "Report generation active. Making your violations look professional since 2024.",
        "Compiling findings into a beautiful, downloadable proof of your document's crimes.",
    ],
    "complete": [
        "Scan complete. Your document has been thoroughly interrogated.",
        "All checks done. The results have been delivered. We take no responsibility for the feelings they cause.",
        "Done. Your compliance status is now a matter of record. You're welcome.",
        "Finished. Whatever happens next is between you and your legal team.",
    ],
}


CLEAN_QUIPS = [
    "Either your document is perfectly compliant, or the violations are extraordinarily well-hidden. Optimistically, we'll assume the former.",
    "No issues found. This is either excellent compliance hygiene or an exceptionally boring document. Both are valid.",
    "Document is clean. We checked twice. We were almost disappointed.",
    "Zero violations. You've achieved what most documents cannot. Treasure this moment.",
    "Nothing flagged. Statistically unusual. Refreshingly so.",
]


RISK_QUIPS = {
    "low": "Low risk. You're doing better than 60% of documents we've seen. The bar is underground.",
    "medium": "Medium risk. The compliance team won't panic. They'll just sigh heavily.",
    "high": "High risk. This document has opinions. Loud, legally questionable opinions.",
    "critical": "Critical risk. We'd say 'don't panic' but the audit trail suggests otherwise.",
}


def get_stage_message(stage: str) -> str:
    """Returns a random sarcastic message for the given scan stage."""
    messages = SCAN_STAGE_MESSAGES.get(stage)
    if messages:
        return random.choice(messages)
    return "Processing... please stand by."


def get_empty_state_quip() -> str:
    """Returns a random quip for when a document has no violations."""
    return random.choice(CLEAN_QUIPS)


def get_risk_quip(risk_level: str) -> str:
    """Returns a dry comment about the given risk level."""
    return RISK_QUIPS.get(
        risk_level.lower(),
        "Risk level: unknown. This is either very good or very bad.",
    )
