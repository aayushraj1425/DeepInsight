from pydantic import BaseModel, Field
from agents.state import AgentState
from events import AgentEvent
from runtime import emit
from llm import client


class ResearchPlan(BaseModel):
    canonical_question: str = Field(
        description="The user's input rephrased as a single, precise academic research question"
    )
    subqueries: list[str] = Field(
        description="2-3 focused Semantic Scholar search strings derived from the canonical question",
        min_length=2,
        max_length=3,
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
                    "You turn user input into precise academic search queries for Semantic Scholar.\n\n"
                    "Step 1 — Interpret: If the input is keywords or a short phrase, expand it into a "
                    "full academic research question (e.g. 'sleep memory' → "
                    "'What is the effect of sleep deprivation on memory consolidation?').\n\n"
                    "Step 2 — Scope check: Semantic Scholar indexes peer-reviewed papers. "
                    "If the topic has little academic literature (job listings, industry trends, "
                    "pop-culture topics), reframe toward the closest empirical research angle "
                    "(e.g. 'swe roles 2025' → 'skill requirements and role evolution in software engineering').\n\n"
                    "Step 3 — Decompose: Generate exactly 2-3 short, precise search strings "
                    "covering different empirical angles. Use academic terminology. "
                    "Keep each query under 8 words."
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
