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
                    "Write a clear, evidence-grounded markdown research report from structured "
                    "academic findings and analysis. Be concise. Do not invent citations or claims. "
                    "Call out limitations when findings are sparse, contradictory, or extracted from abstracts only."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Research question: {state['query']}\n"
                    f"Approved by critic: {state.get('approved')}\n"
                    f"Critic feedback: {state.get('critic_feedback') or 'none'}\n"
                    f"Findings: {state.get('findings', [])[:12]}\n"
                    f"Analysis: {state.get('analysis', {})}\n"
                    f"Charts: {chart_summaries}"
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
