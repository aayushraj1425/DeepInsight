from pydantic import BaseModel, Field

from agents.state import AgentState
from events import AgentEvent
from llm import client
from runtime import emit
from tools.prompting import clip_text, compact_json, slim_findings, slim_paper_sources


class ReasonedInsight(BaseModel):
    claim: str = Field(description="Evidence-backed insight, with no unsupported number")
    evidence_titles: list[str] = Field(description="Source titles supporting this insight")
    causal_logic: str = Field(description="Why the evidence supports this interpretation")
    confidence: str = Field(description="low, medium, or high")


class DeepReasoning(BaseModel):
    core_thesis: str = Field(description="Nuanced answer in one or two sentences")
    causal_chain: list[str] = Field(description="Mechanism-level reasoning steps")
    key_insights: list[ReasonedInsight] = Field(description="Most important synthesized insights")
    contradictory_evidence: list[str] = Field(description="Important disagreements or alternative explanations")
    historical_comparisons: list[str] = Field(description="Relevant comparisons to past technology shifts")
    evidence_gaps: list[str] = Field(description="Missing data or unresolved uncertainty")
    confidence_summary: str = Field(description="Plain-English confidence assessment")


def _fallback_reasoning(state: AgentState) -> dict:
    validation = state.get("validation_report", {})
    return {
        "core_thesis": "The evidence supports a cautious, multi-causal interpretation rather than a single-factor conclusion.",
        "causal_chain": [
            "Separate historical baseline trends from the focal intervention.",
            "Compare primary data against academic papers and tracker/survey evidence.",
            "Treat weak or stale sources as directional rather than definitive.",
        ],
        "key_insights": [
            {
                "claim": "The strongest claims should be grounded in validated primary datasets and corroborated by research papers.",
                "evidence_titles": ["Source validation report"],
                "causal_logic": "Primary data is less vulnerable to survey selection and vendor incentives.",
                "confidence": "medium" if validation.get("primary_source_count", 0) else "low",
            }
        ],
        "contradictory_evidence": ["Contradictions could not be fully adjudicated because synthesis model fallback was used."],
        "historical_comparisons": ["Automation often changes task composition before it changes net employment."],
        "evidence_gaps": ["More primary datasets and recent labor-market indicators would improve confidence."],
        "confidence_summary": "Moderate to low until major claims are checked against multiple independent sources.",
    }


async def reasoner_node(state: AgentState) -> dict:
    sid = state["session_id"]
    await emit(sid, AgentEvent(
        type="node_start",
        agent="reasoner",
        payload={"message": "Synthesizing causal mechanisms, contradictions, and second-order effects..."},
    ))

    try:
        result: DeepReasoning = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a senior intelligence analyst and labor/economic reasoning specialist. "
                        "Synthesize evidence without sensationalism. Every insight must name supporting source titles. "
                        "Only create an insight when at least one provided dataset, paper, report, or uploaded file supports it. "
                        "If the evidence is directional or weak, say so in confidence and causal_logic. "
                        "Do not invent numbers, projections, or citations. Separate correlation from causation, compare "
                        "contradictory evidence, and state uncertainty clearly."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Research question: {clip_text(state['query'], 1200)}\n"
                        f"Research plan: {compact_json(state.get('research_plan', {}), max_chars=7000)}\n"
                        f"Validated source summary: {compact_json(state.get('validation_report', {}), max_chars=10000)}\n"
                        f"Paper sources with abstract snippets: {compact_json(slim_paper_sources(state.get('paper_sources', []), limit=10, include_abstract=True), max_chars=12000)}\n"
                        f"Representative findings: {compact_json(slim_findings(state.get('findings', []), limit=18), max_chars=14000)}\n"
                        f"Analysis: {compact_json(state.get('analysis', {}), max_chars=14000)}"
                    ),
                },
            ],
            response_model=DeepReasoning,
        )
        reasoning = result.model_dump()
    except Exception:
        reasoning = _fallback_reasoning(state)

    await emit(sid, AgentEvent(
        type="reasoning_ready",
        agent="reasoner",
        payload={
            "message": "Deep reasoning synthesis complete",
            "core_thesis": reasoning.get("core_thesis", ""),
            "confidence_summary": reasoning.get("confidence_summary", ""),
            "insight_count": len(reasoning.get("key_insights", [])),
        },
    ))
    await emit(sid, AgentEvent(
        type="node_end",
        agent="reasoner",
        payload={"insight_count": len(reasoning.get("key_insights", []))},
    ))
    return {"reasoning": reasoning}
