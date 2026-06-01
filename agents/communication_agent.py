"""
Communication Agent
Drafts a personalized renewal email/text for the resident based on the
approved decision, the resident's profile, and their communication preference.
"""
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from typing import Literal

class RenewalCommunication(BaseModel):
    channel: Literal["email", "text"]
    subject: str = Field(description="Subject line if email, short header if text")
    body: str = Field(description="The actual message body, personalized and respectful")
    tone_notes: str = Field(description="One-line note on the tone chosen and why")


def draft_communication(
    resident: dict,
    profile_dict: dict,
    decision_dict: dict
) -> RenewalCommunication:
    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.3)
    structured_llm = llm.with_structured_output(RenewalCommunication)

    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "You are a Communication Agent for a property management AI system. "
         "Your job is to draft a renewal communication that is:\n"
         "- Respectful and clear\n"
         "- Personalized to the resident's tenure and history (without referencing "
         "any protected characteristics)\n"
         "- Consistent in tone regardless of resident identity\n"
         "- Includes the resident's right to discuss the terms with management\n\n"
         "Tone guidance based on decision type:\n"
         "- retention_discount: warm, appreciative of their tenure\n"
         "- standard_renewal: professional and clear\n"
         "- premium_offer: positive, framing the new terms clearly\n\n"
         "Match the channel to the resident's communication_preference. "
         "Keep emails under 200 words, texts under 60 words."),
        ("user",
         "Resident name: {name}\n"
         "Unit: {unit}, Property: {property}\n"
         "Communication preference: {channel}\n"
         "Tenure: {tenure_months} months\n\n"
         "Resident Profile: {profile}\n\n"
         "Renewal Decision: {decision}\n\n"
         "Draft the renewal communication.")
    ])

    chain = prompt | structured_llm
    return chain.invoke({
        "name": resident["name"],
        "unit": resident["unit"],
        "property": resident["property"],
        "channel": resident["communication_preference"],
        "tenure_months": resident["tenure_months"],
        "profile": profile_dict,
        "decision": decision_dict
    })