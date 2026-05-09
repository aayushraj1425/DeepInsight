from pydantic import BaseModel, Field

from agents.state import AgentState
from events import AgentEvent
from llm import client
from runtime import emit
from tools.prompting import clip_text, compact_json

MAX_CRITIC_RETRIES = 1


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
        payload={"message": f"Reviewing analysis quality... (attempt {retries + 1}/2)"}
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
                    "- key statistics are missing (for example aggregate ran but value_stats is absent)\n"
                    "- the analysis does not address the research question\n\n"
                    "If you reject, give feedback that can be addressed by re-synthesizing the same evidence only. "
                    "Do not ask for new retrieval.\n\n"
                    "APPROVE if the analysis is substantive and accurately represents the data, "
                    "even if findings are sparse."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Research query: {clip_text(state['query'], 1200)}\n"
                    f"Findings count: {len(findings)}\n"
                    f"Analysis result: {compact_json(analysis, max_chars=14000)}"
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
            "max_retries": MAX_CRITIC_RETRIES,
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
    if state.get("approved", False) or state.get("critic_retries", 0) >= MAX_CRITIC_RETRIES:
        return "visualizer"
    return "analyst"
