from pydantic import BaseModel, Field

from agents.state import AgentState
from events import AgentEvent
from llm import client
from runtime import emit
from tools.prompting import clip_text, compact_json


class ResearchSubproblem(BaseModel):
    name: str = Field(description="Short label for the research subproblem")
    why_it_matters: str = Field(description="Why this subproblem is needed for a trustworthy answer")
    search_queries: list[str] = Field(description="Focused search queries for this subproblem")
    needed_sources: list[str] = Field(description="Specific source types or institutions to look for")
    validation_checks: list[str] = Field(description="Checks needed before trusting evidence")


class IntelligencePlan(BaseModel):
    research_brief: str = Field(description="Concise framing of the investigation")
    question_type: str = Field(description="The kind of research task, e.g. labor economics, market intelligence")
    subproblems: list[ResearchSubproblem] = Field(description="Three to seven investigation branches")
    subqueries: list[str] = Field(description="Four to six high-value search queries")
    source_priorities: list[str] = Field(description="Primary sources and trusted reports to prefer")
    dataset_targets: list[str] = Field(description="Datasets or indicators that would materially improve the answer")
    fact_checks: list[str] = Field(description="Claims or numbers that must be verified before reporting")
    scenario_axes: list[str] = Field(description="Variables that should drive scenario analysis")
    forbidden_shortcuts: list[str] = Field(description="Reasoning shortcuts the system must avoid")


def _fallback_plan(query: str, document_brief: str) -> dict:
    labor = any(term in query.lower() for term in ["job", "jobs", "labor", "employment", "hiring", "layoff", "software", "engineer"])
    if labor:
        subqueries = [
            f"{query} labor market evidence software developers",
            "software developer employment trends BLS AI coding tools",
            "AI coding assistants developer productivity empirical study",
            "technology layoffs interest rates overhiring AI automation",
            "junior software engineer hiring trends AI",
        ]
        source_priorities = [
            "BLS labor data",
            "FRED macro indicators",
            "Stanford AI Index",
            "peer-reviewed AI productivity studies",
            "Stack Overflow Developer Survey",
            "GitHub Octoverse",
            "Layoffs.fyi or company layoff filings with caution",
        ]
        dataset_targets = [
            "BLS software developer and software industry employment",
            "FRED interest-rate and unemployment series",
            "AI adoption and developer survey datasets",
            "tech layoff trackers",
        ]
    else:
        subqueries = [
            query,
            f"{query} systematic review evidence",
            f"{query} datasets trends statistics",
            f"{query} contradictory evidence limitations",
        ]
        source_priorities = ["government data", "academic papers", "industry reports", "public datasets"]
        dataset_targets = ["trusted public datasets relevant to the research question"]

    return {
        "research_brief": f"Investigate '{query}' using primary data, scholarly evidence, and explicit uncertainty.",
        "question_type": "labor economics / market intelligence" if labor else "general research intelligence",
        "subproblems": [
            {
                "name": "Historical baseline",
                "why_it_matters": "Avoid attributing normal cycles or pre-existing trends to the focal cause.",
                "search_queries": subqueries[:2],
                "needed_sources": source_priorities[:3],
                "validation_checks": ["Check latest available year", "Prefer primary time series"],
            },
            {
                "name": "Mechanism and causality",
                "why_it_matters": "Separate correlation, macro shocks, productivity effects, and substitution effects.",
                "search_queries": subqueries[2:4],
                "needed_sources": source_priorities,
                "validation_checks": ["Look for alternative explanations", "Flag survey or vendor bias"],
            },
        ],
        "subqueries": subqueries[:6],
        "source_priorities": source_priorities,
        "dataset_targets": dataset_targets,
        "fact_checks": [
            "Do not report numerical projections unless tied to a named source or transparent model.",
            "Check whether layoffs are attributable to AI or to macro/post-pandemic correction.",
            "Compare automation-displacement claims against augmentation and demand-expansion evidence.",
        ],
        "scenario_axes": ["AI adoption speed", "software demand growth", "interest-rate environment", "skill substitution vs augmentation"],
        "forbidden_shortcuts": [
            "Do not convert productivity gains directly into job losses.",
            "Do not treat news anecdotes as representative labor-market data.",
            "Do not cite stale surveys as current labor-market facts without caveats.",
        ],
        "document_context_used": bool(document_brief),
    }


async def orchestrator_node(state: AgentState) -> dict:
    sid = state["session_id"]
    document_brief = clip_text(state.get("document_brief") or "", 3500)

    await emit(sid, AgentEvent(
        type="node_start",
        agent="orchestrator",
        payload={"message": "Planning an evidence-first intelligence investigation..."},
    ))

    try:
        plan: IntelligencePlan = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are the chief research orchestrator for an autonomous intelligence system. "
                        "Break the user's question into a rigorous research plan. Prefer primary data, "
                        "government sources, academic evidence, and clearly testable claims. The plan must "
                        "explicitly prevent shallow causal reasoning, unsupported projections, and single-source answers."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Research question: {clip_text(state['query'], 1200)}\n\n"
                        f"Uploaded document context, if any:\n{document_brief or 'none'}"
                    ),
                },
            ],
            response_model=IntelligencePlan,
        )
        research_plan = plan.model_dump()
    except Exception:
        research_plan = _fallback_plan(state["query"], document_brief)

    subqueries = [
        clip_text(query, 180)
        for query in research_plan.get("subqueries", [])
        if str(query).strip()
    ][:6]
    if not subqueries:
        subqueries = _fallback_plan(state["query"], document_brief)["subqueries"][:4]

    await emit(sid, AgentEvent(
        type="plan_ready",
        agent="orchestrator",
        payload={
            "message": f"Research plan created with {len(research_plan.get('subproblems', []))} branches",
            "subqueries": subqueries,
            "source_priorities": research_plan.get("source_priorities", []),
            "dataset_targets": research_plan.get("dataset_targets", []),
        },
    ))
    await emit(sid, AgentEvent(
        type="node_end",
        agent="orchestrator",
        payload={"subqueries": subqueries, "plan": compact_json(research_plan, max_chars=6000)},
    ))

    return {"research_plan": research_plan, "subqueries": subqueries}
