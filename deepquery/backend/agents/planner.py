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
        description=(
            "3-4 search strings covering different angles: "
            "2 short academic queries (Semantic Scholar style) + 1-2 natural-language web queries "
            "targeting industry reports, practitioner articles, or statistics sites"
        ),
        min_length=3,
        max_length=4,
    )
    fallback_queries: list[str] = Field(
        description=(
            "2-3 broader/rephrased fallback queries to use if primary subqueries return no results. "
            "These should be simpler, use synonyms, or approach the topic from a different angle."
        ),
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
                    "You decompose a research question into search queries and prepare fallback queries.\n\n"
                    "Step 1 — Interpret: Expand vague input into a precise question. "
                    "If ambiguous (could mean multiple things), cover each interpretation in the subqueries.\n\n"
                    "Step 2 — Primary subqueries (3-4 total):\n"
                    "  • 2 short academic queries (Semantic Scholar style, under 8 words, domain terminology)\n"
                    "  • 1-2 web/industry queries (natural language, targeting reports and statistics)\n\n"
                    "Step 3 — Fallback queries (2-3 total):\n"
                    "  • Broader, simpler, or rephrased versions of the primary queries\n"
                    "  • Use synonyms, remove qualifiers, or approach from a different empirical angle\n"
                    "  • These run automatically if the primary search returns nothing\n\n"
                    "Step 4 — Ensure queries cover: causes, effects, statistics, comparisons, mechanisms."
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
            "fallback_queries": plan.fallback_queries,
            "rationale": plan.rationale,
        }
    ))
    return {
        "subqueries": plan.subqueries,
        "fallback_queries": plan.fallback_queries,
    }
