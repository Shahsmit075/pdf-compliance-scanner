# pipeline/nodes/aggregator.py
"""
Aggregator Node — combines results from all 4 compliance nodes into unified page results.
Computes overall risk per page using both per-check severity AND total flag count.
Risk is ALWAYS a known value: low | medium | high | critical — never "unknown".
"""
from pipeline.state import PipelineState

# "unknown" maps to 0 — treated as low, never inflates risk score
RISK_RANK = {"low": 0, "medium": 1, "high": 2, "critical": 3, "unknown": 0}

KNOWN_RISKS = {"low", "medium", "high", "critical"}


def _normalize_risk(risk: str) -> str:
    """Always return a known risk label — unknown/missing → 'low'."""
    return risk if risk in KNOWN_RISKS else "low"


def _highest_risk(*risks: str) -> str:
    """Return the highest known risk level from multiple inputs."""
    return max(
        (_normalize_risk(r) for r in risks),
        key=lambda r: RISK_RANK.get(r, 0),
    )


def _flags_to_risk(total_flags: int) -> str:
    """
    Secondary scoring: derive risk from raw flag count.
    Used to upgrade risk when severity labels under-report.
    """
    if total_flags >= 10:
        return "critical"
    elif total_flags >= 5:
        return "high"
    elif total_flags >= 2:
        return "medium"
    elif total_flags >= 1:
        return "low"
    return "low"


def aggregator_node(state: PipelineState) -> dict:
    """
    Merge all compliance results into unified page results and summary stats.
    Risk is computed as the MAX of:
      - per-check severity-based risk
      - total flag count-based risk (prevents under-reporting)
    """
    pii_results = state.get("pii_results", [])
    conf_results = state.get("confidential_results", [])
    enc_results = state.get("encoding_results", [])
    abuse_results = state.get("abuse_results", [])

    page_results = []
    total_issues = {"pii": 0, "confidential": 0, "encoding": 0, "abuse": 0}
    risk_counts = {"low": 0, "medium": 0, "high": 0, "critical": 0}

    for page_data in state.get("pages_text", []):
        page_num = page_data["page_num"]

        pii_page   = next((r for r in pii_results   if r["page_num"] == page_num), {})
        conf_page  = next((r for r in conf_results  if r["page_num"] == page_num), {})
        enc_page   = next((r for r in enc_results   if r["page_num"] == page_num), {})
        abuse_page = next((r for r in abuse_results if r["page_num"] == page_num), {})

        pii_flags   = pii_page.get("pii_flags", [])
        conf_flags  = conf_page.get("confidential_flags", [])
        enc_flags   = enc_page.get("encoding_flags", [])
        abuse_flags = abuse_page.get("abuse_flags", [])

        total_issues["pii"]          += len(pii_flags)
        total_issues["confidential"] += len(conf_flags)
        total_issues["encoding"]     += len(enc_flags)
        total_issues["abuse"]        += len(abuse_flags)

        page_total_flags = len(pii_flags) + len(conf_flags) + len(enc_flags) + len(abuse_flags)

        # Risk from severity labels
        severity_risk = _highest_risk(
            pii_page.get("pii_risk", "low"),
            conf_page.get("confidential_risk", "low"),
            enc_page.get("encoding_risk", "low"),
            abuse_page.get("abuse_risk", "low"),
        )

        # Risk from flag count (prevents under-scoring)
        count_risk = _flags_to_risk(page_total_flags)

        # Take the higher of the two
        overall_risk = _highest_risk(severity_risk, count_risk)

        # Normalize per-check risk labels too (no UNKNOWN in the report)
        pii_risk   = _normalize_risk(pii_page.get("pii_risk", "low"))
        conf_risk  = _normalize_risk(conf_page.get("confidential_risk", "low"))
        enc_risk   = _normalize_risk(enc_page.get("encoding_risk", "low"))
        abuse_risk = _normalize_risk(abuse_page.get("abuse_risk", "low"))

        risk_counts[overall_risk] = risk_counts.get(overall_risk, 0) + 1

        page_results.append({
            "page_num":           page_num,
            "text_preview":       page_data["text"][:200],
            "char_count":         page_data["char_count"],
            "pii_flags":          pii_flags,
            "confidential_flags": conf_flags,
            "encoding_flags":     enc_flags,
            "abuse_flags":        abuse_flags,
            "pii_risk":           pii_risk,
            "confidential_risk":  conf_risk,
            "encoding_risk":      enc_risk,
            "abuse_risk":         abuse_risk,
            "overall_risk":       overall_risk,
            "total_flags":        page_total_flags,
        })

    total_flags_all = sum(total_issues.values())

    # Document-level risk = max of all page risks AND total flag count risk
    page_risks = [p["overall_risk"] for p in page_results]
    doc_severity_risk = _highest_risk(*page_risks) if page_risks else "low"
    doc_count_risk = _flags_to_risk(total_flags_all)
    highest_risk = _highest_risk(doc_severity_risk, doc_count_risk)

    summary = {
        "total_pages":        state.get("total_pages", 0),
        "total_issues":       total_issues,
        "risk_counts":        risk_counts,
        "total_flags":        total_flags_all,
        "highest_risk":       highest_risk,
        "pages_with_issues":  len([p for p in page_results if p["total_flags"] > 0]),
        "clean_pages":        len([p for p in page_results if p["total_flags"] == 0]),
        "risk_breakdown": {
            "by_severity": risk_counts,
            "by_type": total_issues,
        },
    }

    return {
        "page_results":       page_results,
        "summary":            summary,
        "processing_complete": True,
    }
