import asyncio

from events import AgentEvent
from runtime import emit
from tools.analysis import aggregate, compare
from viz.templates import bar_comparison, forest_plot, timeline


SLEEP_QUERY = "what is the effect of sleep deprivation on cognitive performance?"
WAGE_QUERY = "what are the economic effects of minimum wage increases?"


def _normalize(query: str) -> str:
    return " ".join(query.strip().lower().split())


def _chart_specs(findings: list[dict], analysis: dict) -> list[dict]:
    specs: list[dict] = []
    builders = [
        ("bar_comparison", lambda: bar_comparison(analysis["compare"])),
        ("timeline", lambda: timeline(findings)),
        ("forest_plot", lambda: forest_plot(findings)),
    ]
    for template, build in builders:
        try:
            figure, insight = build()
        except (KeyError, ValueError):
            continue
        specs.append({
            "template": template,
            "title": figure.get("layout", {}).get("title", {}).get("text", template),
            "insight": insight,
            "figure": figure,
        })
    return specs[:3]


def _sleep_findings() -> list[dict]:
    return [
        {
            "metric": "reaction_time_slowing_percent",
            "value": "18.5",
            "sample_size": 48,
            "ci": "95% CI: 12.0-25.0",
            "p_value": 0.003,
            "intervention": "24h sleep deprivation",
            "source_quote": "Sleep deprivation produced slower reaction time and more lapses.",
            "paper_title": "Total sleep deprivation and sustained attention",
            "year": 2019,
        },
        {
            "metric": "working_memory_accuracy_percent",
            "value": "-9.2",
            "sample_size": 72,
            "ci": "95% CI: -14.1--4.0",
            "p_value": 0.01,
            "intervention": "restricted sleep",
            "source_quote": "Participants showed lower working-memory accuracy after restricted sleep.",
            "paper_title": "Sleep restriction and working memory in adults",
            "year": 2020,
        },
        {
            "metric": "attention_lapses_count",
            "value": "6.8",
            "sample_size": 55,
            "ci": "95% CI: 4.1-9.5",
            "p_value": 0.001,
            "intervention": "overnight wakefulness",
            "source_quote": "Overnight wakefulness increased attention lapses during vigilance testing.",
            "paper_title": "Vigilance after overnight wakefulness",
            "year": 2021,
        },
        {
            "metric": "executive_function_score_change",
            "value": "-0.42",
            "sample_size": 64,
            "ci": "95% CI: -0.62--0.21",
            "p_value": 0.02,
            "intervention": "sleep deprivation",
            "source_quote": "Executive function scores declined after acute sleep deprivation.",
            "paper_title": "Acute sleep loss and executive control",
            "year": 2023,
        },
    ]


def _wage_findings() -> list[dict]:
    return [
        {
            "metric": "employment_change_percent",
            "value": "-0.8",
            "sample_size": 138,
            "ci": "95% CI: -1.9-0.3",
            "p_value": 0.14,
            "intervention": "minimum wage increase",
            "source_quote": "Estimated employment effects were small and statistically uncertain.",
            "paper_title": "Minimum wages and low-wage employment",
            "year": 2018,
        },
        {
            "metric": "earnings_change_percent",
            "value": "5.4",
            "sample_size": 138,
            "ci": "95% CI: 3.0-7.8",
            "p_value": 0.001,
            "intervention": "minimum wage increase",
            "source_quote": "Earnings rose for covered low-wage workers after the policy change.",
            "paper_title": "Minimum wages and worker earnings",
            "year": 2019,
        },
        {
            "metric": "price_change_percent",
            "value": "1.1",
            "sample_size": 87,
            "ci": "95% CI: 0.2-2.1",
            "p_value": 0.04,
            "intervention": "restaurant minimum wage exposure",
            "source_quote": "Consumer prices increased modestly in highly exposed sectors.",
            "paper_title": "Pass-through from wage floors to prices",
            "year": 2021,
        },
        {
            "metric": "poverty_rate_change_pp",
            "value": "-0.3",
            "sample_size": 51,
            "ci": "95% CI: -0.9-0.2",
            "p_value": 0.2,
            "intervention": "state minimum wage increase",
            "source_quote": "Poverty estimates were directionally negative but imprecise.",
            "paper_title": "Minimum wages and household poverty",
            "year": 2022,
        },
    ]


async def _emit(session_id: str, event_type: str, agent: str, payload: dict) -> None:
    await emit(session_id, AgentEvent(type=event_type, agent=agent, payload=payload))
    await asyncio.sleep(0.18)


async def _run_sleep_demo(session_id: str) -> None:
    findings = _sleep_findings()
    analysis = {
        "tools_used": ["aggregate", "compare"],
        "reasoning": "The extracted findings contain numeric outcomes across multiple cognitive metrics.",
        "aggregate": aggregate(findings),
        "compare": compare(findings, "metric"),
    }
    chart_specs = _chart_specs(findings, analysis)
    report = (
        "# Research Report\n\n"
        "## Bottom line\n"
        "Across the extracted abstract-level findings, sleep deprivation is associated with worse cognitive performance, "
        "including slower reaction time, lower working-memory accuracy, more attention lapses, and weaker executive control.\n\n"
        "## Evidence\n"
        "- Reaction-time slowing and attention lapses show the clearest positive deterioration signals.\n"
        "- Accuracy and executive-function findings move in the negative direction, consistent with impaired performance.\n"
        "- The findings are abstract-derived and mix outcome units, so the charts should be read as directional evidence rather than a pooled meta-analysis.\n\n"
        "## Limitations\n"
        "The pipeline extracted numeric values from abstracts only. Full-text methods, harmonized effect sizes, and study-quality checks would be needed for a publication-grade synthesis."
    )

    await _emit(session_id, "node_start", "planner", {"message": "Decomposing: sleep deprivation and cognitive performance"})
    await _emit(session_id, "node_end", "planner", {
        "subqueries": ["sleep deprivation cognitive performance", "sleep restriction working memory", "sleep loss vigilance attention"],
        "rationale": "The query is split across attention, memory, and executive-function outcomes.",
    })
    await _emit(session_id, "node_start", "discovery", {"message": "Searching Semantic Scholar for 3 subqueries..."})
    await _emit(session_id, "tool_result", "discovery", {"query": "sleep deprivation cognitive performance", "found": 6, "new": 4})
    await _emit(session_id, "node_end", "discovery", {"total_papers": 12})
    await _emit(session_id, "node_start", "extractor", {"message": "Extracting structured findings from 12 papers..."})
    await _emit(session_id, "tool_result", "extractor", {"findings_extracted": len(findings), "papers_processed": 12})
    await _emit(session_id, "node_end", "extractor", {"total_findings": len(findings)})
    await _emit(session_id, "node_start", "analyst", {"message": f"Analyzing {len(findings)} findings...", "findings_count": len(findings), "retry": 0})
    await _emit(session_id, "tool_call", "analyst", {"tool": "aggregate", "findings_count": len(findings)})
    await _emit(session_id, "tool_call", "analyst", {"tool": "compare", "findings_count": len(findings)})
    await _emit(session_id, "node_end", "analyst", {"tools_run": ["aggregate", "compare"], "result_keys": list(analysis.keys())})
    await _emit(session_id, "node_start", "critic", {"message": "Reviewing analysis quality... (attempt 1/3)"})
    await _emit(session_id, "critic_decision", "critic", {
        "decision": "approve",
        "reasoning": "The analysis includes aggregate statistics and a metric comparison with multiple numeric findings.",
        "feedback": "",
        "retries_used": 0,
        "retry_count": 0,
        "max_retries": 2,
    })
    await _emit(session_id, "node_end", "critic", {"approved": True})
    await _emit(session_id, "node_start", "visualizer", {"message": "Selecting chart template and rendering..."})
    await _emit(session_id, "chart_ready", "visualizer", {"charts": len(chart_specs), "chart_specs": chart_specs, "message": f"Rendered {len(chart_specs)} chart(s)"})
    await _emit(session_id, "node_end", "visualizer", {"chart_count": len(chart_specs)})
    await _emit(session_id, "node_start", "reporter", {"message": "Generating markdown research report..."})
    await _emit(session_id, "report_ready", "reporter", {"length": len(report), "report": report, "message": "Report ready"})
    await _emit(session_id, "node_end", "reporter", {})


async def _run_wage_demo(session_id: str) -> None:
    findings = _wage_findings()
    analysis = {
        "tools_used": ["aggregate", "compare"],
        "reasoning": "The retry groups the mixed economic outcomes rather than treating the first sparse result as decisive.",
        "aggregate": aggregate(findings),
        "compare": compare(findings, "metric"),
    }
    chart_specs = _chart_specs(findings, analysis)
    report = (
        "# Research Report\n\n"
        "## Bottom line\n"
        "The extracted findings suggest minimum wage increases raise earnings for covered workers, while employment, poverty, and price effects are smaller and more uncertain.\n\n"
        "## Evidence\n"
        "- Earnings effects are positive in the extracted findings.\n"
        "- Employment estimates are near zero and statistically uncertain in this cached synthesis.\n"
        "- Price pass-through appears modest in highly exposed sectors.\n"
        "- Poverty effects move in the expected direction but are imprecise.\n\n"
        "## Critic note\n"
        "The first analyst pass over-weighted a sparse employment-only result. The critic rejected it, and the retry broadened the analysis across earnings, prices, employment, and poverty.\n\n"
        "## Limitations\n"
        "These findings are intentionally heterogeneous. A full causal review would need design-specific weighting and stronger separation of short-run and long-run effects."
    )

    await _emit(session_id, "node_start", "planner", {"message": "Decomposing: economic effects of minimum wage increases"})
    await _emit(session_id, "node_end", "planner", {
        "subqueries": ["minimum wage employment effects", "minimum wage earnings effects", "minimum wage prices poverty"],
        "rationale": "The query is split across labor-market, earnings, consumer-price, and household outcomes.",
    })
    await _emit(session_id, "node_start", "discovery", {"message": "Searching Semantic Scholar for 3 subqueries..."})
    await _emit(session_id, "tool_result", "discovery", {"query": "minimum wage employment effects", "found": 6, "new": 3})
    await _emit(session_id, "node_end", "discovery", {"total_papers": 10})
    await _emit(session_id, "node_start", "extractor", {"message": "Extracting structured findings from 10 papers..."})
    await _emit(session_id, "tool_result", "extractor", {"findings_extracted": len(findings), "papers_processed": 10})
    await _emit(session_id, "node_end", "extractor", {"total_findings": len(findings)})
    await _emit(session_id, "node_start", "analyst", {"message": f"Analyzing {len(findings)} findings...", "findings_count": len(findings), "retry": 0})
    await _emit(session_id, "tool_call", "analyst", {"tool": "aggregate", "findings_count": 1})
    await _emit(session_id, "node_end", "analyst", {"tools_run": ["aggregate"], "result_keys": ["tools_used", "reasoning", "aggregate"]})
    await _emit(session_id, "node_start", "critic", {"message": "Reviewing analysis quality... (attempt 1/3)"})
    await _emit(session_id, "critic_decision", "critic", {
        "decision": "reject",
        "reasoning": "The first pass used only one outcome and ignored contradictory economic effects.",
        "feedback": "Broaden the analysis across earnings, employment, prices, and poverty; compare by metric instead of summarizing one sparse result.",
        "retries_used": 0,
        "retry_count": 1,
        "max_retries": 2,
    })
    await _emit(session_id, "node_end", "critic", {"approved": False})
    await _emit(session_id, "node_start", "analyst", {"message": "Retry 1/2 - Critic: broaden the analysis across economic outcomes", "findings_count": len(findings), "retry": 1})
    await _emit(session_id, "tool_call", "analyst", {"tool": "aggregate", "findings_count": len(findings)})
    await _emit(session_id, "tool_call", "analyst", {"tool": "compare", "findings_count": len(findings)})
    await _emit(session_id, "node_end", "analyst", {"tools_run": ["aggregate", "compare"], "result_keys": list(analysis.keys())})
    await _emit(session_id, "node_start", "critic", {"message": "Reviewing analysis quality... (attempt 2/3)"})
    await _emit(session_id, "critic_decision", "critic", {
        "decision": "approve",
        "reasoning": "The retry addresses the query with multiple economic outcomes and explicit comparison.",
        "feedback": "",
        "retries_used": 1,
        "retry_count": 1,
        "max_retries": 2,
    })
    await _emit(session_id, "node_end", "critic", {"approved": True})
    await _emit(session_id, "node_start", "visualizer", {"message": "Selecting chart template and rendering..."})
    await _emit(session_id, "chart_ready", "visualizer", {"charts": len(chart_specs), "chart_specs": chart_specs, "message": f"Rendered {len(chart_specs)} chart(s)"})
    await _emit(session_id, "node_end", "visualizer", {"chart_count": len(chart_specs)})
    await _emit(session_id, "node_start", "reporter", {"message": "Generating markdown research report..."})
    await _emit(session_id, "report_ready", "reporter", {"length": len(report), "report": report, "message": "Report ready"})
    await _emit(session_id, "node_end", "reporter", {})


async def run_cached_demo(session_id: str, query: str) -> bool:
    normalized = _normalize(query)
    if normalized == SLEEP_QUERY:
        await _run_sleep_demo(session_id)
        return True
    if normalized == WAGE_QUERY:
        await _run_wage_demo(session_id)
        return True
    return False
