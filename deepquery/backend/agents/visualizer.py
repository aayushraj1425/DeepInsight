from typing import Literal

from pydantic import BaseModel, Field
from agents.state import AgentState
from events import AgentEvent
from llm import client
from runtime import emit
from viz.templates import bar_comparison, chartable_counts, forest_plot, timeline


ChartTemplate = Literal["forest_plot", "bar_comparison", "timeline"]


class ChartSelection(BaseModel):
    templates: list[ChartTemplate] = Field(
        description="One to three chart templates that best fit the available analysis and findings"
    )
    rationale: str = Field(description="One sentence explaining why these charts fit")


def _available_templates(findings: list[dict], analysis: dict) -> list[ChartTemplate]:
    counts = chartable_counts(findings, analysis)
    available: list[ChartTemplate] = []
    if counts["bar_comparison"] > 0:
        available.append("bar_comparison")
    if counts["timeline"] >= 2:
        available.append("timeline")
    if counts["forest_plot"] > 0:
        available.append("forest_plot")
    return available


def _build_chart(template: ChartTemplate, findings: list[dict], analysis: dict) -> dict:
    if template == "forest_plot":
        figure, insight = forest_plot(findings)
    elif template == "bar_comparison":
        figure, insight = bar_comparison(analysis.get("compare") or {})
    else:
        figure, insight = timeline(findings)

    return {
        "template": template,
        "title": figure.get("layout", {}).get("title", {}).get("text", template),
        "insight": insight,
        "figure": figure,
    }


async def visualizer_node(state: AgentState) -> dict:
    sid = state["session_id"]
    findings = state.get("findings", [])
    analysis = state.get("analysis", {})

    await emit(sid, AgentEvent(
        type="node_start", agent="visualizer",
        payload={"message": "Selecting chart template and rendering..."}
    ))

    available = _available_templates(findings, analysis)
    if not available:
        await emit(sid, AgentEvent(
            type="chart_ready", agent="visualizer",
            payload={
                "charts": 0,
                "chart_specs": [],
                "message": "No chartable numeric data found",
            }
        ))
        await emit(sid, AgentEvent(
            type="node_end", agent="visualizer",
            payload={"chart_count": 0}
        ))
        return {"chart_specs": []}

    selection: ChartSelection = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "Pick the most useful Plotly chart templates for a research analysis dashboard. "
                    "Only choose from the provided available templates. Prefer comparison charts when "
                    "grouped analysis exists, timelines when publication years exist, and forest plots "
                    "when per-study estimates are the clearest evidence."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Research query: {state['query']}\n"
                    f"Available templates: {available}\n"
                    f"Chartable counts: {chartable_counts(findings, analysis)}\n"
                    f"Analysis keys: {list(analysis.keys())}\n"
                    f"Sample findings: {findings[:5]}"
                ),
            },
        ],
        response_model=ChartSelection,
    )

    chosen: list[ChartTemplate] = []
    for template in selection.templates:
        if template in available and template not in chosen:
            chosen.append(template)
    if not chosen:
        chosen = available[:2]

    chart_specs: list[dict] = []
    for template in chosen[:3]:
        try:
            chart_specs.append(_build_chart(template, findings, analysis))
        except ValueError:
            continue

    await emit(sid, AgentEvent(
        type="chart_ready", agent="visualizer",
        payload={
            "charts": len(chart_specs),
            "chart_specs": chart_specs,
            "rationale": selection.rationale,
            "message": f"Rendered {len(chart_specs)} chart(s)",
        }
    ))
    await emit(sid, AgentEvent(
        type="node_end", agent="visualizer",
        payload={"chart_count": len(chart_specs)}
    ))
    return {"chart_specs": chart_specs}
