"""
Resident Profile Agent
"""
import json
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from typing import Literal


class ResidentProfile(BaseModel):
    resident_id: str
    name: str
    tenure_category: Literal["new", "established", "long_term"]
    payment_reliability: Literal["excellent", "good", "concerning", "poor"]
    maintenance_engagement: Literal["low", "moderate", "high"]
    market_position: Literal["under_market", "at_market", "over_market"]
    rent_gap_percent: float
    risk_signals: list[str]
    summary: str


def build_profile(resident: dict) -> ResidentProfile:
    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
    structured_llm = llm.with_structured_output(ResidentProfile)

    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "You are a Resident Profile Agent for a property management AI system. "
         "Given raw resident data, produce a structured profile that downstream "
         "agents can use for renewal decisions. Be objective. Never infer protected characteristics."),
        ("user",
         "Resident data:\n{resident_json}\n\nProduce a structured profile.")
    ])

    chain = prompt | structured_llm
    return chain.invoke({"resident_json": json.dumps(resident, indent=2)})