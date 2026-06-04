# agents/alert_agent/nodes.py
"""
Alert Agent — dispatches notifications via Slack webhook or email when risk thresholds are breached.
"""
import uuid
import json
import logging
import os
from datetime import datetime

from storage.database import DataSourceDB
from agents.alert_agent.state import AlertAgentState

logger = logging.getLogger(__name__)


def check_thresholds_node(state: AlertAgentState) -> dict:
    """Check if any configured alert thresholds are breached."""
    configs = DataSourceDB.get_alert_configs()
    if not configs:
        return {"should_alert": False, "triggered_configs": []}

    RISK_RANK = {"low": 0, "medium": 1, "high": 2, "critical": 3}
    scan_risk_rank = RISK_RANK.get(state.get("highest_risk", "low"), 0)
    triggered = []

    for cfg in configs:
        trigger_levels = cfg.get("trigger_risk_levels", ["critical", "high"])
        if isinstance(trigger_levels, str):
            trigger_levels = json.loads(trigger_levels)

        for level in trigger_levels:
            if scan_risk_rank >= RISK_RANK.get(level, 99):
                triggered.append(cfg)
                break

    return {
        "should_alert": bool(triggered),
        "triggered_configs": triggered,
    }


def send_alerts_node(state: AlertAgentState) -> dict:
    """Send alerts via all triggered channels."""
    if not state.get("should_alert"):
        return {"alerts_sent": [], "alerts_failed": []}

    sent = []
    failed = []

    source_name = state.get("source_name", state.get("source_id", "Unknown Source"))
    scan_id = state.get("scan_id", "")
    highest_risk = state.get("highest_risk", "low")
    total_flags = state.get("total_flags", 0)
    risk_score = state.get("risk_score", 0.0)

    message = (
        f"🚨 *Compliance Alert — {source_name}*\n"
        f"Risk Level: *{highest_risk.upper()}*\n"
        f"Total Flags: {total_flags}\n"
        f"Risk Score: {risk_score:.1f}/100\n"
        f"Scan ID: `{scan_id}`\n"
        f"Timestamp: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}"
    )

    for cfg in state.get("triggered_configs", []):
        channel = cfg.get("channel", "")
        channel_config = cfg.get("channel_config", {})
        if isinstance(channel_config, str):
            try:
                channel_config = json.loads(channel_config)
            except Exception:
                channel_config = {}

        alert_id = str(uuid.uuid4())[:12]
        ok = False

        if channel == "slack":
            ok = _send_slack(channel_config.get("webhook_url", ""), message)
        elif channel == "email":
            ok = _send_email(
                channel_config.get("recipients", []),
                f"Compliance Alert: {source_name} — {highest_risk.upper()} Risk",
                message,
            )
        elif channel == "webhook":
            ok = _send_webhook(channel_config.get("url", ""), {
                "source_name": source_name,
                "scan_id": scan_id,
                "highest_risk": highest_risk,
                "total_flags": total_flags,
                "risk_score": risk_score,
                "message": message,
            })

        DataSourceDB.log_alert({
            "alert_id":       alert_id,
            "config_id":      cfg.get("config_id"),
            "scan_id":        scan_id,
            "channel":        channel,
            "message_preview": message[:200],
            "status":         "sent" if ok else "failed",
        })

        if ok:
            sent.append({"config_id": cfg.get("config_id"), "channel": channel})
        else:
            failed.append({"config_id": cfg.get("config_id"), "channel": channel})

    return {"alerts_sent": sent, "alerts_failed": failed}


def _send_slack(webhook_url: str, message: str) -> bool:
    """Send a Slack webhook notification."""
    if not webhook_url:
        logger.warning("Slack webhook URL not configured")
        return False
    try:
        import urllib.request
        payload = json.dumps({"text": message}).encode("utf-8")
        req = urllib.request.Request(
            webhook_url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status == 200
    except Exception as e:
        logger.error(f"Slack alert failed: {e}")
        return False


def _send_email(recipients: list, subject: str, body: str) -> bool:
    """Send email alert via SMTP (configured via SMTP_* env vars)."""
    if not recipients:
        logger.warning("No email recipients configured")
        return False
    try:
        import smtplib
        from email.mime.text import MIMEText

        smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        smtp_user = os.getenv("SMTP_USER", "")
        smtp_pass = os.getenv("SMTP_PASS", "")
        from_addr = os.getenv("SMTP_FROM", smtp_user)

        # ── Clear diagnostic if credentials are missing ────────────────────
        missing = []
        if not smtp_user:
            missing.append("SMTP_USER")
        if not smtp_pass:
            missing.append("SMTP_PASS")
        if missing:
            logger.error(
                f"Email alert cannot be sent — missing env vars: {', '.join(missing)}. "
                f"Add them to your .env file. "
                f"For Gmail, use an App Password from https://myaccount.google.com/apppasswords"
            )
            return False

        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = from_addr
        msg["To"] = ", ".join(recipients)

        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(from_addr, recipients, msg.as_string())

        logger.info(f"Email alert sent to: {', '.join(recipients)}")
        return True
    except Exception as e:
        logger.error(f"Email alert failed: {e}")
        return False



def _send_webhook(url: str, payload: dict) -> bool:
    """Send generic webhook POST."""
    if not url:
        return False
    try:
        import urllib.request
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status < 300
    except Exception as e:
        logger.error(f"Webhook alert failed: {e}")
        return False
