from pydantic import BaseModel, Field
from agents.state import AgentState
from events import AgentEvent
from runtime import emit
from llm import client


class CriticVerdict(BaseModel):
    approved: bool = Field(
        description="True only if analysis is substantive and findings are grounded in real source quotes"
    )
    reasoning: str = Field(description="Concise explanation of the decision")
    feedback: str = Field(
        "",
        description="Specific actionable feedback for the Analyst if rejecting. Empty string if approving.",
    )
    specific_action: str = Field(
        "",
        description="Concrete next step for the Analyst: which tool to run, which field to focus on.",
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

    # Pre-check: approve immediately if findings are genuinely empty (no retry helps)
    if not findings:
        verdict_approved = True
        verdict_reasoning = "No numeric findings extracted — source texts had no explicit numbers. Proceeding to report with data-quality note."
        verdict_feedback = ""
        verdict_action = ""
    else:
        verdict_obj: CriticVerdict = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You review research findings for data quality and hallucination. "
                        "Be strict — your job is to catch bad data before it reaches the report.\n\n"
                        "REJECT if ANY of these are true:\n"
                        "1. A finding has no source_quote, or the quote is vague/missing a number.\n"
                        "2. Numbers are suspiciously round (exactly 10%, 15%, 50%) with no context — "
                        "hallucination smell.\n"
                        "3. Fewer than 2 findings have a source_quote that contains the cited number.\n"
                        "4. The findings cite wildly different populations/regions/years that do not "
                        "combine coherently into one analysis.\n"
                        "5. The analysis only has an 'error' key or stub data.\n"
                        "6. The findings clearly don't address the research question at all.\n\n"
                        "APPROVE if:\n"
                        "- At least 2 findings have real numeric values grounded in source quotes, OR\n"
                        "- Findings are sparse but honest (the data simply isn't there) — "
                        "sparse honest data is better than rich hallucinated data.\n\n"
                        "When rejecting, name the specific finding and rule violated in `feedback`. "
                        "Put a concrete next step in `specific_action`."
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
        verdict_reasoning = verdict_obj.reasoning
        verdict_feedback = verdict_obj.feedback
        verdict_action = verdict_obj.specific_action

    new_retries = retries if verdict_approved else retries + 1

    await emit(sid, AgentEvent(
        type="critic_decision", agent="critic",
        payload={
            "decision": "approve" if verdict_approved else "reject",
            "reasoning": verdict_reasoning,
            "feedback": verdict_feedback,
            "specific_action": verdict_action,
            "retries_used": retries,
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
        "critic_retries": new_retries,
    }


def route_after_critic(state: AgentState) -> str:
    if state.get("approved", False) or state.get("critic_retries", 0) >= 2:
        return "visualizer"
    return "analyst"
