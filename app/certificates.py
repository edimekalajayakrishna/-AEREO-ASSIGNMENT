import os
import re
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, A4
from reportlab.pdfgen import canvas

OUTPUT_DIR = os.getenv("CERTIFICATE_DIR", "certificates")

def safe_filename(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9_-]+", "_", value.strip())
    return value[:60] or "recipient"

def generate_certificate(*, recipient_name: str, event_name: str,
                         course_name: str, issuer_name: str,
                         job_id: int, recipient_id: int) -> str:
    """Generate one PDF from the application's single predefined template."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filename = f"job_{job_id}_{recipient_id}_{safe_filename(recipient_name)}.pdf"
    path = os.path.abspath(os.path.join(OUTPUT_DIR, filename))
    page = landscape(A4)
    pdf = canvas.Canvas(path, pagesize=page)
    width, height = page

    pdf.setFillColor(colors.HexColor("#F7F4EC"))
    pdf.rect(0, 0, width, height, fill=1, stroke=0)
    pdf.setStrokeColor(colors.HexColor("#17324D"))
    pdf.setLineWidth(4)
    pdf.rect(24, 24, width - 48, height - 48, fill=0, stroke=1)
    pdf.setStrokeColor(colors.HexColor("#C49A43"))
    pdf.setLineWidth(1.5)
    pdf.rect(35, 35, width - 70, height - 70, fill=0, stroke=1)

    pdf.setFillColor(colors.HexColor("#17324D"))
    pdf.setFont("Helvetica-Bold", 28)
    pdf.drawCentredString(width / 2, height - 105, "CERTIFICATE OF COMPLETION")
    pdf.setFillColor(colors.HexColor("#555555"))
    pdf.setFont("Helvetica", 14)
    pdf.drawCentredString(width / 2, height - 145, "This certificate is proudly presented to")
    pdf.setFillColor(colors.HexColor("#17324D"))
    pdf.setFont("Helvetica-Bold", 30)
    pdf.drawCentredString(width / 2, height - 195, recipient_name[:100])
    pdf.setFillColor(colors.HexColor("#555555"))
    pdf.setFont("Helvetica", 14)
    pdf.drawCentredString(width / 2, height - 232, "for successfully participating in / completing")
    pdf.setFillColor(colors.HexColor("#17324D"))
    pdf.setFont("Helvetica-Bold", 19)
    pdf.drawCentredString(width / 2, height - 265, course_name[:120])
    pdf.setFillColor(colors.HexColor("#555555"))
    pdf.setFont("Helvetica", 12)
    pdf.drawCentredString(width / 2, 95, f"Event: {event_name[:120]}")
    pdf.setStrokeColor(colors.HexColor("#17324D"))
    pdf.line(width / 2 - 100, 75, width / 2 + 100, 75)
    pdf.setFont("Helvetica-Bold", 12)
    pdf.setFillColor(colors.HexColor("#17324D"))
    pdf.drawCentredString(width / 2, 55, issuer_name[:100])
    pdf.save()
    return path
