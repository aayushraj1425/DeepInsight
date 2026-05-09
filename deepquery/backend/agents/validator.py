from collections import Counter
from datetime import datetime, timezone
from typing import Any

from agents.state import AgentState
from events import AgentEvent
from runtime import emit


CURRENT_YEAR = datetime.now(timezone.utc).year

PROVIDER_CREDIBILITY = {
    "BLS": 0.96,
    "FRED": 0.95,
    "World Bank": 0.92,
    "OECD": 0.92,
    "IMF": 0.9,
    "SEC EDGAR": 0.9,
    "Stanford HAI": 0.88,
    "NBER": 0.86,
    "Data.gov": 0.84,
    "Semantic Scholar": 0.82,
    "OpenAlex": 0.82,
    "Crossref": 0.8,
    "McKinsey": 0.76,
    "WEF": 0.74,
    "LinkedIn": 0.73,
    "arXiv": 0.74,
    "Stack Overflow": 0.72,
    "GitHub": 0.72,
    "Layoffs.fyi": 0.68,
    "DataCite": 0.68,
}


def _provider(item: dict) -> str:
    return str(item.get("provider") or item.get("source") or "Unknown")


def _latest_year(item: dict) -> int | None:
    for key in ("latest_year", "year"):
        try:
            value = item.get(key)
            if value:
                return int(value)
        except (TypeError, ValueError):
            pass
    summary = item.get("summary", {})
    if isinstance(summary, dict):
        value = (summary.get("value") or {}).get("latest_year")
        try:
            return int(value) if value else None
        except (TypeError, ValueError):
            return None
    return None


def _score_source(item: dict, kind: str) -> dict:
    provider = _provider(item)
    credibility = float(item.get("credibility") or PROVIDER_CREDIBILITY.get(provider, 0.6))
    latest_year = _latest_year(item)
    freshness_penalty = 0.0
    freshness_note = "freshness unknown"
    if latest_year:
        age = max(0, CURRENT_YEAR - latest_year)
        freshness_penalty = min(0.25, age * 0.04)
        freshness_note = "current" if age <= 2 else f"stale or lagged by {age} years"

    method_penalty = 0.0
    title = str(item.get("title") or "")
    if provider in {"arXiv", "Stack Overflow", "GitHub", "Layoffs.fyi", "McKinsey", "WEF", "LinkedIn"}:
        method_penalty += 0.06
    if not item.get("url") and kind != "paper":
        method_penalty += 0.04

    score = max(0.0, min(1.0, credibility - freshness_penalty - method_penalty))
    flags = []
    if freshness_penalty >= 0.12:
        flags.append(freshness_note)
    if provider in {"Stack Overflow", "GitHub"}:
        flags.append("platform or survey selection bias")
    if provider in {"McKinsey", "WEF", "LinkedIn"}:
        flags.append("report or platform data should be corroborated with primary data")
    if provider == "Layoffs.fyi":
        flags.append("layoff tracker is timely but unofficial")
    if provider == "arXiv":
        flags.append("preprint evidence may not be peer reviewed")

    return {
        "source_id": item.get("source_id") or item.get("dataset_id") or item.get("paper_id") or title,
        "title": title,
        "provider": provider,
        "kind": kind,
        "credibility_score": round(score, 2),
        "latest_year": latest_year,
        "freshness": freshness_note,
        "flags": flags,
        "url": item.get("url"),
    }


def build_validation_report(state: AgentState) -> dict[str, Any]:
    papers = state.get("paper_sources", [])
    datasets = state.get("datasets", [])
    table_profiles = (state.get("dataset_analysis", {}) or {}).get("tables", [])
    trusted_sources = (state.get("dataset_analysis", {}) or {}).get("trusted_sources", [])

    scored = []
    scored.extend(_score_source(source, "paper") for source in papers[:20])
    scored.extend(_score_source(source, "dataset") for source in datasets[:20])
    scored.extend(_score_source(source, "trusted_time_series") for source in table_profiles[:12])
    scored.extend(_score_source(source, "source_candidate") for source in trusted_sources[:12])

    provider_counts = Counter(item["provider"] for item in scored)
    primary_providers = {"BLS", "FRED", "World Bank", "OECD", "IMF", "SEC EDGAR", "Data.gov"}
    primary_count = sum(count for provider, count in provider_counts.items() if provider in primary_providers)
    low_confidence = [item for item in scored if item["credibility_score"] < 0.7]
    stale = [item for item in scored if item.get("latest_year") and CURRENT_YEAR - int(item["latest_year"]) > 2]

    report = {
        "source_count": len(scored),
        "provider_counts": dict(provider_counts),
        "primary_source_count": primary_count,
        "average_credibility": round(sum(item["credibility_score"] for item in scored) / len(scored), 2) if scored else 0,
        "low_confidence_sources": low_confidence[:8],
        "stale_or_lagged_sources": stale[:8],
        "source_scores": scored[:40],
        "validation_rules": [
            "Primary government and central-bank data outrank surveys, trackers, and vendor reports.",
            "Sources older than two years are treated as lagged for fast-moving labor and AI markets.",
            "Unloaded dataset candidates may guide research but should not support precise numeric claims.",
            "Preprints and survey data require caveats unless corroborated by stronger sources.",
        ],
    }
    if primary_count == 0:
        report["warning"] = "No primary government or central-bank source was validated for this run."
    return report


async def validator_node(state: AgentState) -> dict:
    sid = state["session_id"]
    await emit(sid, AgentEvent(
        type="node_start",
        agent="validator",
        payload={"message": "Scoring source credibility, freshness, and methodology risk..."},
    ))

    report = build_validation_report(state)

    await emit(sid, AgentEvent(
        type="validation_ready",
        agent="validator",
        payload={
            "message": f"Validated {report['source_count']} sources; average credibility {report['average_credibility']}",
            "average_credibility": report["average_credibility"],
            "primary_source_count": report["primary_source_count"],
            "provider_counts": report["provider_counts"],
            "warnings": [report.get("warning")] if report.get("warning") else [],
        },
    ))
    await emit(sid, AgentEvent(
        type="node_end",
        agent="validator",
        payload={"source_count": report["source_count"], "average_credibility": report["average_credibility"]},
    ))
    return {"validation_report": report}
