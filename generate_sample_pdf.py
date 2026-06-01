"""
Generates a sample rental application PDF for testing the Document Ingestion Agent.
"""
from pypdf import PdfWriter
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

filename = "sample_documents/rental_application_sample.pdf"
c = canvas.Canvas(filename, pagesize=letter)
c.setFont("Helvetica", 11)

lines = [
    "RENTAL APPLICATION & LEASE SUMMARY",
    "Maple Ridge Apartments",
    "",
    "Applicant Name: David Martinez",
    "Resident ID: R006",
    "Unit Number: 5B",
    "Property: Maple Ridge Apartments",
    "",
    "Lease Details",
    "Lease Start Date: 2024-04-01",
    "Lease End Date: 2025-03-31",
    "Current Monthly Rent: $1,725",
    "Comparable Market Rate: $1,875",
    "",
    "Payment History (Past 12 Months)",
    "On-Time Payments: 12",
    "Late Payments: 0",
    "Missed Payments: 0",
    "",
    "Maintenance",
    "Submitted Maintenance Tickets: 1",
    "",
    "Tenure: 12 months",
    "Preferred Communication: email",
    "",
    "All information provided is accurate to the best of my knowledge.",
]

y = 720
for line in lines:
    c.drawString(72, y, line)
    y -= 18
c.save()
print(f"Generated: {filename}")