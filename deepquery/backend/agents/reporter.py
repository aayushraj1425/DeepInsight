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
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": (
                    "Write a markdown research report strictly from the provided findings.\n\n"
                    "STRICT RULES — violating any of these makes the report worse, not better:\n"
                    "1. ONLY use numbers that appear in the findings list. Never invent, estimate, or infer numbers.\n"
                    "2. Every bullet in ## Key Findings must cite a number from the findings AND name its source (paper title or URL).\n"
                    "   Format: **[metric]**: [value] — [source title], [year if available]\n"
                    "3. If fewer than 3 numeric findings exist, write a short ## Data Quality note explaining "
                    "   that quantitative evidence was limited for this query, and list what was found honestly.\n"
                    "4. Use ## Bottom line for a 1-2 sentence summary using only numbers from the findings.\n"
                    "5. Use ## Key Findings for the bullet list (only as many bullets as real findings support).\n"
                    "6. Use ## Evidence for interpretation — only reference trends visible in the actual data.\n"
                    "7. Use ## Limitations to flag sparse data, web-only sources, or missing peer review.\n"
                    "8. If the findings are from web articles (not academic papers), note this explicitly."
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
