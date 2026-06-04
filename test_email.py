"""
Demo alert email — uses actual ARPIT_TESTING Snowflake scan data from the UI.
Sends a beautifully formatted compliance alert to religiousbhandhu@gmail.com
"""
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

SMTP_HOST  = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT  = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER  = os.getenv("SMTP_USER", "")
SMTP_PASS  = os.getenv("SMTP_PASS", "")
SMTP_FROM  = os.getenv("SMTP_FROM", SMTP_USER)
RECIPIENT  = "religiousbhandhu@gmail.com"

# ── Actual scan data from ARPIT_TESTING Snowflake scan ──────────────────────
SCAN_DATA = {
    "source_name":  "ARPIT_TESTING",
    "source_type":  "Snowflake ❄️",
    "scan_id":      "56b399e4-4c2a-4f89-bc1d-9a3e7d12f0b8",
    "risk_level":   "HIGH",
    "risk_score":   "20.0 / 100",
    "tables":       8,
    "columns":      61,
    "flags":        2,
    "schema_changes": 0,
    "timestamp":    datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
    "flagged_columns": [
        {
            "column":     "CUSTOMER.C_PHONE",
            "type":       "PII",
            "category":   "PII_PHONE",
            "risk":       "HIGH",
            "confidence": "93%",
            "recommendation": "Apply tokenization; restrict SELECT to authorized roles."
        },
        {
            "column":     "SUPPLIER.S_PHONE",
            "type":       "PII",
            "category":   "PII_PHONE",
            "risk":       "HIGH",
            "confidence": "93%",
            "recommendation": "Apply tokenization; restrict SELECT to authorized roles."
        },
    ]
}

# ── Plain text version ───────────────────────────────────────────────────────
plain = f"""
🚨 COMPLIANCE ALERT — {SCAN_DATA['source_name']} ({SCAN_DATA['source_type']})
============================================================

Risk Level   : {SCAN_DATA['risk_level']}
Risk Score   : {SCAN_DATA['risk_score']}
Scan ID      : {SCAN_DATA['scan_id']}
Timestamp    : {SCAN_DATA['timestamp']}

SCAN SUMMARY
------------
Tables Scanned   : {SCAN_DATA['tables']}
Columns Scanned  : {SCAN_DATA['columns']}
Compliance Flags : {SCAN_DATA['flags']}
Schema Changes   : {SCAN_DATA['schema_changes']}

FLAGGED COLUMNS
---------------
"""
for col in SCAN_DATA["flagged_columns"]:
    plain += f"""
  Column       : {col['column']}
  Type         : {col['type']} ({col['category']})
  Risk         : {col['risk']} — Confidence: {col['confidence']}
  Action       : {col['recommendation']}
  ---
"""
plain += """
ACTION REQUIRED: Review and remediate flagged columns immediately.

--
PDF Compliance Scanner · Gen AI Capstone — Team 1
Powered by Groq Llama 3 · LangGraph · Langfuse
"""

# ── HTML version ─────────────────────────────────────────────────────────────
flagged_rows_html = ""
for col in SCAN_DATA["flagged_columns"]:
    flagged_rows_html += f"""
    <tr>
      <td style="padding:10px 14px;font-family:monospace;font-size:13px;color:#f0ede6;
                 border-bottom:1px solid #2a2a2a">{col['column']}</td>
      <td style="padding:10px 14px;font-family:monospace;font-size:13px;color:#e8c838;
                 border-bottom:1px solid #2a2a2a">{col['type']}</td>
      <td style="padding:10px 14px;font-family:monospace;font-size:13px;color:#e8a838;
                 border-bottom:1px solid #2a2a2a">{col['category']}</td>
      <td style="padding:10px 14px;font-family:monospace;font-size:13px;color:#ff8c42;
                 font-weight:700;border-bottom:1px solid #2a2a2a">{col['risk']}</td>
      <td style="padding:10px 14px;font-family:monospace;font-size:13px;color:#4fd180;
                 border-bottom:1px solid #2a2a2a">{col['confidence']}</td>
      <td style="padding:10px 14px;font-family:'DM Sans',sans-serif;font-size:12px;
                 color:#7a7a7a;border-bottom:1px solid #2a2a2a">{col['recommendation']}</td>
    </tr>
    """

html = f"""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#0a0a0a;font-family:'Segoe UI',Arial,sans-serif">
  <div style="max-width:680px;margin:32px auto;background:#111111;border:1px solid #2a2a2a;border-radius:8px;overflow:hidden">

    <!-- Header -->
    <div style="background:linear-gradient(135deg,#1a0a00 0%,#0d0d0d 100%);
                border-bottom:2px solid #e8a838;padding:28px 32px">
      <div style="font-family:'Courier New',monospace;font-size:11px;color:#e8a838;
                  letter-spacing:0.25em;text-transform:uppercase;margin-bottom:10px">
        ⚠ COMPLIANCE ALERT · PDF COMPLIANCE SCANNER
      </div>
      <div style="font-family:'Courier New',monospace;font-size:26px;font-weight:700;
                  color:#ff8c42;letter-spacing:0.05em">
        🚨 {SCAN_DATA['risk_level']} RISK DETECTED
      </div>
      <div style="font-family:'Courier New',monospace;font-size:16px;color:#f0ede6;
                  margin-top:6px">
        ❄️ Snowflake · <strong style="color:#e8a838">{SCAN_DATA['source_name']}</strong>
      </div>
    </div>

    <!-- Timestamp + Scan ID -->
    <div style="background:#0d0d0d;padding:12px 32px;border-bottom:1px solid #2a2a2a;
                display:flex;justify-content:space-between">
      <span style="font-family:monospace;font-size:12px;color:#5a5a5a">
        🕐 {SCAN_DATA['timestamp']}
      </span>
      <span style="font-family:monospace;font-size:12px;color:#5a5a5a">
        ID: {SCAN_DATA['scan_id']}
      </span>
    </div>

    <!-- Stats Grid -->
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:1px;
                background:#2a2a2a;border-bottom:1px solid #2a2a2a;margin:24px 32px 0">
      <div style="background:#141414;padding:16px;text-align:center">
        <div style="font-family:monospace;font-size:10px;color:#5a5a5a;
                    letter-spacing:0.15em;margin-bottom:6px">TABLES</div>
        <div style="font-family:monospace;font-size:28px;font-weight:700;
                    color:#7dd3fc">{SCAN_DATA['tables']}</div>
      </div>
      <div style="background:#141414;padding:16px;text-align:center">
        <div style="font-family:monospace;font-size:10px;color:#5a5a5a;
                    letter-spacing:0.15em;margin-bottom:6px">COLUMNS</div>
        <div style="font-family:monospace;font-size:28px;font-weight:700;
                    color:#e8a838">{SCAN_DATA['columns']}</div>
      </div>
      <div style="background:#141414;padding:16px;text-align:center">
        <div style="font-family:monospace;font-size:10px;color:#5a5a5a;
                    letter-spacing:0.15em;margin-bottom:6px">FLAGS</div>
        <div style="font-family:monospace;font-size:28px;font-weight:700;
                    color:#f87171">{SCAN_DATA['flags']}</div>
      </div>
      <div style="background:#141414;padding:16px;text-align:center">
        <div style="font-family:monospace;font-size:10px;color:#5a5a5a;
                    letter-spacing:0.15em;margin-bottom:6px">RISK SCORE</div>
        <div style="font-family:monospace;font-size:28px;font-weight:700;
                    color:#ff8c42">{SCAN_DATA['risk_score']}</div>
      </div>
    </div>

    <!-- Flagged Columns -->
    <div style="padding:24px 32px">
      <div style="font-family:monospace;font-size:11px;color:#e8a838;
                  letter-spacing:0.2em;margin-bottom:14px">FLAGGED COLUMNS</div>
      <table style="width:100%;border-collapse:collapse;background:#0d0d0d;
                    border:1px solid #2a2a2a;border-radius:4px;overflow:hidden">
        <thead>
          <tr style="background:#1a1a1a">
            <th style="padding:10px 14px;text-align:left;font-family:monospace;
                       font-size:11px;color:#5a5a5a;letter-spacing:0.12em;
                       border-bottom:1px solid #2a2a2a">COLUMN</th>
            <th style="padding:10px 14px;text-align:left;font-family:monospace;
                       font-size:11px;color:#5a5a5a;letter-spacing:0.12em;
                       border-bottom:1px solid #2a2a2a">TYPE</th>
            <th style="padding:10px 14px;text-align:left;font-family:monospace;
                       font-size:11px;color:#5a5a5a;letter-spacing:0.12em;
                       border-bottom:1px solid #2a2a2a">CATEGORY</th>
            <th style="padding:10px 14px;text-align:left;font-family:monospace;
                       font-size:11px;color:#5a5a5a;letter-spacing:0.12em;
                       border-bottom:1px solid #2a2a2a">RISK</th>
            <th style="padding:10px 14px;text-align:left;font-family:monospace;
                       font-size:11px;color:#5a5a5a;letter-spacing:0.12em;
                       border-bottom:1px solid #2a2a2a">CONF.</th>
            <th style="padding:10px 14px;text-align:left;font-family:monospace;
                       font-size:11px;color:#5a5a5a;letter-spacing:0.12em;
                       border-bottom:1px solid #2a2a2a">RECOMMENDATION</th>
          </tr>
        </thead>
        <tbody>{flagged_rows_html}</tbody>
      </table>
    </div>

    <!-- Action Required Banner -->
    <div style="margin:0 32px 24px;background:rgba(255,69,69,0.08);
                border-left:3px solid #f87171;border-radius:0 4px 4px 0;padding:14px 18px">
      <div style="font-family:monospace;font-size:12px;color:#f87171;
                  letter-spacing:0.12em;margin-bottom:4px">⚠ ACTION REQUIRED</div>
      <div style="font-family:'Segoe UI',Arial,sans-serif;font-size:14px;color:#9a9a9a">
        Phone number columns detected without encryption or access controls.
        Apply tokenization and restrict SELECT permissions to authorized roles immediately.
      </div>
    </div>

    <!-- Footer -->
    <div style="background:#0a0a0a;border-top:1px solid #2a2a2a;padding:18px 32px;
                display:flex;justify-content:space-between;align-items:center">
      <div style="font-family:monospace;font-size:11px;color:#3a3a3a">
        PDF COMPLIANCE SCANNER · GEN AI CAPSTONE — TEAM 1
      </div>
      <div style="font-family:monospace;font-size:11px;color:#3a3a3a">
        Groq Llama 3 · LangGraph · Langfuse
      </div>
    </div>

  </div>
</body>
</html>
"""

# ── Send ─────────────────────────────────────────────────────────────────────
print("=" * 55)
print("📧 SENDING DEMO SNOWFLAKE COMPLIANCE ALERT EMAIL")
print("=" * 55)
print(f"  From : {SMTP_FROM}")
print(f"  To   : {RECIPIENT}")
print(f"  Subj : 🚨 Compliance Alert — ARPIT_TESTING (HIGH Risk)")
print("=" * 55)

msg = MIMEMultipart("alternative")
msg["Subject"] = f"🚨 Compliance Alert — {SCAN_DATA['source_name']} Snowflake — HIGH Risk Detected"
msg["From"]    = SMTP_FROM
msg["To"]      = RECIPIENT
msg.attach(MIMEText(plain, "plain"))
msg.attach(MIMEText(html, "html"))

try:
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(SMTP_USER, SMTP_PASS)
        server.sendmail(SMTP_FROM, [RECIPIENT], msg.as_string())
    print(f"\n✅ SUCCESS — Demo alert email sent to {RECIPIENT}")
    print("   Check inbox at religiousbhandhu@gmail.com now!")
except Exception as e:
    print(f"\n❌ FAILED: {e}")
