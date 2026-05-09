from dataclasses import dataclass

from agents.state import AgentState
from events import AgentEvent
from runtime import emit
from viz.templates import (
    chartable_counts,
    claim_support_status,
    evidence_quality,
    scenario_matrix,
    source_mix,
    trend_change_summary,
    trend_series,
)


ChartTemplate = str


@dataclass
class ChartCandidate:
    template: ChartTemplate
    score: float
    argument_role: str
    reason: str


def _available_templates(
    findings: list[dict],
    analysis: dict,
    validation_report: dict,
    economic_model: dict,
    fact_check_report: dict,
) -> list[ChartTemplate]:
    counts = chartable_counts(findings, analysis, validation_report, economic_model)
    available: list[ChartTemplate] = []
    if counts["trend_change_summary"] > 0:
        available.append("trend_change_summary")
    if counts["trend_series"] >= 4:
        available.append("trend_series")
    if fact_check_report.get("checked_claims"):
        available.append("claim_support_status")
    if counts["scenario_matrix"] > 0:
        available.append("scenario_matrix")
    if counts["evidence_quality"] > 0:
        available.append("evidence_quality")
    if counts["source_mix"] > 0:
        available.append("source_mix")
    return available


def _build_chart(
    candidate: ChartCandidate,
    findings: list[dict],
    analysis: dict,
    validation_report: dict,
    economic_model: dict,
    fact_check_report: dict,
) -> dict:
    template = candidate.template
    if template == "trend_change_summary":
        figure, insight = trend_change_summary(analysis)
    elif template == "trend_series":
        figure, insight = trend_series(findings)
    elif template == "claim_support_status":
        figure, insight = claim_support_status(fact_check_report)
    elif template == "evidence_quality":
        figure, insight = evidence_quality(validation_report)
    elif template == "scenario_matrix":
        figure, insight = scenario_matrix(economic_model)
    else:
        figure, insight = source_mix(findings)

    metadata = _chart_metadata(template, findings, analysis, validation_report, economic_model, fact_check_report)

    return {
        "template": template,
        "title": figure.get("layout", {}).get("title", {}).get("text", template),
        "insight": insight,
        "argument_role": candidate.argument_role,
        "selection_reason": candidate.reason,
        "impact_score": round(candidate.score, 2),
        "explanation": metadata["explanation"],
        "source_titles": metadata["source_titles"],
        "caveat": metadata["caveat"],
        "confidence": metadata["confidence"],
        "figure": figure,
    }


def _unique_titles(items: list[str], limit: int = 5) -> list[str]:
    seen: set[str] = set()
    titles: list[str] = []
    for item in items:
        title = str(item or "").strip()
        if not title or title in seen:
            continue
        seen.add(title)
        titles.append(title)
        if len(titles) >= limit:
            break
    return titles


def _chart_metadata(
    template: ChartTemplate,
    findings: list[dict],
    analysis: dict,
    validation_report: dict,
    economic_model: dict,
    fact_check_report: dict,
) -> dict:
    if template == "trend_change_summary":
        source_titles = _unique_titles([
            trend.get("source_title") or trend.get("metric") or ""
            for trend in ((analysis.get("trends") or {}).get("trends") or [])
        ])
        return {
            "explanation": (
                "Shows which loaded indicators changed the most over their available historical window. "
                "This is usually the strongest chart for grounding an argument in observed data."
            ),
            "source_titles": source_titles,
            "caveat": "Trend magnitude does not prove causation; use it to establish context and direction.",
            "confidence": "High for computed historical change when based on primary time-series data.",
        }

    if template == "trend_series":
        source_titles = _unique_titles([
            finding.get("source_title") or finding.get("paper_title") or ""
            for finding in findings
            if finding.get("series_id")
        ])
        return {
            "explanation": (
                "Compares trusted public time series after indexing each series to 100 in its first observed year. "
                "This keeps units separate while showing direction and relative change."
            ),
            "source_titles": source_titles,
            "caveat": "Indexed lines show movement, not absolute job counts or causal proof.",
            "confidence": "High for the displayed historical values; medium for causal interpretation.",
        }

    if template == "evidence_quality":
        source_titles = _unique_titles([
            row.get("title") or row.get("provider") or ""
            for row in (validation_report.get("source_scores") or [])
        ])
        return {
            "explanation": (
                "Shows how much trust to place in the evidence base using provider credibility, freshness, "
                "and methodology-risk flags."
            ),
            "source_titles": source_titles,
            "caveat": "Credibility scores are a transparent heuristic, not an external rating agency score.",
            "confidence": "Medium; useful for prioritizing evidence, not for proving claims by itself.",
        }

    if template == "claim_support_status":
        source_titles = _unique_titles([
            source
            for claim in (fact_check_report.get("checked_claims") or [])
            for source in (claim.get("supporting_sources") or [])
        ])
        return {
            "explanation": (
                "Shows whether the report's major claims are supported, partial, contradicted, or insufficiently evidenced."
            ),
            "source_titles": source_titles,
            "caveat": "This depends on extracted evidence quality; unsupported claims should be rewritten or excluded.",
            "confidence": "Medium to high when claims were checked against multiple source types.",
        }

    if template == "scenario_matrix":
        source_titles = _unique_titles([
            basis
            for scenario in (economic_model.get("scenarios") or [])
            for basis in (scenario.get("evidence_basis") or [])
        ])
        return {
            "explanation": (
                "Summarizes scenario confidence based on explicit assumptions and evidence strength. "
                "It avoids unsupported numerical forecasts."
            ),
            "source_titles": source_titles,
            "caveat": "Scenario confidence is qualitative; it should be read as decision support, not prediction.",
            "confidence": "Medium unless the scenario is backed by multiple primary datasets.",
        }

    source_titles = _unique_titles([
        finding.get("source_title") or finding.get("paper_title") or ""
        for finding in findings
    ])
    return {
        "explanation": "Shows where the evidence came from so users can see whether the answer is balanced or source-heavy.",
        "source_titles": source_titles,
        "caveat": "Counts of findings do not measure truth; stronger sources still matter more than more sources.",
        "confidence": "Medium for evidence coverage; low for causal conclusions without the report context.",
    }


def _source_type_count(findings: list[dict]) -> int:
    return len({str(finding.get("source_type") or "unknown") for finding in findings})


def _trend_strength(analysis: dict) -> float:
    trends = (analysis.get("trends") or {}).get("trends") or []
    if not trends:
        return 0.0
    strengths = []
    for trend in trends:
        value = trend.get("pct_change")
        if value is None:
            value = trend.get("absolute_change")
        try:
            strengths.append(abs(float(value)))
        except (TypeError, ValueError):
            continue
    return max(strengths) if strengths else 0.0


def _claim_risk(fact_check_report: dict) -> int:
    risky_statuses = {"contradicted", "insufficient_evidence", "partially_supported"}
    return sum(
        1 for claim in (fact_check_report.get("checked_claims") or [])
        if str(claim.get("status") or "") in risky_statuses
    ) + len(fact_check_report.get("red_flags") or [])


def _chart_candidates(
    findings: list[dict],
    analysis: dict,
    validation_report: dict,
    economic_model: dict,
    fact_check_report: dict,
) -> list[ChartCandidate]:
    available = set(_available_templates(findings, analysis, validation_report, economic_model, fact_check_report))
    candidates: list[ChartCandidate] = []
    primary_sources = int(validation_report.get("primary_source_count") or 0)
    avg_credibility = float(validation_report.get("average_credibility") or 0)
    trend_count = len((analysis.get("trends") or {}).get("trends") or [])
    scenario_count = len(economic_model.get("scenarios") or [])
    source_type_count = _source_type_count(findings)
    claim_risk = _claim_risk(fact_check_report)

    if "trend_change_summary" in available:
        score = 90 + min(25, trend_count * 3) + min(20, _trend_strength(analysis) / 2) + min(10, primary_sources * 2)
        candidates.append(ChartCandidate(
            "trend_change_summary",
            score,
            "Historical baseline",
            "Ranks actual computed changes in the strongest loaded indicators, making it the most data-grounded exhibit.",
        ))

    if "trend_series" in available:
        score = 82 + min(20, trend_count * 2) + min(12, primary_sources * 2)
        candidates.append(ChartCandidate(
            "trend_series",
            score,
            "Trend context",
            "Shows the direction of trusted indicators over time without mixing raw units.",
        ))

    if "claim_support_status" in available:
        score = 76 + min(30, claim_risk * 6)
        candidates.append(ChartCandidate(
            "claim_support_status",
            score,
            "Claim verification",
            "Highlights whether the strongest claims are actually supported before the user trusts the report.",
        ))

    if "evidence_quality" in available:
        trust_gap = max(0.0, 0.9 - avg_credibility)
        score = 68 + trust_gap * 60 + min(12, len(validation_report.get("low_confidence_sources") or []) * 3)
        candidates.append(ChartCandidate(
            "evidence_quality",
            score,
            "Source reliability",
            "Explains how much weight to place on each source, especially when the evidence base is uneven.",
        ))

    if "scenario_matrix" in available:
        score = 58 + min(24, scenario_count * 6)
        if trend_count == 0:
            score += 10
        candidates.append(ChartCandidate(
            "scenario_matrix",
            score,
            "Decision scenarios",
            "Summarizes assumption-driven futures only after evidence and claims have been checked.",
        ))

    if "source_mix" in available and source_type_count >= 2:
        score = 38 + min(14, source_type_count * 4)
        candidates.append(ChartCandidate(
            "source_mix",
            score,
            "Evidence coverage",
            "Shows whether the run relied on a balanced evidence mix or one dominant source type.",
        ))

    candidates.sort(key=lambda candidate: candidate.score, reverse=True)
    return candidates


async def visualizer_node(state: AgentState) -> dict:
    sid = state["session_id"]
    findings = state.get("findings", [])
    analysis = state.get("analysis", {})
    validation_report = state.get("validation_report", {})
    economic_model = state.get("economic_model", {})
    fact_check_report = state.get("fact_check_report", {})

    await emit(sid, AgentEvent(
        type="node_start", agent="visualizer",
        payload={"message": "Selecting chart template and rendering..."}
    ))

    candidates = _chart_candidates(findings, analysis, validation_report, economic_model, fact_check_report)
    if not candidates:
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

    rationale = (
        "Ranked chart candidates by argument impact: computed trends first, then claim support, source quality, "
        "and scenarios only when they add decision value."
    )

    chart_specs: list[dict] = []
    used_roles: set[str] = set()
    for candidate in candidates:
        if len(chart_specs) >= 3:
            break
        if candidate.argument_role in used_roles:
            continue
        try:
            chart_specs.append(_build_chart(candidate, findings, analysis, validation_report, economic_model, fact_check_report))
            used_roles.add(candidate.argument_role)
        except ValueError:
            continue

    await emit(sid, AgentEvent(
        type="chart_ready", agent="visualizer",
        payload={
            "charts": len(chart_specs),
            "chart_specs": chart_specs,
            "rationale": rationale,
            "candidate_scores": [
                {
                    "template": candidate.template,
                    "score": round(candidate.score, 2),
                    "argument_role": candidate.argument_role,
                }
                for candidate in candidates
            ],
            "message": f"Rendered {len(chart_specs)} chart(s)",
        }
    ))
    await emit(sid, AgentEvent(
        type="node_end", agent="visualizer",
        payload={"chart_count": len(chart_specs)}
    ))
    return {"chart_specs": chart_specs}
