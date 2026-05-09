from agents.state import AgentState
from events import AgentEvent
from runtime import emit
from tools.analysis import aggregate, compare, trend_analysis, triangulate_sources


async def analyst_node(state: AgentState) -> dict:
    sid = state["session_id"]
    findings = state.get("findings", [])
    retries = state.get("critic_retries", 0)
    feedback = state.get("critic_feedback", "")

    msg = f"Analyzing {len(findings)} findings..."
    if retries > 0 and feedback:
        msg = f"Retry {retries}/1 | Feedback: {feedback[:70]}"

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

    tools = ["aggregate", "compare_metric", "compare_source_type", "trend_analysis", "triangulate_sources"]
    analysis: dict = {
        "tools_used": tools,
        "reasoning": (
            "Ran deterministic descriptive analysis to avoid model-selected statistics. "
            "Trend and source-triangulation results are interpreted later with validation and fact-checking."
        ),
    }

    for tool in tools:
        await emit(sid, AgentEvent(
            type="tool_call", agent="analyst",
            payload={"tool": tool, "findings_count": len(findings)}
        ))
        if tool == "aggregate":
            analysis["aggregate"] = aggregate(findings)
        elif tool == "compare_metric":
            analysis["compare"] = compare(findings, "metric")
        elif tool == "compare_source_type":
            analysis["compare_by_source_type"] = compare(findings, "source_type")
        elif tool == "trend_analysis":
            analysis["trends"] = trend_analysis(findings)
        elif tool == "triangulate_sources":
            analysis["triangulation"] = triangulate_sources(findings)

    await emit(sid, AgentEvent(
        type="node_end", agent="analyst",
        payload={"tools_run": tools, "result_keys": list(analysis.keys())}
    ))
    return {"analysis": analysis}
