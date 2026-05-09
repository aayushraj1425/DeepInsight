from pydantic import BaseModel, Field
from agents.state import AgentState
from events import AgentEvent
from runtime import emit
from llm import client


class CriticVerdict(BaseModel):
    approved: bool = Field(
        description="True if the analysis adequately addresses the research question with the available data"
    )
    reasoning: str = Field(description="Concise explanation of the decision")
    feedback: str = Field(
        "",
        description="Specific, actionable feedback for the Analyst if rejecting. Empty string if approving.",
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

    verdict: CriticVerdict = await client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a rigorous research quality critic. Evaluate whether the statistical "
                    "analysis adequately addresses the research question given the available findings.\n\n"
                    "REJECT if:\n"
                    "- findings list is empty or has fewer than 2 items\n"
                    "- analysis contains an error key or only stub data\n"
                    "- key statistics are missing (e.g. aggregate ran but value_stats is absent)\n"
                    "- the analysis does not address the research question\n\n"
                    "APPROVE if the analysis is substantive and accurately represents the data, "
                    "even if findings are sparse."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Research query: {state['query']}\n"
                    f"Findings count: {len(findings)}\n"
                    f"Analysis result: {analysis}"
                ),
            },
        ],
        response_model=CriticVerdict,
    )

    new_retries = retries if verdict.approved else retries + 1

    await emit(sid, AgentEvent(
        type="critic_decision", agent="critic",
        payload={
            "decision": "approve" if verdict.approved else "reject",
            "reasoning": verdict.reasoning,
            "feedback": verdict.feedback,
            "retries_used": retries,
            "retry_count": new_retries,
            "max_retries": 2,
        }
    ))
    await emit(sid, AgentEvent(
        type="node_end", agent="critic",
        payload={"approved": verdict.approved}
    ))
    return {
        "approved": verdict.approved,
        "critic_feedback": verdict.feedback,
        "critic_retries": new_retries,
    }


def route_after_critic(state: AgentState) -> str:
    if state.get("approved", False) or state.get("critic_retries", 0) >= 2:
        return "visualizer"
    return "analyst"
