"""
Document Ingestion Agent
Reads an unstructured rental application or lease PDF, extracts the text,
and uses an LLM to convert it into the structured resident JSON format
that the rest of the pipeline expects.

Implements exception handling: if required fields can't be extracted with
high confidence, the resident is routed to human review for manual correction.
"""
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from typing import Literal, Optional
from pypdf import PdfReader


class ExtractedResident(BaseModel):
    resident_id: str = Field(description="Unique resident ID; generate if missing")
    name: str
    unit: str
    property: str
    current_rent: float
    lease_start: str = Field(description="YYYY-MM-DD")
    lease_end: str = Field(description="YYYY-MM-DD")
    on_time_payments: int
    late_payments: int
    missed_payments: int
    maintenance_tickets: int
    communication_preference: Literal["email", "text"]
    tenure_months: int
    market_rate_for_unit: float
    extraction_confidence: float = Field(
        ge=0, le=1,
        description="0-1 confidence that extraction is reliable"
    )
    missing_fields: list[str] = Field(
        description="Any fields the agent had to guess or default"
    )


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract raw text from a PDF using pypdf."""
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text


def ingest_document(pdf_path: str) -> dict:
    """
    Reads a rental application PDF and returns a structured resident record
    in the same format as data/residents.json, plus an ingestion trace.
    """
    raw_text = extract_text_from_pdf(pdf_path)

    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
    structured_llm = llm.with_structured_output(ExtractedResident)

    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "You are a Document Ingestion Agent for a property management AI system. "
         "Extract structured resident data from a rental application or lease document. "
         "Rules:\n"
         "- Extract only what you can read from the document\n"
         "- If a field is missing, default it sensibly and list it in missing_fields\n"
         "- Lower extraction_confidence if you had to guess any important field\n"
         "- Never invent identity details (name, unit) — these MUST come from the document\n"
         "- Numeric fields default to 0 if not present\n"
         "- Communication preference defaults to 'email' if not stated"),
        ("user",
         "Document text:\n\n{text}\n\n"
         "Extract a structured resident record.")
    ])

    chain = prompt | structured_llm
    extracted = chain.invoke({"text": raw_text})

    # Convert to the same shape as data/residents.json entries
    resident_record = {
        "resident_id": extracted.resident_id,
        "name": extracted.name,
        "unit": extracted.unit,
        "property": extracted.property,
        "current_rent": extracted.current_rent,
        "lease_start": extracted.lease_start,
        "lease_end": extracted.lease_end,
        "payment_history": {
            "on_time_payments": extracted.on_time_payments,
            "late_payments": extracted.late_payments,
            "missed_payments": extracted.missed_payments
        },
        "maintenance_tickets": extracted.maintenance_tickets,
        "communication_preference": extracted.communication_preference,
        "tenure_months": extracted.tenure_months,
        "market_rate_for_unit": extracted.market_rate_for_unit
    }

    ingestion_trace = {
        "raw_text_length": len(raw_text),
        "extraction_confidence": extracted.extraction_confidence,
        "missing_fields": extracted.missing_fields,
        "needs_human_review": extracted.extraction_confidence < 0.7 or len(extracted.missing_fields) > 2
    }

    return {
        "resident": resident_record,
        "ingestion_trace": ingestion_trace
    }