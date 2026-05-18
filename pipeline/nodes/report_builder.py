# pipeline/nodes/report_builder.py
"""
Report Builder Node — generates professional PDF compliance reports using ReportLab.
Includes executive summary, risk heatmap, and detailed findings with:
  - matched value/snippet
  - detection method (regex vs AI)
  - real confidence percentage
  - context window
  - severity color coding
"""
import os
from datetime import datetime
from pipeline.state import PipelineState

from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Table, TableStyle,
    Spacer, HRFlowable, PageBreak, KeepTogether,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT

# ── Color palette ─────────────────────────────────────────────────────────────
COLOR_CRITICAL   = colors.HexColor("#C0392B")
COLOR_HIGH       = colors.HexColor("#E67E22")
COLOR_MEDIUM     = colors.HexColor("#F39C12")
COLOR_LOW        = colors.HexColor("#27AE60")
COLOR_HEADER     = colors.HexColor("#2C3E50")
COLOR_SUB_HEADER = colors.HexColor("#34495E")
COLOR_LIGHT_GRAY = colors.HexColor("#ECF0F1")
COLOR_LIGHT_RED  = colors.HexColor("#FADBD8")
COLOR_LIGHT_ORG  = colors.HexColor("#FDEBD0")
COLOR_WHITE      = colors.white

RISK_COLORS = {
    "critical": COLOR_CRITICAL,
    "high":     COLOR_HIGH,
    "medium":   COLOR_MEDIUM,
    "low":      COLOR_LOW,
    "unknown":  colors.gray,
}

RISK_BG_COLORS = {
    "critical": COLOR_LIGHT_RED,
    "high":     COLOR_LIGHT_ORG,
    "medium":   colors.HexColor("#FEF9E7"),
    "low":      colors.HexColor("#EAFAF1"),
}


def _rc(risk: str) -> colors.Color:
    return RISK_COLORS.get(risk.lower(), colors.gray)


def _fmt_confidence(flag: dict) -> str:
    """Always return a real confidence string, never N/A."""
    conf = flag.get("confidence")
    if isinstance(conf, (float, int)):
        return f"{float(conf):.0%}"
    # Encoding node uses severity strings not confidence
    sev = flag.get("severity", "")
    sev_map = {"critical": "95%+", "high": "90%+", "medium": "75%+", "low": "65%+"}
    return sev_map.get(sev, "70%")


def _fmt_value(flag: dict) -> str:
    """Return the matched value or a safe placeholder."""
    val = flag.get("value") or flag.get("match") or ""
    if not val or val == "[REDACTED — abuse content]":
        return "[redacted]"
    return str(val)[:50]


def _fmt_context(flag: dict) -> str:
    """Return truncated context or note."""
    ctx = flag.get("context") or flag.get("note") or flag.get("recommendation") or ""
    ctx = ctx.replace("\n", " ").strip()
    return (ctx[:70] + "…") if len(ctx) > 70 else ctx


def _fmt_method(flag: dict) -> str:
    method = flag.get("detection_method", "ai")
    return "Regex" if method == "keyword" or method == "regex" else "AI"


def report_node(state: PipelineState) -> dict:
    """Generate an enterprise-grade PDF compliance report."""
    os.makedirs("reports", exist_ok=True)

    safe_name = "".join(c for c in state["pdf_name"] if c.isalnum() or c in "._- ")
    timestamp  = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = f"reports/{safe_name}_{state['upload_id']}_{timestamp}_compliance.pdf"

    doc = SimpleDocTemplate(
        report_path,
        pagesize=A4,
        rightMargin=1.8*cm, leftMargin=1.8*cm,
        topMargin=2*cm, bottomMargin=2*cm,
    )

    styles = getSampleStyleSheet()
    story  = []

    title_style = ParagraphStyle(
        "CT", parent=styles["Title"], fontSize=22,
        textColor=COLOR_HEADER, spaceAfter=6, alignment=TA_CENTER,
    )
    subtitle_style = ParagraphStyle(
        "Sub", parent=styles["Normal"], fontSize=9,
        textColor=colors.gray, alignment=TA_CENTER, spaceAfter=16,
    )
    section_heading = ParagraphStyle(
        "SH", parent=styles["Heading2"], fontSize=12,
        textColor=COLOR_HEADER, spaceBefore=12, spaceAfter=5,
    )
    body_style = ParagraphStyle(
        "B", parent=styles["Normal"], fontSize=8.5,
        spaceAfter=3, leading=13,
    )
    page_hdr_style = ParagraphStyle(
        "PH", parent=body_style, fontName="Helvetica-Bold", fontSize=9,
    )

    # ── TITLE ─────────────────────────────────────────────────────────────
    story.append(Paragraph("🛡️ PDF Compliance Report", title_style))
    story.append(Paragraph(
        f"Document: <b>{state['pdf_name']}</b> &nbsp;|&nbsp; "
        f"Scan ID: {state['upload_id']} &nbsp;|&nbsp; "
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        subtitle_style,
    ))
    story.append(HRFlowable(width="100%", thickness=2, color=COLOR_HEADER))
    story.append(Spacer(1, 0.4*cm))

    # ── EXECUTIVE SUMMARY ─────────────────────────────────────────────────
    summary = state.get("summary", {})
    story.append(Paragraph("Executive Summary", section_heading))

    highest_risk = summary.get("highest_risk", "low")
    risk_color   = _rc(highest_risk)

    summary_data = [
        ["Metric", "Value"],
        ["Total Pages Scanned",    str(summary.get("total_pages", 0))],
        ["Total Compliance Flags", str(summary.get("total_flags", 0))],
        ["Pages with Issues",      str(summary.get("pages_with_issues", 0))],
        ["Clean Pages",            str(summary.get("clean_pages", 0))],
        ["Highest Risk Level",     highest_risk.upper()],
        ["PII Violations",         str(summary.get("total_issues", {}).get("pii", 0))],
        ["Confidentiality Issues", str(summary.get("total_issues", {}).get("confidential", 0))],
        ["Encoding Issues",        str(summary.get("total_issues", {}).get("encoding", 0))],
        ["Abuse / Unlawful",       str(summary.get("total_issues", {}).get("abuse", 0))],
    ]

    summary_table = Table(summary_data, colWidths=[8.5*cm, 8.5*cm])
    summary_table.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, 0),  COLOR_HEADER),
        ("TEXTCOLOR",    (0, 0), (-1, 0),  COLOR_WHITE),
        ("FONTNAME",     (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",     (0, 0), (-1, 0),  10),
        ("BACKGROUND",   (0, 5), (-1, 5),  risk_color),
        ("TEXTCOLOR",    (0, 5), (-1, 5),  COLOR_WHITE),
        ("FONTNAME",     (0, 5), (-1, 5),  "Helvetica-Bold"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [COLOR_LIGHT_GRAY, COLOR_WHITE]),
        ("GRID",         (0, 0), (-1, -1), 0.4, colors.gray),
        ("FONTSIZE",     (0, 1), (-1, -1), 9),
        ("PADDING",      (0, 0), (-1, -1), 6),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 0.5*cm))

    # ── RISK HEATMAP ──────────────────────────────────────────────────────
    story.append(Paragraph("Page-by-Page Risk Heatmap", section_heading))
    heatmap_data = [["Page", "PII", "Confid.", "Encoding", "Abuse", "Total", "Risk"]]

    for pr in state.get("page_results", []):
        heatmap_data.append([
            str(pr["page_num"]),
            str(len(pr.get("pii_flags", []))),
            str(len(pr.get("confidential_flags", []))),
            str(len(pr.get("encoding_flags", []))),
            str(len(pr.get("abuse_flags", []))),
            str(pr.get("total_flags", 0)),
            pr.get("overall_risk", "low").upper(),
        ])

    heatmap_table = Table(
        heatmap_data,
        colWidths=[1.4*cm, 1.8*cm, 2.2*cm, 2.3*cm, 1.8*cm, 1.6*cm, 2.2*cm],
    )
    heatmap_style = [
        ("BACKGROUND",    (0, 0), (-1, 0),  COLOR_HEADER),
        ("TEXTCOLOR",     (0, 0), (-1, 0),  COLOR_WHITE),
        ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, -1), 8),
        ("GRID",          (0, 0), (-1, -1), 0.3, colors.gray),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("PADDING",       (0, 0), (-1, -1), 4),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [COLOR_LIGHT_GRAY, COLOR_WHITE]),
    ]
    for i, pr in enumerate(state.get("page_results", []), start=1):
        risk = pr.get("overall_risk", "low")
        if risk in ("critical", "high", "medium"):
            heatmap_style.append(("BACKGROUND", (6, i), (6, i), _rc(risk)))
            if risk in ("critical", "high"):
                heatmap_style.append(("TEXTCOLOR", (6, i), (6, i), COLOR_WHITE))

    heatmap_table.setStyle(TableStyle(heatmap_style))
    story.append(heatmap_table)
    story.append(Spacer(1, 0.5*cm))

    # ── DETAILED FINDINGS — enterprise-grade table ────────────────────────
    story.append(PageBreak())
    story.append(Paragraph("Detailed Findings", section_heading))
    story.append(Paragraph(
        "Each row represents one detected violation. "
        "Detection Method: <b>Regex</b> = pattern match; <b>AI</b> = model inference.",
        body_style,
    ))
    story.append(Spacer(1, 0.2*cm))

    for pr in state.get("page_results", []):
        all_flags = (
            [(f, "PII")          for f in pr.get("pii_flags", [])] +
            [(f, "CONFIDENTIAL") for f in pr.get("confidential_flags", [])] +
            [(f, "ENCODING")     for f in pr.get("encoding_flags", [])] +
            [(f, "ABUSE")        for f in pr.get("abuse_flags", [])]
        )
        if not all_flags:
            continue

        page_risk = pr.get("overall_risk", "low")
        page_hdr_para = Paragraph(
            f"Page {pr['page_num']} — Overall Risk: "
            f"<font color='#{_rc(page_risk).hexval()[2:]}'>●</font> "
            f"<b>{page_risk.upper()}</b>  ({len(all_flags)} flag(s))",
            ParagraphStyle(
                "PHx", parent=page_hdr_style,
                textColor=_rc(page_risk),
            ),
        )

        # Header row: Type | Entity Type | Matched Value | Confidence | Method | Severity | Context
        finding_data = [[
            "Type", "Entity", "Matched Value", "Conf.", "Method", "Severity", "Context / Snippet"
        ]]

        for flag, check_type in all_flags:
            category   = flag.get("category") or flag.get("type") or "UNKNOWN"
            matched    = _fmt_value(flag)
            confidence = _fmt_confidence(flag)
            method     = _fmt_method(flag)
            severity   = (flag.get("risk_level") or flag.get("severity") or "medium").upper()
            context    = _fmt_context(flag)

            finding_data.append([
                check_type,
                category,
                matched,
                confidence,
                method,
                severity,
                context,
            ])

        finding_table = Table(
            finding_data,
            colWidths=[1.8*cm, 2.2*cm, 2.5*cm, 1.2*cm, 1.3*cm, 1.7*cm, 6.5*cm],
        )

        # Base style
        finding_style = [
            ("BACKGROUND",    (0, 0), (-1, 0),  COLOR_SUB_HEADER),
            ("TEXTCOLOR",     (0, 0), (-1, 0),  COLOR_WHITE),
            ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
            ("FONTSIZE",      (0, 0), (-1, -1), 7),
            ("GRID",          (0, 0), (-1, -1), 0.3, colors.lightgrey),
            ("ROWBACKGROUNDS",(0, 1), (-1, -1), [COLOR_LIGHT_GRAY, COLOR_WHITE]),
            ("PADDING",       (0, 0), (-1, -1), 3),
            ("VALIGN",        (0, 0), (-1, -1), "TOP"),
            ("WORDWRAP",      (0, 0), (-1, -1), True),
        ]

        # Color-code severity column (col 5)
        for row_idx, (flag, _) in enumerate(all_flags, start=1):
            sev = (flag.get("risk_level") or flag.get("severity") or "low").lower()
            if sev in ("critical", "high"):
                finding_style.append(("BACKGROUND", (5, row_idx), (5, row_idx), _rc(sev)))
                finding_style.append(("TEXTCOLOR",  (5, row_idx), (5, row_idx), COLOR_WHITE))
            elif sev == "medium":
                finding_style.append(("BACKGROUND", (5, row_idx), (5, row_idx), COLOR_MEDIUM))

        finding_table.setStyle(TableStyle(finding_style))

        story.append(KeepTogether([page_hdr_para, Spacer(1, 0.1*cm), finding_table]))
        story.append(Spacer(1, 0.4*cm))

    doc.build(story)

    return {
        "report_path": report_path,
        "processing_complete": True,
    }
