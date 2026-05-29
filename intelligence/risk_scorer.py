# intelligence/risk_scorer.py
"""
Risk Scorer — computes numeric risk scores from scan results for trend analysis.

Score formula (0–100):
  - Base score from violation count
  - Multiplier by severity distribution (critical > high > medium > low)
  - Compliance percentage = 100 - (flagged_columns / total_columns * 100)
"""
from datetime import datetime

SEVERITY_WEIGHTS = {
    "critical": 25.0,
    "high":     10.0,
    "medium":    3.0,
    "low":       1.0,
}


def compute_risk_score(scan_results: list, total_columns: int = 0) -> dict:
    """
    Compute risk score and compliance percentage from a list of scan results.

    Args:
        scan_results: List of ds_scan_results dicts with 'risk_level', 'check_type'
        total_columns: Total columns scanned (for compliance % calculation)

    Returns:
        {
            "risk_score": float (0-100),
            "compliance_pct": float (0-100),
            "highest_risk": str,
            "pii_count": int,
            "confidential_count": int,
            "abuse_count": int,
            "custom_count": int,
            "total_violations": int,
        }
    """
    if not scan_results:
        return {
            "risk_score": 0.0,
            "compliance_pct": 100.0,
            "highest_risk": "low",
            "pii_count": 0,
            "confidential_count": 0,
            "abuse_count": 0,
            "custom_count": 0,
            "total_violations": 0,
        }

    RISK_RANK = {"low": 0, "medium": 1, "high": 2, "critical": 3}

    raw_score = 0.0
    highest = "low"
    counts = {"pii": 0, "confidential": 0, "abuse": 0, "custom": 0}
    risk_levels = []

    for result in scan_results:
        rl = (result.get("risk_level") or "low").lower()
        ct = (result.get("check_type") or "custom").lower()

        raw_score += SEVERITY_WEIGHTS.get(rl, 1.0)
        risk_levels.append(rl)

        if RISK_RANK.get(rl, 0) > RISK_RANK.get(highest, 0):
            highest = rl

        if ct in counts:
            counts[ct] += 1
        else:
            counts["custom"] += 1

    # Normalize to 0-100
    risk_score = min(100.0, round(raw_score, 1))

    # Compliance percentage
    flagged_entities = len({r.get("entity_name") for r in scan_results})
    if total_columns > 0:
        compliance_pct = round(max(0.0, (1 - flagged_entities / total_columns) * 100), 1)
    else:
        compliance_pct = 100.0 if not scan_results else max(0.0, 100.0 - risk_score)

    return {
        "risk_score": risk_score,
        "compliance_pct": compliance_pct,
        "highest_risk": highest,
        "pii_count": counts["pii"],
        "confidential_count": counts["confidential"],
        "abuse_count": counts["abuse"],
        "custom_count": counts["custom"],
        "total_violations": len(scan_results),
    }


def build_trend_entry(source_id: str, risk_metrics: dict) -> dict:
    """Build a risk_trends row from computed risk metrics."""
    return {
        "source_id":          source_id,
        "trend_date":         datetime.utcnow().strftime("%Y-%m-%d"),
        "risk_score":         risk_metrics.get("risk_score", 0.0),
        "pii_count":          risk_metrics.get("pii_count", 0),
        "confidential_count": risk_metrics.get("confidential_count", 0),
        "abuse_count":        risk_metrics.get("abuse_count", 0),
        "custom_count":       risk_metrics.get("custom_count", 0),
        "total_violations":   risk_metrics.get("total_violations", 0),
        "compliance_pct":     risk_metrics.get("compliance_pct", 100.0),
    }
