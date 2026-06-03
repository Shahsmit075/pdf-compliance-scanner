import sys
import os
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT

COLOR_CRITICAL   = colors.HexColor("#C0392B")
COLOR_HIGH       = colors.HexColor("#E67E22")
COLOR_MEDIUM     = colors.HexColor("#F39C12")
COLOR_LOW        = colors.HexColor("#27AE60")
COLOR_HEADER     = colors.HexColor("#2C3E50")
COLOR_SUB_HEADER = colors.HexColor("#34495E")
COLOR_LIGHT_GRAY = colors.HexColor("#ECF0F1")
COLOR_WHITE      = colors.white

def make_wrappable(text: str) -> str:
    """Make long contiguous strings wrappable in ReportLab by inserting zero-width spaces."""
    if not text:
        return text
    # Escape HTML special characters since we'll wrap in Paragraph which parses XML
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    
    words = text.split(" ")
    processed_words = []
    
    # We use a unique placeholder that contains no separators
    placeholder = "XBREAKX"
    
    for word in words:
        if len(word) <= 10:
            processed_words.append(word)
            continue
        w = word
        for sep in ["_", "-", ":", "/", ".", "="]:
            w = w.replace(sep, f"{sep}{placeholder}")
            
        chunks = w.split(placeholder)
        processed_chunks = []
        for chunk in chunks:
            if len(chunk) > 10:
                sub_chunks = [chunk[i:i+6] for i in range(0, len(chunk), 6)]
                processed_chunks.append(placeholder.join(sub_chunks))
            else:
                processed_chunks.append(chunk)
        processed_words.append(placeholder.join(processed_chunks))
        
    final_text = " ".join(processed_words)
    # Now replace placeholder with the 0-size font tag acting as ZWSP
    zwsp = '<font size="0"> </font>'
    return final_text.replace(placeholder, zwsp)

def main():
    doc = SimpleDocTemplate(
        "scratch/test_output.pdf",
        pagesize=A4,
        rightMargin=1.8*cm, leftMargin=1.8*cm,
        topMargin=2*cm, bottomMargin=2*cm,
    )
    
    styles = getSampleStyleSheet()
    story = []
    
    table_cell_style = ParagraphStyle(
        "TCell", parent=styles["Normal"], fontName="Helvetica", fontSize=7,
        leading=9,
    )
    table_cell_center_style = ParagraphStyle(
        "TCellC", parent=table_cell_style, alignment=TA_CENTER,
    )
    table_cell_bold_style = ParagraphStyle(
        "TCellB", parent=table_cell_style, fontName="Helvetica-Bold",
        textColor=COLOR_WHITE,
    )
    table_cell_bold_center_style = ParagraphStyle(
        "TCellBC", parent=table_cell_bold_style, alignment=TA_CENTER,
    )
    
    finding_data = [[
        Paragraph("Violation", table_cell_bold_style),
        Paragraph("Matched Value", table_cell_bold_style),
        Paragraph("Severity", table_cell_bold_center_style),
        Paragraph("Detection", table_cell_bold_center_style),
        Paragraph("Context / Snippet", table_cell_bold_style),
    ]]
    
    # Let's add some test rows matching the user's data
    test_violations = [
        ("CONFIDENTIAL", "AWS_ACCESS_KEY", "AKIAIO...MPLE", "99%", "Regex", "CRITICAL", "CONFIDENTIAL AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE"),
        ("CONFIDENTIAL", "AWS_SECRET_KEY", "AWS_SE...EKEY", "97%", "Regex", "CRITICAL", "CONFIDENTIAL AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE"),
        ("CONFIDENTIAL", "GITHUB_TOKEN", "ghp_12...wxyz", "98%", "Regex", "CRITICAL", "...=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY GitHub Token:"),
        ("CONFIDENTIAL", "PASSWORD_INLINE", "PASSWO...123!", "91%", "Regex", "CRITICAL", "...tials: DB_HOST=prod-db.company.internal DB_USER=admin DB_PAS"),
        ("CONFIDENTIAL", "SALARY_DATA", "Salary...0000", "82%", "Regex", "HIGH", "...ASSWORD=SuperSecretPassword123! Salary Information: CEO Sala"),
        ("ENCODING", "OCR_CORRUPTION", "[redacted]", "85%", "AI", "HIGH", "OCR corruption patterns: Isolated chars, OCR confusion chars (l/1/0/O)"),
    ]
    
    for check_type, category, matched, confidence, method, severity, context in test_violations:
        v_type_wrapped = make_wrappable(check_type)
        v_cat_wrapped = make_wrappable(category)
        violation_html = f"<b>{v_type_wrapped}</b><br/><font color='#555555'>{v_cat_wrapped}</font>"
        
        finding_data.append([
            Paragraph(violation_html, table_cell_style),
            Paragraph(make_wrappable(matched), table_cell_style),
            severity,
            f"{method} ({confidence})",
            Paragraph(make_wrappable(context), table_cell_style),
        ])
        
    finding_table = Table(
        finding_data,
        colWidths=[3.5*cm, 3.0*cm, 1.5*cm, 2.2*cm, 7.2*cm],
    )
    
    finding_style = [
        ("BACKGROUND",    (0, 0), (-1, 0),  COLOR_SUB_HEADER),
        ("GRID",          (0, 0), (-1, -1), 0.3, colors.lightgrey),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [COLOR_LIGHT_GRAY, COLOR_WHITE]),
        ("PADDING",       (0, 0), (-1, -1), 3),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("ALIGN",         (2, 0), (3, -1),  "CENTER"),
        ("FONTNAME",      (2, 1), (3, -1),  "Helvetica"),
        ("FONTSIZE",      (2, 1), (3, -1),  7),
    ]
    
    # Apply color coding to Severity column (col 2)
    for i in range(1, len(finding_data)):
        sev = test_violations[i-1][5].lower()
        if sev == "critical":
            finding_style.append(("BACKGROUND", (2, i), (2, i), COLOR_CRITICAL))
            finding_style.append(("TEXTCOLOR",  (2, i), (2, i), COLOR_WHITE))
            finding_style.append(("FONTNAME",   (2, i), (2, i), "Helvetica-Bold"))
        elif sev == "high":
            finding_style.append(("BACKGROUND", (2, i), (2, i), COLOR_HIGH))
            finding_style.append(("TEXTCOLOR",  (2, i), (2, i), COLOR_WHITE))
            finding_style.append(("FONTNAME",   (2, i), (2, i), "Helvetica-Bold"))
        elif sev == "medium":
            finding_style.append(("BACKGROUND", (2, i), (2, i), COLOR_MEDIUM))
            finding_style.append(("TEXTCOLOR",  (2, i), (2, i), COLOR_WHITE))
            finding_style.append(("FONTNAME",   (2, i), (2, i), "Helvetica-Bold"))
        else:
            finding_style.append(("BACKGROUND", (2, i), (2, i), COLOR_LOW))
            finding_style.append(("TEXTCOLOR",  (2, i), (2, i), COLOR_WHITE))
            finding_style.append(("FONTNAME",   (2, i), (2, i), "Helvetica-Bold"))
            
    finding_table.setStyle(TableStyle(finding_style))
    story.append(finding_table)
    
    doc.build(story)
    print("Test PDF built successfully in scratch/test_output.pdf")

if __name__ == "__main__":
    main()
