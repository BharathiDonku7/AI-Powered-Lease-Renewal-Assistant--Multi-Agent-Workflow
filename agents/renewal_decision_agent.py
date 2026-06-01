"""
Renewal Decision Agent
Recommends a renewal strategy. Has access to two tools — a market intelligence
lookup and a live external API for local geographic context. The LLM decides
at runtime whether to invoke either tool.
"""
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from pydantic import BaseModel, Field
from typing import Literal
from tools.market_tools import lookup_market_rate, get_local_context


class RenewalDecision(BaseModel):
    recommendation: Literal[
        "standard_renewal",
        "retention_discount",
        "premium_offer",
        "do_not_renew"
    ]
    proposed_rent: float
    rent_change_percent: float
    lease_term_months: int
    reasoning: str
    confidence: float = Field(ge=0, le=1)
    tools_used: list[str] = Field(default_factory=list)


def make_decision(
    profile_dict: dict,
    current_rent: float,
    market_rate: float,
    property_name: str = ""
) -> RenewalDecision:
    base_llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
    llm_with_tools = base_llm.bind_tools([lookup_market_rate, get_local_context])

    system_msg = SystemMessage(content=(
        "You are a Renewal Decision Agent. You have access to two tools:\n"
        "- lookup_market_rate: fetches market intelligence for a property\n"
        "- get_local_context: live external API for geographic context by zipcode\n\n"
        "Use them when helpful to gather context before making a decision. "
        "After gathering info, produce a renewal decision.\n\n"
        "Guidelines:\n"
        "- Excellent payers with long tenure: consider retention_discount\n"
        "- Strong payers under market: premium_offer (modest increase toward market)\n"
        "- Poor payment history (missed payments): do_not_renew\n"
        "- Default: standard_renewal\n"
        "- Never recommend rent increase above 15%\n"
        "- Never use protected characteristics"
    ))

    user_msg = HumanMessage(content=(
        f"Resident Profile: {profile_dict}\n\n"
        f"Current rent: ${current_rent}\n"
        f"Listed market rate: ${market_rate}\n"
        f"Property: {property_name}\n\n"
        "Decide on the renewal. You may call any of the available tools "
        "before deciding if you want more context."
    ))

    messages = [system_msg, user_msg]
    tools_used = []

    # First LLM call — the LLM decides whether to use any tools
    ai_response = llm_with_tools.invoke(messages)
    messages.append(ai_response)

    # Execute any tool calls the LLM made
    if ai_response.tool_calls:
        for tool_call in ai_response.tool_calls:
            tool_name = tool_call["name"]
            if tool_name == "lookup_market_rate":
                tool_result = lookup_market_rate.invoke(tool_call["args"])
                tools_used.append("lookup_market_rate")
            elif tool_name == "get_local_context":
                tool_result = get_local_context.invoke(tool_call["args"])
                tools_used.append("get_local_context")
            else:
                continue
            messages.append(ToolMessage(
                content=str(tool_result),
                tool_call_id=tool_call["id"]
            ))

        # Follow-up call now that the LLM has the tool results
        ai_response = base_llm.invoke(messages)
        messages.append(ai_response)

    # Convert the conclusion to structured output.
    # We send messages directly (no ChatPromptTemplate) so curly braces in
    # the conversation context aren't misinterpreted as template variables.
    structured_llm = base_llm.with_structured_output(RenewalDecision)

    conversation_summary = "\n".join([
        str(m.content) for m in messages if hasattr(m, "content")
    ])

    final_messages = [
        SystemMessage(content=(
            "Based on the conversation above, produce the final structured renewal decision."
        )),
        HumanMessage(content=(
            f"Conversation context:\n{conversation_summary}\n\n"
            f"Resident profile (key fields): tenure={profile_dict.get('tenure_category')}, "
            f"payment_reliability={profile_dict.get('payment_reliability')}, "
            f"market_position={profile_dict.get('market_position')}\n"
            f"Current rent: ${current_rent}\n"
            f"Market rate: ${market_rate}\n\n"
            "Output the final RenewalDecision."
        ))
    ]

    decision = structured_llm.invoke(final_messages)
    decision.tools_used = tools_used
    return decision