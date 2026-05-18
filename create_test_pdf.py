# create_test_pdf.py — run this to generate a demo PDF for testing
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4


def create_test_pdf():
    c = canvas.Canvas("tests/fixtures/demo_violations.pdf", pagesize=A4)
    width, height = A4

    # Page 1: PII violations
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, height - 50, "Employee Record — Confidential")
    c.setFont("Helvetica", 11)
    c.drawString(50, height - 90, "Name: John Smith")
    c.drawString(50, height - 110, "Email: john.smith@company.com")
    c.drawString(50, height - 130, "Phone: +91-9876543210")
    c.drawString(50, height - 150, "Aadhaar: 1234 5678 9012")
    c.drawString(50, height - 170, "Address: 42 MG Road, Bangalore 560001")
    c.showPage()

    # Page 2: Confidential data
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, height - 50, "System Configuration — DO NOT SHARE")
    c.setFont("Helvetica", 11)
    c.drawString(50, height - 90, "API Key: sk-prod-abc123def456ghi789jkl012mno345pqr")
    c.drawString(50, height - 110, "Database password: SuperSecret@DB123")
    c.drawString(50, height - 130, "Project: OPERATION PHOENIX — Phase 2 Launch")
    c.drawString(50, height - 150, "Q4 Revenue Target: $42M (confidential)")
    c.showPage()

    # Page 3: Clean page
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, height - 50, "Public Information")
    c.setFont("Helvetica", 11)
    c.drawString(50, height - 90, "Our company was founded in 2020.")
    c.drawString(50, height - 110, "We operate in the technology sector.")
    c.drawString(50, height - 130, "Contact our PR team for media inquiries.")
    c.showPage()

    c.save()
    print("Demo PDF created: tests/fixtures/demo_violations.pdf")


create_test_pdf()
