# agents/compliance_agent/nodes.py
"""
Compliance Agent Nodes.

Flow:
  classify_columns (rules engine — always runs)
    ↓
  ai_enhance (AI classification for ambiguous columns — best effort)
    ↓
  compute_risk_summary
    ↓
  save_results
"""
import uuid
import logging
from datetime import datetime
from typing import List

from intelligence.rules_engine import classify_column
from intelligence.risk_scorer import compute_risk_score
from storage.database import DataSourceDB
from agents.compliance_agent.state import ComplianceAgentState

logger = logging.getLogger(__name__)

RISK_RANK = {"low": 0, "medium": 1, "high": 2, "critical": 3}


def classify_columns_node(state: ComplianceAgentState) -> dict:
    """
    Run the rules engine against all columns in the metadata.
    This always runs — no AI dependency.
    """
    metadata = state.get("metadata", {})
    scan_scope = set(state.get("scan_scope", []))
    tables = metadata.get("tables", [])

    if scan_scope:
        tables = [t for t in tables if t["name"] in scan_scope]

    classifications = []
    total_tables = len(tables)
    total_columns = 0

    for table in tables:
        table_name = table["name"]
        for col in table.get("columns", []):
            col_name = col["name"]
            data_type = col.get("data_type", "")
            total_columns += 1

            result = classify_column(col_name, data_type)
            if result["classification"] != "unclassified":
                classifications.append({
                    "table":          table_name,
                    "column":         col_name,
                    "entity_name":    f"{table_name}.{col_name}",
                    "classification": result["classification"],
                    "risk_level":     result["risk_level"],
                    "confidence":     result["confidence"],
                    "recommendation": result["recommendation"],
                    "match_method":   result["match_method"],
                    "data_type":      data_type,
                })

    return {
        "column_classifications": classifications,
        "total_tables": total_tables,
        "total_columns": total_columns,
    }


def ai_enhance_node(state: ComplianceAgentState) -> dict:
    """
    Use AI to classify columns that the rules engine marked as 'unclassified'
    but may still be sensitive. Best-effort — failures are non-fatal.
    """
    try:
        from config.ai_provider import call_ai, parse_json_response

        metadata = state.get("metadata", {})
        tables = metadata.get("tables", [])
        classified_entities = {c["entity_name"] for c in state.get("column_classifications", [])}

        # Build a summary of unclassified columns for the AI
        unclassified = []
        for table in tables[:10]:  # Limit tables sent to AI
            for col in table.get("columns", []):
                entity = f"{table['name']}.{col['name']}"
                if entity not in classified_entities:
                    unclassified.append({
                        "table": table["name"],
                        "column": col["name"],
                        "data_type": col.get("data_type", "unknown"),
                    })

        if not unclassified:
            return {"ai_enhanced": False}

        # Only send ambiguous columns to AI
        col_list = "\n".join(
            f"- {c['table']}.{c['column']} (type: {c['data_type']})"
            for c in unclassified[:30]
        )

        system_prompt = """You are a data compliance expert. Analyze the following database columns and identify any that may contain sensitive data (PII, PCI, PHI, credentials, financial data).

Respond with JSON in this exact format:
{
  "findings": [
    {
      "entity_name": "table.column",
      "classification": "PII_EMAIL|PCI_CARD_NUMBER|PHI_DIAGNOSIS|CONFIDENTIAL_SALARY|...",
      "risk_level": "low|medium|high|critical",
      "confidence": 0.0-1.0,
      "recommendation": "brief recommendation"
    }
  ]
}

Only include columns that are potentially sensitive. Skip clearly non-sensitive columns."""

        response = call_ai(
            system_prompt=system_prompt,
            user_message=f"Analyze these columns:\n{col_list}",
            max_tokens=1024,
        )
        parsed = parse_json_response(response)
        ai_findings = parsed.get("findings", [])

        # Merge AI findings with existing classifications
        existing = list(state.get("column_classifications", []))
        existing_entities = {c["entity_name"] for c in existing}

        for finding in ai_findings:
            entity = finding.get("entity_name", "")
            if entity and entity not in existing_entities and finding.get("confidence", 0) >= 0.70:
                # Find table/column from entity_name
                parts = entity.split(".")
                table_name = parts[0] if len(parts) >= 2 else entity
                col_name = ".".join(parts[1:]) if len(parts) >= 2 else entity

                existing.append({
                    "table":          table_name,
                    "column":         col_name,
                    "entity_name":    entity,
                    "classification": finding.get("classification", "AI_FLAGGED"),
                    "risk_level":     finding.get("risk_level", "medium"),
                    "confidence":     finding.get("confidence", 0.70),
                    "recommendation": finding.get("recommendation", "Review this column."),
                    "match_method":   "ai",
                    "data_type":      "",
                })
                existing_entities.add(entity)

        return {"column_classifications": existing, "ai_enhanced": True}

    except Exception as e:
        logger.warning(f"AI enhancement failed (non-fatal): {e}")
        return {"ai_enhanced": False}


def compute_risk_summary_node(state: ComplianceAgentState) -> dict:
    """Compute document-level risk summary from all column classifications."""
    classifications = state.get("column_classifications", [])
    total_columns = state.get("total_columns", 0)

    # Convert classifications to scan_results format for risk scorer
    pseudo_results = [
        {
            "risk_level": c["risk_level"],
            "check_type": _classify_to_check_type(c["classification"]),
            "entity_name": c["entity_name"],
        }
        for c in classifications
    ]

    metrics = compute_risk_score(pseudo_results, total_columns)

    return {
        "total_flags": len(classifications),
        "highest_risk": metrics["highest_risk"],
        "risk_score": metrics["risk_score"],
    }


def save_results_node(state: ComplianceAgentState) -> dict:
    """Persist scan results to the database."""
    scan_id = state["scan_id"]
    source_id = state["source_id"]
    classifications = state.get("column_classifications", [])

    results = []
    for c in classifications:
        results.append({
            "result_id":      str(uuid.uuid4())[:16],
            "scan_id":        scan_id,
            "source_id":      source_id,
            "entity_type":    "column",
            "entity_name":    c["entity_name"],
            "check_type":     _classify_to_check_type(c["classification"]),
            "flag_category":  c["classification"],
            "confidence":     c["confidence"],
            "risk_level":     c["risk_level"],
            "evidence":       f"Column name: {c['column']} | Type: {c.get('data_type', '')} | Method: {c.get('match_method', '')}",
            "recommendation": c["recommendation"],
            "created_at":     datetime.utcnow().isoformat(),
        })

    DataSourceDB.save_scan_results(results)

    # Update scan run
    DataSourceDB.complete_scan_run(scan_id, {
        "status":        "completed",
        "total_tables":  state.get("total_tables", 0),
        "total_columns": state.get("total_columns", 0),
        "total_flags":   state.get("total_flags", 0),
        "risk_score":    state.get("risk_score", 0.0),
        "highest_risk":  state.get("highest_risk", "low"),
        "result_data":   {
            "classifications": classifications,
            "summary": {
                "total_tables":  state.get("total_tables", 0),
                "total_columns": state.get("total_columns", 0),
                "total_flags":   state.get("total_flags", 0),
                "highest_risk":  state.get("highest_risk", "low"),
                "risk_score":    state.get("risk_score", 0.0),
            }
        },
    })

    return {"scan_results": results, "completed": True}


def _classify_to_check_type(classification: str) -> str:
    """Map classification label to check_type category."""
    if not classification:
        return "custom"
    upper = classification.upper()
    if upper.startswith("PII") or upper.startswith("PHI"):
        return "pii"
    if upper.startswith("PCI") or upper.startswith("CONFIDENTIAL"):
        return "confidential"
    return "custom"
