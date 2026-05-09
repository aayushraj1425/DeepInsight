from pydantic import BaseModel, Field
from agents.state import AgentState
from events import AgentEvent
from llm import client
from runtime import emit


class ResearchReport(BaseModel):
    markdown: str = Field(description="Concise markdown research report for the user")


async def reporter_node(state: AgentState) -> dict:
    sid = state["session_id"]
    chart_summaries = [
        {
            "template": chart.get("template"),
            "title": chart.get("title"),
            "insight": chart.get("insight"),
        }
        for chart in state.get("chart_specs", [])
    ]

    await emit(sid, AgentEvent(
        type="node_start", agent="reporter",
        payload={"message": "Generating markdown research report..."}
    ))

    result: ResearchReport = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "Write a data-rich markdown research report from structured academic findings and analysis.\n\n"
                    "RULES:\n"
                    "1. Every bullet point MUST contain at least one specific number from the findings "
                    "(e.g. '18.5% reaction-time slowing', 'mean score −9.2', 'n=45 participants'). "
                    "No qualitative-only bullets.\n"
                    "2. Format each bullet as: **[metric or finding]**: [value with unit] — [brief context "
                    "(intervention, year, or sample size if available)].\n"
                    "3. Use ## Bottom line for a 1-2 sentence quantitative summary with the most striking number.\n"
                    "4. Use ## Key Findings for the bullet list (4-6 bullets, each with a number).\n"
                    "5. Use ## Evidence for a short paragraph interpreting the pattern across findings.\n"
                    "6. Use ## Limitations for caveats about data quality.\n"
                    "7. Do not invent numbers. Only use values present in the findings or analysis."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Research question: {state['query']}\n"
                    f"Approved by critic: {state.get('approved')}\n"
                    f"Critic feedback: {state.get('critic_feedback') or 'none'}\n"
                    f"Findings (with numeric values, interventions, years): {state.get('findings', [])[:12]}\n"
                    f"Analysis (aggregate stats, comparisons): {state.get('analysis', {})}\n"
                    f"Chart insights: {chart_summaries}"
                ),
            },
        ],
        response_model=ResearchReport,
    )

    report = result.markdown
    await emit(sid, AgentEvent(
        type="report_ready", agent="reporter",
        payload={"length": len(report), "report": report, "message": "Report ready"}
    ))
    await emit(sid, AgentEvent(
        type="node_end", agent="reporter",
        payload={}
    ))
    return {"report": report}
