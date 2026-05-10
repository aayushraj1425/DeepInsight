from typing import Literal
from pydantic import BaseModel, Field
from agents.state import AgentState
from events import AgentEvent
from runtime import emit
from llm import client


class CriticVerdict(BaseModel):
    approved: bool = Field(
        description="True if analysis is substantive and findings are grounded in real source quotes"
    )
    reasoning: str = Field(description="Concise explanation of the decision")
    rejection_type: Literal["hallucinated", "weak_analysis", "off_topic", ""] = Field(
        "",
        description=(
            "Why rejected: "
            "'hallucinated' — quotes/numbers not from source text; "
            "'weak_analysis' — findings exist but analysis tools chose wrong grouping; "
            "'off_topic' — findings don't address the research question; "
            "'' — approved"
        ),
    )
    feedback: str = Field(
        "",
        description="Specific actionable feedback for the next agent. Empty if approving.",
    )


async def critic_node(state: AgentState) -> dict:
    sid = state["session_id"]
    retries = state.get("critic_retries", 0)
    findings = state.get("findings", [])
    analysis = state.get("analysis", {})

    await emit(sid, AgentEvent(
        type="node_start", agent="critic",
        payload={"message": f"Reviewing analysis quality... (attempt {retries + 1}/3)"}
    ))

    # Empty findings: approve immediately — no retry will help, reporter handles it honestly
    if not findings:
        verdict_approved = True
        rejection_type = ""
        verdict_reasoning = "No numeric findings — source texts had no explicit numbers. Reporter will synthesize from abstracts."
        verdict_feedback = ""
    else:
        verdict_obj: CriticVerdict = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a research quality auditor. Classify rejections precisely — "
                        "the rejection_type determines which agent fixes the problem.\n\n"
                        "REJECT + rejection_type='hallucinated' if:\n"
                        "- A source_quote is not verbatim from the source (fabricated or paraphrased)\n"
                        "- A number in a finding does not appear in its source_quote\n"
                        "- Numbers are suspiciously round (10%, 50%) with zero context\n"
                        "→ Cause: bad source papers. Fix: re-discover with different queries.\n\n"
                        "REJECT + rejection_type='off_topic' if:\n"
                        "- Findings are real but address a completely different question than asked\n"
                        "- Papers found were about adjacent topics, not the actual query\n"
                        "→ Cause: wrong papers. Fix: re-discover with rephrased queries.\n\n"
                        "REJECT + rejection_type='weak_analysis' if:\n"
                        "- Findings are valid but the analyst chose wrong grouping or wrong tools\n"
                        "- Compare/correlate was run on incompatible metrics\n"
                        "→ Cause: analysis strategy. Fix: retry analyst with different tools.\n\n"
                        "APPROVE if:\n"
                        "- At least 2 findings have real numbers grounded in verbatim source quotes, OR\n"
                        "- Findings are sparse but honest — sparse honest data beats rich hallucinated data"
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Research query: {state['query']}\n"
                        f"Findings count: {len(findings)}\n"
                        f"Sample findings (first 6): {findings[:6]}\n"
                        f"Analysis result: {analysis}"
                    ),
                },
            ],
            response_model=CriticVerdict,
        )
        verdict_approved = verdict_obj.approved
        rejection_type = verdict_obj.rejection_type if not verdict_approved else ""
        verdict_reasoning = verdict_obj.reasoning
        verdict_feedback = verdict_obj.feedback

    new_retries = retries if verdict_approved else retries + 1

    await emit(sid, AgentEvent(
        type="critic_decision", agent="critic",
        payload={
            "decision": "approve" if verdict_approved else "reject",
            "rejection_type": rejection_type,
            "reasoning": verdict_reasoning,
            "feedback": verdict_feedback,
            "retry_count": new_retries,
            "max_retries": 2,
        }
    ))
    await emit(sid, AgentEvent(
        type="node_end", agent="critic",
        payload={"approved": verdict_approved}
    ))
    return {
        "approved": verdict_approved,
        "critic_feedback": verdict_feedback,
        "critic_rejection_type": rejection_type,
        "critic_retries": new_retries,
    }


def route_after_critic(state: AgentState) -> str:
    if state.get("approved", False):
        return "visualizer"

    retries = state.get("critic_retries", 0)
    if retries >= 2:
        # Max retries hit — force through so user always gets a response
        return "visualizer"

    rejection_type = state.get("critic_rejection_type", "")
    discovery_retries = state.get("discovery_retries", 0)

    # Hallucinated or off-topic findings → problem is in the source papers, not the analysis
    # Re-run discovery with fallback queries (only once to avoid infinite loops)
    if rejection_type in ("hallucinated", "off_topic") and discovery_retries == 0:
        return "discovery"

    # Weak analysis → same papers, different analysis strategy
    return "analyst"
