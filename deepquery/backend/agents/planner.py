from pydantic import BaseModel, Field
from agents.state import AgentState
from events import AgentEvent
from runtime import emit
from llm import client


class ResearchPlan(BaseModel):
    canonical_question: str = Field(
        description="The user's input rephrased as a single, precise research question"
    )
    subqueries: list[str] = Field(
        description="3-4 search strings: 2 academic (Semantic Scholar) + 1-2 web-optimized for industry/practitioner sources",
        min_length=3,
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
                    "You decompose a research question into a mix of academic and web search strings.\n\n"
                    "Step 1 — Interpret: Expand keywords into a precise research question.\n\n"
                    "Step 2 — Generate 3-4 subqueries covering different angles:\n"
                    "  • 2 academic queries (short, precise, Semantic Scholar style, under 8 words each). "
                    "Use domain terminology from medicine, psychology, economics, CS, etc.\n"
                    "  • 1-2 web/industry queries (natural language, broader — targeting reports, "
                    "industry analyses, practitioner articles, and statistics sites). "
                    "These are especially important for topics like job market trends, business strategy, "
                    "technology adoption, or current events that have little peer-reviewed coverage.\n\n"
                    "Step 3 — Ensure the subqueries cover different facets: causes, effects, "
                    "interventions, statistics, comparisons, or mechanisms."
                ),
            },
            {"role": "user", "content": state["query"]},
        ],
        response_model=ResearchPlan,
    )

    await emit(sid, AgentEvent(
        type="node_end", agent="planner",
        payload={
            "canonical_question": plan.canonical_question,
            "subqueries": plan.subqueries,
            "rationale": plan.rationale,
        }
    ))
    return {"subqueries": plan.subqueries}
