from pydantic import BaseModel, ConfigDict, Field

from agents.state import AgentState
from events import AgentEvent
from llm import client
from runtime import emit
from tools.prompting import clip_text, compact_json


class Scenario(BaseModel):
    name: str = Field(description="Scenario label, e.g. baseline, upside, downside")
    directional_outcome: str = Field(description="Qualitative outcome without arbitrary invented percentages")
    assumptions: list[str] = Field(description="Explicit assumptions grounded in evidence")
    evidence_basis: list[str] = Field(description="Source titles or analysis outputs supporting assumptions")
    risks_to_scenario: list[str] = Field(description="What could make this scenario wrong")
    confidence: str = Field(description="low, medium, or high")


class EconomicModel(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    model_type: str = Field(description="Modeling approach used")
    why_not_naive: str = Field(description="Why the model avoids simplistic productivity-to-job-loss math")
    key_drivers: list[str] = Field(description="Variables that govern the outcome")
    scenarios: list[Scenario] = Field(description="Optimistic, realistic/base, and pessimistic scenarios")
    leading_indicators_to_watch: list[str] = Field(description="Observable signals users should monitor")
    quantitative_limits: list[str] = Field(description="Why precise forecasts are limited or what data is missing")


def _fallback_model(state: AgentState) -> dict:
    return {
        "model_type": "qualitative scenario model with evidence constraints",
        "why_not_naive": "Productivity improvements can reduce task demand, expand markets, change skill mix, or all three; job effects cannot be inferred by direct arithmetic.",
        "key_drivers": [
            "AI adoption speed",
            "software demand growth",
            "macro financing conditions",
            "skill substitution versus augmentation",
            "new AI-native product creation",
        ],
        "scenarios": [
            {
                "name": "Base case",
                "directional_outcome": "Role composition changes more than the occupation disappears.",
                "assumptions": ["Software demand remains material", "AI automates tasks unevenly"],
                "evidence_basis": ["Validated source and trend analysis"],
                "risks_to_scenario": ["Rapid autonomous-agent substitution could compress entry-level hiring faster than historical analogies imply."],
                "confidence": "medium",
            }
        ],
        "leading_indicators_to_watch": ["BLS software-related employment", "entry-level job postings", "AI-tool adoption surveys", "tech layoff reasons", "interest-rate cycle"],
        "quantitative_limits": ["No precise forecast should be reported without a validated forecasting dataset and transparent assumptions."],
    }


async def economist_node(state: AgentState) -> dict:
    sid = state["session_id"]
    await emit(sid, AgentEvent(
        type="node_start",
        agent="economist",
        payload={"message": "Building cautious scenarios instead of unsupported projections..."},
    ))

    try:
        result: EconomicModel = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a labor economist and market strategist. Build grounded scenario analysis. "
                        "Never invent percentages or precise forecasts. If using a number, it must come from the provided "
                        "evidence or analysis. Explain assumptions, causal mechanisms, and uncertainty. Acknowledge that "
                        "higher productivity can either displace labor or expand demand depending on market elasticity."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Research question: {clip_text(state['query'], 1200)}\n"
                        f"Deep reasoning: {compact_json(state.get('reasoning', {}), max_chars=12000)}\n"
                        f"Analysis: {compact_json(state.get('analysis', {}), max_chars=14000)}\n"
                        f"Validation report: {compact_json(state.get('validation_report', {}), max_chars=9000)}\n"
                        f"Research plan scenario axes: {compact_json((state.get('research_plan', {}) or {}).get('scenario_axes', []), max_chars=3000)}"
                    ),
                },
            ],
            response_model=EconomicModel,
        )
        model = result.model_dump()
    except Exception:
        model = _fallback_model(state)

    await emit(sid, AgentEvent(
        type="model_ready",
        agent="economist",
        payload={
            "message": "Scenario model ready",
            "scenario_count": len(model.get("scenarios", [])),
            "model_type": model.get("model_type", ""),
        },
    ))
    await emit(sid, AgentEvent(
        type="node_end",
        agent="economist",
        payload={"scenario_count": len(model.get("scenarios", []))},
    ))
    return {"economic_model": model}
