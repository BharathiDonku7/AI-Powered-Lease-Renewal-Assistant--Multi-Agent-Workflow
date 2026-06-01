"""
Orchestrator
Coordinates all agents. Can optionally start from a PDF document (Document Ingestion Agent)
or directly from a structured resident record.
"""
from agents.document_ingestion_agent import ingest_document
from agents.resident_profile_agent import build_profile
from agents.renewal_decision_agent import make_decision
from agents.compliance_agent import review_decision
from agents.communication_agent import draft_communication


def process_renewal_from_pdf(pdf_path: str) -> dict:
    """End-to-end flow starting from an unstructured PDF document."""
    ingestion = ingest_document(pdf_path)
    resident = ingestion["resident"]
    ingestion_trace = ingestion["ingestion_trace"]

    # Exception handling — low confidence routes to human review
    if ingestion_trace["needs_human_review"]:
        return {
            "resident_id": resident.get("resident_id", "UNKNOWN"),
            "resident_name": resident.get("name", "UNKNOWN"),
            "steps": [{
                "agent": "DocumentIngestionAgent",
                "output": {
                    "resident_extracted": resident,
                    "ingestion_trace": ingestion_trace
                }
            }],
            "final_status": "pending_human_review_ingestion"
        }

    trace = process_renewal(resident)
    trace["steps"].insert(0, {
        "agent": "DocumentIngestionAgent",
        "output": {
            "resident_extracted": resident,
            "ingestion_trace": ingestion_trace
        }
    })
    return trace


def process_renewal(resident: dict) -> dict:
    """Standard pipeline starting from a structured resident record."""
    trace = {"resident_id": resident["resident_id"], "steps": []}

    profile = build_profile(resident)
    profile_dict = profile.model_dump()
    trace["steps"].append({"agent": "ResidentProfileAgent", "output": profile_dict})
   
    # Add zipcode to profile so the agent can use it for local context lookups
    profile_with_zip = {**profile_dict, "zipcode": resident.get("zipcode", "")}
    decision = make_decision(
        profile_dict=profile_with_zip,
        current_rent=resident["current_rent"],
        market_rate=resident["market_rate_for_unit"],
        property_name=resident.get("property", "")
    )
    decision_dict = decision.model_dump()
    trace["steps"].append({"agent": "RenewalDecisionAgent", "output": decision_dict})

    review = review_decision(profile_dict=profile_dict, decision_dict=decision_dict)
    review_dict = review.model_dump()
    trace["steps"].append({"agent": "ComplianceAgent", "output": review_dict})

    if review.verdict in ("approved", "escalate_to_human"):
        comm = draft_communication(resident, profile_dict, decision_dict)
        comm_dict = comm.model_dump()
        trace["steps"].append({"agent": "CommunicationAgent", "output": comm_dict})
    else:
        trace["steps"].append({
            "agent": "CommunicationAgent",
            "output": {"status": "skipped", "reason": "blocked by compliance"}
        })

    if review.verdict == "approved":
        final_status = "auto_approved_and_sent"
    elif review.verdict == "escalate_to_human":
        final_status = "pending_human_review"
    else:
        final_status = "blocked_by_compliance"

    trace["final_status"] = final_status
    trace["resident_name"] = resident["name"]
    return trace