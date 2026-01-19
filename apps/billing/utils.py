from io import BytesIO
from django.conf import settings

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch


def generate_invoice_pdf(invoice):
    """
    Generates a PDF from a simple HTML template using ReportLab's Paragraph parser.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, leftMargin=0.75*inch, rightMargin=0.75*inch, topMargin=0.75*inch, bottomMargin=0.75*inch)
    
    # Container for the 'Flowable' objects
    story = []
    styles = getSampleStyleSheet()

    # Get the custom HTML template
    from django.template.loader import render_to_string
    html_string = render_to_string('billing/invoice_pdf_simple.html', {'invoice': invoice})

    # The magic: Use the Paragraph style to parse the HTML
    # We use a custom style to allow for more text content
    story.append(Paragraph(html_string, styles['Normal']))

    # Build the PDF
    doc.build(story)

    # Rewind and return the buffer
    buffer.seek(0)
    return buffer