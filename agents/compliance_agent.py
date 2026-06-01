"""
Compliance Agent — RAG over fair housing rules with veto authority
"""
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pydantic import BaseModel, Field
from typing import Literal


class ComplianceReview(BaseModel):
    verdict: Literal["approved", "escalate_to_human", "vetoed"]
    triggered_rules: list[str]
    reasoning: str
    required_action: str

_vector_store = None

def _get_vector_store():
    global _vector_store
    if _vector_store is None:
        loader = TextLoader("knowledge_base/fair_housing_rules.txt")
        docs = loader.load()
        splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=50)
        chunks = splitter.split_documents(docs)
        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        _vector_store = FAISS.from_documents(chunks, embeddings)
    return _vector_store

def review_decision(profile_dict: dict, decision_dict: dict) -> ComplianceReview:
    vs = _get_vector_store()

    query = (
        f"Renewal recommendation: {decision_dict['recommendation']}, "
        f"rent change {decision_dict['rent_change_percent']}%, "
        f"tenure {profile_dict.get('tenure_category')}, "
        f"payment reliability {profile_dict.get('payment_reliability')}"
    )
    relevant_rules = vs.similarity_search(query, k=4)
    rules_context = "\n\n".join([d.page_content for d in relevant_rules])

    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
    structured_llm = llm.with_structured_output(ComplianceReview)

    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "You are a Compliance Agent. Review the renewal decision against the "
         "provided fair housing and policy rules. Verdicts:\n"
         "- approved: fully compliant\n"
         "- escalate_to_human: acceptable but needs human review per policy\n"
         "- vetoed: violates policy, must not proceed\n\n"
         "Always escalate non-renewals, rent increases above 10%, residents with "
         "<6mo history, or any case with potential fair housing risk. "
         "Be strict. When in doubt, escalate."),
        ("user",
         "Relevant policy rules:\n{rules}\n\n"
         "Resident profile:\n{profile}\n\n"
         "Renewal decision:\n{decision}\n\n"
         "Review for compliance.")
    ])

    chain = prompt | structured_llm
    return chain.invoke({
        "rules": rules_context,
        "profile": profile_dict,
        "decision": decision_dict
    })