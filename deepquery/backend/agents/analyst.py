from typing import Literal
from pydantic import BaseModel, Field
from agents.state import AgentState
from events import AgentEvent
from runtime import emit
from llm import client
from tools.analysis import aggregate, compare, correlate


class ToolSelection(BaseModel):
    tools: list[Literal["aggregate", "compare", "correlate"]] = Field(
        description="Which tools to run. Always include aggregate. Add compare/correlate when data supports it."
    )
    compare_group_by: str = Field("metric", description="Field to group by for compare (usually 'metric' or 'intervention')")
    correlate_metric_a: str = Field("", description="First metric name for correlate tool")
    correlate_metric_b: str = Field("", description="Second metric name for correlate tool")
    reasoning: str = Field(description="Why these tools fit the available data")


async def analyst_node(state: AgentState) -> dict:
    sid = state["session_id"]
    findings = state.get("findings", [])
    retries = state.get("critic_retries", 0)
    feedback = state.get("critic_feedback", "")

    msg = f"Analyzing {len(findings)} findings..."
    if retries > 0 and feedback:
        msg = f"Retry {retries}/2 — Critic: {feedback[:70]}"

    await emit(sid, AgentEvent(
        type="node_start", agent="analyst",
        payload={"message": msg, "findings_count": len(findings), "retry": retries}
    ))

    if not findings:
        await emit(sid, AgentEvent(
            type="node_end", agent="analyst",
            payload={"error": "no findings to analyze"}
        ))
        return {"analysis": {"error": "no findings", "total_findings": 0}}

    selection: ToolSelection = await client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": (
                    "Choose statistical analysis tools for a set of research findings. "
                    "Always run aggregate. Add compare if multiple metrics/interventions exist. "
                    "Add correlate only if two specific numeric metrics can be paired."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Research query: {state['query']}\n"
                    f"Total findings: {len(findings)}\n"
                    f"Sample findings: {findings[:4]}\n"
                    f"Critic feedback to address: {feedback or 'none'}"
                ),
            },
        ],
        response_model=ToolSelection,
    )

    analysis: dict = {"tools_used": selection.tools, "reasoning": selection.reasoning}

    for tool in selection.tools:
        await emit(sid, AgentEvent(
            type="tool_call", agent="analyst",
            payload={"tool": tool, "findings_count": len(findings)}
        ))
        if tool == "aggregate":
            analysis["aggregate"] = aggregate(findings)
        elif tool == "compare":
            analysis["compare"] = compare(findings, selection.compare_group_by)
        elif tool == "correlate" and selection.correlate_metric_a and selection.correlate_metric_b:
            analysis["correlate"] = correlate(
                findings, selection.correlate_metric_a, selection.correlate_metric_b
            )

    await emit(sid, AgentEvent(
        type="node_end", agent="analyst",
        payload={"tools_run": selection.tools, "result_keys": list(analysis.keys())}
    ))
    return {"analysis": analysis}
