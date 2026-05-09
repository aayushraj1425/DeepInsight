from pydantic import BaseModel, Field
from agents.state import AgentState
from events import AgentEvent
from runtime import emit
from llm import client


class ResearchPlan(BaseModel):
    subqueries: list[str] = Field(
        description="2-4 precise Semantic Scholar search queries derived from the research question",
        min_length=2,
        max_length=4,
    )
    rationale: str = Field(description="One sentence explaining the decomposition strategy")


async def planner_node(state: AgentState) -> dict:
    sid = state["session_id"]
    await emit(sid, AgentEvent(
        type="node_start", agent="planner",
        payload={"message": f"Decomposing: {state['query'][:80]}"}
    ))

    plan: ResearchPlan = await client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": (
                    "You decompose a research question into 2-4 focused academic search queries "
                    "suitable for Semantic Scholar. Use precise domain terminology. "
                    "Each query should target a different angle of the question."
                ),
            },
            {"role": "user", "content": f"Research question: {state['query']}"},
        ],
        response_model=ResearchPlan,
    )

    await emit(sid, AgentEvent(
        type="node_end", agent="planner",
        payload={"subqueries": plan.subqueries, "rationale": plan.rationale}
    ))
    return {"subqueries": plan.subqueries}
