from pydantic import BaseModel, Field
from agents.state import AgentState
from events import AgentEvent
from runtime import emit
from llm import client
from tools.prompting import clip_text


class ResearchPlan(BaseModel):
    direct_query: str = Field(description="A direct academic query based on the user's request")
    expanded_query: str = Field(description="A terminology-expanded query using related academic vocabulary")
    related_query: str = Field(description="A query covering a related topic, method, or comparative angle")
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
                    "suitable for Semantic Scholar. Return exactly three queries: "
                    "one direct query, one terminology-expanded query, and one related topic or method query. "
                    "Use precise domain terminology and reflect any useful details from uploaded materials."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Research question: {state['query']}\n\n"
                    f"Uploaded material brief:\n{clip_text(state.get('document_brief') or 'none', 3500)}"
                ),
            },
        ],
        response_model=ResearchPlan,
    )

    subqueries = [plan.direct_query, plan.expanded_query, plan.related_query]

    await emit(sid, AgentEvent(
        type="node_end", agent="planner",
        payload={"subqueries": subqueries, "rationale": plan.rationale}
    ))
    return {"subqueries": subqueries}
