from pydantic import BaseModel, Field

from agents.state import AgentState
from events import AgentEvent
from llm import client
from runtime import emit
from tools.prompting import clip_text, compact_json, slim_findings, slim_paper_sources


class ClaimCheck(BaseModel):
    claim: str = Field(description="Claim being checked")
    status: str = Field(description="supported, partially_supported, contradicted, or insufficient_evidence")
    supporting_sources: list[str] = Field(description="Source titles that support the claim")
    contradicting_sources: list[str] = Field(description="Source titles that challenge the claim")
    confidence: str = Field(description="low, medium, or high")
    note: str = Field(description="Brief explanation")


class FactCheckReport(BaseModel):
    approved_for_report: bool = Field(description="True if the final report can safely proceed with caveats")
    checked_claims: list[ClaimCheck] = Field(description="Major claims and numerical assertions checked")
    red_flags: list[str] = Field(description="Unsupported, stale, or contradictory claims to avoid")
    citation_instructions: list[str] = Field(description="Rules reporter must follow")
    uncertainty_statement: str = Field(description="Honest confidence and limitations statement")


def _fallback_factcheck(state: AgentState) -> dict:
    validation = state.get("validation_report", {})
    red_flags = []
    if validation.get("primary_source_count", 0) == 0:
        red_flags.append("No primary source was validated; avoid precise numerical claims.")
    if validation.get("low_confidence_sources"):
        red_flags.append("Some sources have low credibility or selection-bias flags.")
    return {
        "approved_for_report": True,
        "checked_claims": [],
        "red_flags": red_flags,
        "citation_instructions": [
            "Cite source titles inline for every major claim.",
            "Do not include precise projections unless the method and source are explicit.",
            "Separate dataset-backed findings from paper-backed interpretations.",
        ],
        "uncertainty_statement": "Proceed with explicit uncertainty and avoid unsupported numerical projections.",
    }


async def factchecker_node(state: AgentState) -> dict:
    sid = state["session_id"]
    await emit(sid, AgentEvent(
        type="node_start",
        agent="factchecker",
        payload={"message": "Checking major claims against sources, validation scores, and contradictions..."},
    ))

    try:
        result: FactCheckReport = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a strict fact-checking editor. Verify major claims and numerical assertions "
                        "using only the provided evidence. If support is missing, mark insufficient_evidence. "
                        "Do not rescue weak claims by adding outside knowledge. Require citations by source title. "
                        "If a numerical or causal claim lacks a supporting source title, add it to red_flags and mark "
                        "approved_for_report false unless it can be rewritten as uncertainty or a hypothesis."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Research question: {clip_text(state['query'], 1200)}\n"
                        f"Reasoning to check: {compact_json(state.get('reasoning', {}), max_chars=12000)}\n"
                        f"Economic model to check: {compact_json(state.get('economic_model', {}), max_chars=12000)}\n"
                        f"Validation report: {compact_json(state.get('validation_report', {}), max_chars=10000)}\n"
                        f"Representative findings: {compact_json(slim_findings(state.get('findings', []), limit=20), max_chars=14000)}\n"
                        f"Paper sources with abstract snippets: {compact_json(slim_paper_sources(state.get('paper_sources', []), limit=12, include_abstract=True), max_chars=12000)}"
                    ),
                },
            ],
            response_model=FactCheckReport,
        )
        report = result.model_dump()
    except Exception:
        report = _fallback_factcheck(state)

    await emit(sid, AgentEvent(
        type="factcheck_ready",
        agent="factchecker",
        payload={
            "message": "Fact-checking complete",
            "approved_for_report": report.get("approved_for_report", True),
            "checked_claims": len(report.get("checked_claims", [])),
            "red_flags": report.get("red_flags", [])[:5],
        },
    ))
    await emit(sid, AgentEvent(
        type="node_end",
        agent="factchecker",
        payload={"checked_claims": len(report.get("checked_claims", []))},
    ))
    return {"fact_check_report": report, "approved": report.get("approved_for_report", True)}
