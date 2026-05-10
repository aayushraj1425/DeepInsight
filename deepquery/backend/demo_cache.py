import asyncio
import re
from urllib.parse import quote_plus

from events import AgentEvent
from runtime import emit
from tools.analysis import aggregate, compare
from viz.templates import bar_comparison, forest_plot, timeline


SLEEP_QUERY      = "what is the effect of sleep deprivation on cognitive performance?"
WAGE_QUERY       = "what are the economic effects of minimum wage increases?"
GLP1_QUERY       = "glp-1 effects on cognition"
MICROPLASTIC_QUERY = "microplastics and gut microbiome"
VITAMIND_QUERY   = "vitamin d and depression"


def _normalize(query: str) -> str:
    return " ".join(query.strip().lower().split())


def _chart_specs(findings: list[dict], analysis: dict) -> list[dict]:
    chart_findings = _cached_findings(findings)
    specs: list[dict] = []
    builders = [
        ("bar_comparison", lambda: bar_comparison(analysis["compare"], chart_findings)),
        ("timeline",       lambda: timeline(chart_findings)),
        ("forest_plot",    lambda: forest_plot(chart_findings)),
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


def _source_search_url(title: str) -> str:
    return f"https://www.semanticscholar.org/search?q={quote_plus(title)}&sort=relevance"


def _cached_findings(findings: list[dict]) -> list[dict]:
    rows = []
    for finding in findings:
        title = finding.get("paper_title") or "Cached demo source"
        rows.append({
            **finding,
            "source": finding.get("source") or "cached_demo",
            "url": finding.get("url") or _source_search_url(title),
        })
    return rows


def _sources_from_findings(findings: list[dict]) -> list[dict]:
    sources = []
    seen = set()
    for finding in findings:
        title = finding.get("paper_title") or "Cached demo source"
        if title in seen:
            continue
        seen.add(title)
        sources.append({
            "title": title,
            "provider": "Cached demo / title search",
            "url": finding.get("url") or _source_search_url(title),
            "year": finding.get("year"),
            "citationCount": None,
        })
    return sources


# ── Sleep deprivation ────────────────────────────────────────────────────────

def _sleep_findings() -> list[dict]:
    return [
        {"metric": "reaction_time_slowing_percent", "value": "18.5", "sample_size": 48,
         "ci": "95% CI: 12.0-25.0", "p_value": 0.003, "intervention": "24h sleep deprivation",
         "source_quote": "Sleep deprivation produced slower reaction time and more lapses.",
         "paper_title": "Total sleep deprivation and sustained attention", "year": 2019},
        {"metric": "working_memory_accuracy_percent", "value": "-9.2", "sample_size": 72,
         "ci": "95% CI: -14.1--4.0", "p_value": 0.01, "intervention": "restricted sleep",
         "source_quote": "Participants showed lower working-memory accuracy after restricted sleep.",
         "paper_title": "Sleep restriction and working memory in adults", "year": 2020},
        {"metric": "attention_lapses_count", "value": "6.8", "sample_size": 55,
         "ci": "95% CI: 4.1-9.5", "p_value": 0.001, "intervention": "overnight wakefulness",
         "source_quote": "Overnight wakefulness increased attention lapses during vigilance testing.",
         "paper_title": "Vigilance after overnight wakefulness", "year": 2021},
        {"metric": "executive_function_score_change", "value": "-0.42", "sample_size": 64,
         "ci": "95% CI: -0.62--0.21", "p_value": 0.02, "intervention": "sleep deprivation",
         "source_quote": "Executive function scores declined after acute sleep deprivation.",
         "paper_title": "Acute sleep loss and executive control", "year": 2023},
    ]


# ── Minimum wage ─────────────────────────────────────────────────────────────

def _wage_findings() -> list[dict]:
    return [
        {"metric": "employment_change_percent", "value": "-0.8", "sample_size": 138,
         "ci": "95% CI: -1.9-0.3", "p_value": 0.14, "intervention": "minimum wage increase",
         "source_quote": "Estimated employment effects were small and statistically uncertain.",
         "paper_title": "Minimum wages and low-wage employment", "year": 2018},
        {"metric": "earnings_change_percent", "value": "5.4", "sample_size": 138,
         "ci": "95% CI: 3.0-7.8", "p_value": 0.001, "intervention": "minimum wage increase",
         "source_quote": "Earnings rose for covered low-wage workers after the policy change.",
         "paper_title": "Minimum wages and worker earnings", "year": 2019},
        {"metric": "price_change_percent", "value": "1.1", "sample_size": 87,
         "ci": "95% CI: 0.2-2.1", "p_value": 0.04, "intervention": "restaurant minimum wage exposure",
         "source_quote": "Consumer prices increased modestly in highly exposed sectors.",
         "paper_title": "Pass-through from wage floors to prices", "year": 2021},
        {"metric": "poverty_rate_change_pp", "value": "-0.3", "sample_size": 51,
         "ci": "95% CI: -0.9-0.2", "p_value": 0.2, "intervention": "state minimum wage increase",
         "source_quote": "Poverty estimates were directionally negative but imprecise.",
         "paper_title": "Minimum wages and household poverty", "year": 2022},
    ]


# ── GLP-1 & cognition ────────────────────────────────────────────────────────

def _glp1_findings() -> list[dict]:
    return [
        {"metric": "mmse_score_change", "value": "2.3", "sample_size": 103,
         "ci": "95% CI: 1.1-3.5", "p_value": 0.001, "intervention": "semaglutide 1mg/week",
         "source_quote": "MMSE scores improved significantly in GLP-1 treated patients vs placebo.",
         "paper_title": "Semaglutide and cognitive outcomes in T2D", "year": 2022},
        {"metric": "hippocampal_volume_change_pct", "value": "1.8", "sample_size": 67,
         "ci": "95% CI: 0.4-3.2", "p_value": 0.012, "intervention": "liraglutide 1.8mg",
         "source_quote": "Hippocampal volume increased modestly in the liraglutide group.",
         "paper_title": "Liraglutide and hippocampal neurogenesis", "year": 2021},
        {"metric": "memory_recall_accuracy_pct", "value": "12.8", "sample_size": 88,
         "ci": "95% CI: 7.2-18.4", "p_value": 0.004, "intervention": "GLP-1 receptor agonist",
         "source_quote": "Delayed recall accuracy improved 12.8% over 24 weeks of treatment.",
         "paper_title": "GLP-1 agonists and episodic memory", "year": 2023},
        {"metric": "executive_function_z_score", "value": "0.47", "sample_size": 74,
         "ci": "95% CI: 0.18-0.76", "p_value": 0.003, "intervention": "dulaglutide",
         "source_quote": "Executive function composite z-score rose 0.47 SD vs controls.",
         "paper_title": "Dulaglutide effects on executive control", "year": 2023},
        {"metric": "neuroinflammation_il6_change_pct", "value": "-22.4", "sample_size": 55,
         "ci": "95% CI: -31.0--13.8", "p_value": 0.001, "intervention": "semaglutide",
         "source_quote": "IL-6 levels fell 22.4% in treated patients, suggesting reduced neuroinflammation.",
         "paper_title": "GLP-1 and neuroinflammatory markers", "year": 2024},
    ]


# ── Microplastics & gut microbiome ───────────────────────────────────────────

def _microplastic_findings() -> list[dict]:
    return [
        {"metric": "shannon_diversity_index_change", "value": "-0.31", "sample_size": 42,
         "ci": "95% CI: -0.52--0.10", "p_value": 0.005, "intervention": "10μg/kg/day microplastic exposure",
         "source_quote": "Microplastic-exposed mice showed reduced alpha diversity (Shannon index).",
         "paper_title": "Polystyrene microplastics and gut diversity", "year": 2022},
        {"metric": "il6_inflammatory_marker_pct", "value": "28.0", "sample_size": 38,
         "ci": "95% CI: 14.0-42.0", "p_value": 0.001, "intervention": "PET microplastic ingestion",
         "source_quote": "IL-6 elevated 28% in high-dose exposure groups vs controls.",
         "paper_title": "Microplastics and intestinal inflammation", "year": 2023},
        {"metric": "gut_permeability_teer_change_pct", "value": "-19.0", "sample_size": 29,
         "ci": "95% CI: -28.0--10.0", "p_value": 0.002, "intervention": "chronic microplastic exposure",
         "source_quote": "TEER values declined 19%, indicating increased intestinal permeability.",
         "paper_title": "Microplastic effects on tight junction integrity", "year": 2022},
        {"metric": "bifidobacterium_abundance_change_pct", "value": "-24.0", "sample_size": 51,
         "ci": "95% CI: -34.0--14.0", "p_value": 0.001, "intervention": "nanoplastic ingestion",
         "source_quote": "Bifidobacterium counts dropped 24% with nanoplastic exposure.",
         "paper_title": "Nanoplastics and probiotic bacteria", "year": 2023},
        {"metric": "butyrate_producing_bacteria_change_pct", "value": "-16.5", "sample_size": 44,
         "ci": "95% CI: -24.0--9.0", "p_value": 0.003, "intervention": "mixed microplastic diet",
         "source_quote": "Butyrate-producing species declined 16.5%, reducing SCFA output.",
         "paper_title": "Microplastics and short-chain fatty acid metabolism", "year": 2024},
    ]


# ── Vitamin D & depression ───────────────────────────────────────────────────

def _vitamind_findings() -> list[dict]:
    return [
        {"metric": "hamilton_depression_scale_change", "value": "-4.2", "sample_size": 120,
         "ci": "95% CI: -6.1--2.3", "p_value": 0.001, "intervention": "Vitamin D3 2000 IU/day",
         "source_quote": "HAM-D scores fell 4.2 points more in the supplemented group vs placebo.",
         "paper_title": "Vitamin D supplementation and HAM-D scores", "year": 2020},
        {"metric": "response_rate_pct", "value": "42.0", "sample_size": 89,
         "ci": "95% CI: 32.0-52.0", "p_value": 0.008, "intervention": "Vitamin D3 4000 IU/day",
         "source_quote": "42% of participants met response criteria vs 24% in the placebo arm.",
         "paper_title": "High-dose Vitamin D in major depression", "year": 2021},
        {"metric": "remission_rate_pct", "value": "26.0", "sample_size": 89,
         "ci": "95% CI: 17.0-35.0", "p_value": 0.02, "intervention": "Vitamin D3 4000 IU/day",
         "source_quote": "Remission rates were 26% in the treated group vs 14% placebo.",
         "paper_title": "High-dose Vitamin D in major depression", "year": 2021},
        {"metric": "serum_25ohd_change_ng_ml", "value": "18.0", "sample_size": 134,
         "ci": "95% CI: 14.0-22.0", "p_value": 0.001, "intervention": "Vitamin D3 supplementation",
         "source_quote": "25(OH)D serum levels rose 18 ng/mL on average across supplemented arms.",
         "paper_title": "Vitamin D bioavailability in depression trials", "year": 2022},
        {"metric": "phq9_score_change", "value": "-3.1", "sample_size": 76,
         "ci": "95% CI: -4.8--1.4", "p_value": 0.001, "intervention": "Vitamin D + antidepressant",
         "source_quote": "PHQ-9 dropped 3.1 points more in the combination arm than antidepressant alone.",
         "paper_title": "Adjunct Vitamin D to antidepressant therapy", "year": 2023},
    ]


# ── Shared emit helper ───────────────────────────────────────────────────────

def _section(markdown: str, title: str) -> str:
    match = re.search(rf"##\s+{re.escape(title)}\s+([\s\S]*?)(?=\n##\s+|\s*$)", markdown, re.IGNORECASE)
    return match.group(1).strip() if match else ""


def _clean_markdown(text: str) -> str:
    return re.sub(r"\[(.*?)\]\(.*?\)", r"\1", re.sub(r"\*\*(.*?)\*\*", r"\1", text)).strip()


def _synthesis_from_report(report: str) -> dict:
    bottom_line = _clean_markdown(_section(report, "Bottom line") or report.split("\n\n", 1)[0])
    key_findings = [
        _clean_markdown(re.sub(r"^\s*[-*]\s+", "", line).strip())
        for line in _section(report, "Key Findings").splitlines()
        if re.match(r"^\s*[-*]\s+", line)
    ]
    limitation = _clean_markdown(_section(report, "Limitations").splitlines()[0]) if _section(report, "Limitations") else ""
    confidence = "high" if len(key_findings) >= 4 and "p=" in report.lower() else "moderate"
    return {
        "answer": bottom_line,
        "confidence": confidence,
        "mostReliableResult": key_findings[0] if key_findings else "",
        "mainLimitation": limitation,
        "evidenceCount": len(key_findings),
        "studiesCount": len(key_findings),
    }


async def _emit(session_id: str, event_type: str, agent: str, payload: dict) -> None:
    if event_type == "report_ready" and "synthesis" not in payload and payload.get("report"):
        synthesis = _synthesis_from_report(payload["report"])
        await emit(session_id, AgentEvent(
            type="synthesis_ready",
            agent=agent,
            payload={"synthesis": synthesis, "message": "Synthesis ready"},
        ))
        payload = {**payload, "synthesis": synthesis}
        await asyncio.sleep(0.18)
    await emit(session_id, AgentEvent(type=event_type, agent=agent, payload=payload))
    await asyncio.sleep(0.18)


async def _emit_cached_sources(session_id: str, findings: list[dict]) -> None:
    await _emit(
        session_id,
        "sources_ready",
        "discovery",
        {
            "sources": _sources_from_findings(findings),
            "message": "Cached demo sources ready",
        },
    )


# ── Demo runners ─────────────────────────────────────────────────────────────

async def _run_sleep_demo(session_id: str) -> None:
    findings = _sleep_findings()
    analysis = {
        "tools_used": ["aggregate", "compare"],
        "reasoning": "Numeric outcomes across multiple cognitive metrics.",
        "aggregate": aggregate(findings),
        "compare": compare(findings, "metric"),
    }
    chart_specs = _chart_specs(findings, analysis)
    report = (
        "# Research Report\n\n"
        "## Bottom line\n"
        "Sleep deprivation consistently impairs cognition: reaction time slows by 18.5%, "
        "working-memory accuracy drops −9.2 points, and executive function falls −0.42 SD.\n\n"
        "## Key Findings\n"
        "- **Reaction-time slowing**: 18.5% — 24h deprivation, n=48, p=0.003 (95% CI: 12–25%)\n"
        "- **Working-memory accuracy**: −9.2% — restricted sleep, n=72, p=0.01\n"
        "- **Attention lapses**: 6.8 count increase — overnight wakefulness, n=55, p=0.001\n"
        "- **Executive function**: −0.42 SD — acute deprivation, n=64, p=0.02\n\n"
        "## Evidence\n"
        "All four outcomes moved in the impairment direction. Reaction time and attention "
        "lapses show the clearest dose-response signals.\n\n"
        "## Limitations\n"
        "Abstract-derived findings only. Full-text extraction and harmonised effect sizes would strengthen the synthesis."
    )
    await _emit(session_id, "node_start", "planner", {"message": "Decomposing: sleep deprivation and cognitive performance"})
    await _emit(session_id, "node_end", "planner", {
        "canonical_question": "What is the effect of sleep deprivation on cognitive performance?",
        "subqueries": ["sleep deprivation cognitive performance", "sleep restriction working memory", "sleep loss vigilance attention"],
        "rationale": "Split across attention, memory, and executive-function outcomes.",
    })
    await _emit(session_id, "node_start", "discovery", {"message": "Searching for 3 subqueries..."})
    await _emit(session_id, "tool_result", "discovery", {"source": "semantic_scholar", "query": "sleep deprivation cognitive performance", "found": 6, "new": 4})
    await _emit(session_id, "node_end", "discovery", {"total_papers": 12})
    await _emit_cached_sources(session_id, findings)
    await _emit(session_id, "node_start", "extractor", {"message": "Extracting structured findings from 12 papers..."})
    await _emit(session_id, "tool_result", "extractor", {"findings_extracted": len(findings), "papers_processed": 12})
    await _emit(session_id, "node_end", "extractor", {"total_findings": len(findings)})
    await _emit(session_id, "node_start", "analyst", {"message": f"Analyzing {len(findings)} findings...", "findings_count": len(findings), "retry": 0})
    await _emit(session_id, "tool_call", "analyst", {"tool": "aggregate", "findings_count": len(findings)})
    await _emit(session_id, "tool_call", "analyst", {"tool": "compare", "findings_count": len(findings)})
    await _emit(session_id, "node_end", "analyst", {"tools_run": ["aggregate", "compare"], "result_keys": list(analysis.keys())})
    await _emit(session_id, "node_start", "critic", {"message": "Reviewing analysis quality... (attempt 1/3)"})
    await _emit(session_id, "critic_decision", "critic", {"decision": "approve", "reasoning": "Aggregate and comparison cover multiple outcomes.", "feedback": "", "retries_used": 0, "retry_count": 0, "max_retries": 2})
    await _emit(session_id, "node_end", "critic", {"approved": True})
    await _emit(session_id, "node_start", "visualizer", {"message": "Rendering charts..."})
    await _emit(session_id, "chart_ready", "visualizer", {"charts": len(chart_specs), "chart_specs": chart_specs, "message": f"Rendered {len(chart_specs)} chart(s)"})
    await _emit(session_id, "node_end", "visualizer", {"chart_count": len(chart_specs)})
    await _emit(session_id, "node_start", "reporter", {"message": "Generating markdown research report..."})
    await _emit(session_id, "report_ready", "reporter", {"length": len(report), "report": report, "message": "Report ready"})
    await _emit(session_id, "node_end", "reporter", {})


async def _run_wage_demo(session_id: str) -> None:
    findings = _wage_findings()
    analysis = {
        "tools_used": ["aggregate", "compare"],
        "reasoning": "Groups mixed economic outcomes after critic rejected a sparse first pass.",
        "aggregate": aggregate(findings),
        "compare": compare(findings, "metric"),
    }
    chart_specs = _chart_specs(findings, analysis)
    report = (
        "# Research Report\n\n"
        "## Bottom line\n"
        "Minimum wage increases raise covered-worker earnings by ~5.4% while employment effects "
        "remain near zero (−0.8%, p=0.14) and price pass-through is modest at +1.1%.\n\n"
        "## Key Findings\n"
        "- **Earnings change**: +5.4% — n=138 studies, p=0.001 (95% CI: 3.0–7.8%)\n"
        "- **Employment change**: −0.8% — statistically uncertain, p=0.14\n"
        "- **Consumer price increase**: +1.1% — restaurant sector, n=87, p=0.04\n"
        "- **Poverty rate change**: −0.3 pp — directional but imprecise, p=0.20\n\n"
        "## Critic note\n"
        "First analyst pass over-weighted a sparse employment-only result. "
        "Critic rejected it; retry broadened across all four outcomes.\n\n"
        "## Limitations\n"
        "Heterogeneous designs. Short-run and long-run effects need separation."
    )
    await _emit(session_id, "node_start", "planner", {"message": "Decomposing: economic effects of minimum wage increases"})
    await _emit(session_id, "node_end", "planner", {
        "canonical_question": "What are the economic effects of minimum wage increases?",
        "subqueries": ["minimum wage employment effects", "minimum wage earnings effects", "minimum wage prices poverty"],
        "rationale": "Split across labour-market, earnings, consumer-price, and household outcomes.",
    })
    await _emit(session_id, "node_start", "discovery", {"message": "Searching for 3 subqueries..."})
    await _emit(session_id, "tool_result", "discovery", {"source": "semantic_scholar", "query": "minimum wage employment effects", "found": 6, "new": 3})
    await _emit(session_id, "node_end", "discovery", {"total_papers": 10})
    await _emit_cached_sources(session_id, findings)
    await _emit(session_id, "node_start", "extractor", {"message": "Extracting structured findings from 10 papers..."})
    await _emit(session_id, "tool_result", "extractor", {"findings_extracted": len(findings), "papers_processed": 10})
    await _emit(session_id, "node_end", "extractor", {"total_findings": len(findings)})
    await _emit(session_id, "node_start", "analyst", {"message": f"Analyzing {len(findings)} findings...", "findings_count": len(findings), "retry": 0})
    await _emit(session_id, "tool_call", "analyst", {"tool": "aggregate", "findings_count": 1})
    await _emit(session_id, "node_end", "analyst", {"tools_run": ["aggregate"], "result_keys": ["tools_used", "reasoning", "aggregate"]})
    await _emit(session_id, "node_start", "critic", {"message": "Reviewing analysis quality... (attempt 1/3)"})
    await _emit(session_id, "critic_decision", "critic", {
        "decision": "reject",
        "reasoning": "First pass used only one outcome; ignores contradictory effects.",
        "feedback": "Broaden the analysis across earnings, employment, prices, and poverty.",
        "retries_used": 0, "retry_count": 1, "max_retries": 2,
    })
    await _emit(session_id, "node_end", "critic", {"approved": False})
    await _emit(session_id, "node_start", "analyst", {"message": "Retry 1/2 — broadening across all economic outcomes", "findings_count": len(findings), "retry": 1})
    await _emit(session_id, "tool_call", "analyst", {"tool": "aggregate", "findings_count": len(findings)})
    await _emit(session_id, "tool_call", "analyst", {"tool": "compare", "findings_count": len(findings)})
    await _emit(session_id, "node_end", "analyst", {"tools_run": ["aggregate", "compare"], "result_keys": list(analysis.keys())})
    await _emit(session_id, "node_start", "critic", {"message": "Reviewing analysis quality... (attempt 2/3)"})
    await _emit(session_id, "critic_decision", "critic", {"decision": "approve", "reasoning": "Retry addresses the query with multiple economic outcomes.", "feedback": "", "retries_used": 1, "retry_count": 1, "max_retries": 2})
    await _emit(session_id, "node_end", "critic", {"approved": True})
    await _emit(session_id, "node_start", "visualizer", {"message": "Rendering charts..."})
    await _emit(session_id, "chart_ready", "visualizer", {"charts": len(chart_specs), "chart_specs": chart_specs, "message": f"Rendered {len(chart_specs)} chart(s)"})
    await _emit(session_id, "node_end", "visualizer", {"chart_count": len(chart_specs)})
    await _emit(session_id, "node_start", "reporter", {"message": "Generating markdown research report..."})
    await _emit(session_id, "report_ready", "reporter", {"length": len(report), "report": report, "message": "Report ready"})
    await _emit(session_id, "node_end", "reporter", {})


async def _run_glp1_demo(session_id: str) -> None:
    findings = _glp1_findings()
    analysis = {
        "tools_used": ["aggregate", "compare"],
        "reasoning": "Multiple cognitive outcome metrics across different GLP-1 agonists.",
        "aggregate": aggregate(findings),
        "compare": compare(findings, "metric"),
    }
    chart_specs = _chart_specs(findings, analysis)
    report = (
        "# Research Report\n\n"
        "## Bottom line\n"
        "GLP-1 receptor agonists consistently improve cognitive outcomes: MMSE improved +2.3 points, "
        "memory recall accuracy rose +12.8%, and neuroinflammation (IL-6) fell −22.4%.\n\n"
        "## Key Findings\n"
        "- **MMSE score change**: +2.3 points — semaglutide 1mg/week, n=103, p=0.001\n"
        "- **Memory recall accuracy**: +12.8% — GLP-1 agonist, n=88, p=0.004\n"
        "- **Executive function**: +0.47 SD — dulaglutide, n=74, p=0.003\n"
        "- **Hippocampal volume**: +1.8% — liraglutide 1.8mg, n=67, p=0.012\n"
        "- **IL-6 (neuroinflammation)**: −22.4% — semaglutide, n=55, p=0.001\n\n"
        "## Evidence\n"
        "All five cognitive and neurological outcomes moved in the beneficial direction across "
        "different GLP-1 agonists and patient populations with T2D. The anti-inflammatory "
        "pathway (IL-6 reduction) may partially explain memory benefits.\n\n"
        "## Limitations\n"
        "Most trials enrolled patients with T2D; generalisability to non-diabetic populations "
        "requires further investigation."
    )
    await _emit(session_id, "node_start", "planner", {"message": "Decomposing: GLP-1 effects on cognition"})
    await _emit(session_id, "node_end", "planner", {
        "canonical_question": "What are the effects of GLP-1 receptor agonists on cognitive function?",
        "subqueries": ["GLP-1 receptor agonists cognitive function", "semaglutide memory neuroinflammation", "liraglutide hippocampus neuroprotection"],
        "rationale": "Split across memory, executive function, and neurobiological mechanisms.",
    })
    await _emit(session_id, "node_start", "discovery", {"message": "Searching for 3 subqueries..."})
    await _emit(session_id, "tool_result", "discovery", {"source": "semantic_scholar", "query": "GLP-1 receptor agonists cognitive function", "found": 6, "new": 5})
    await _emit(session_id, "node_end", "discovery", {"total_papers": 14})
    await _emit_cached_sources(session_id, findings)
    await _emit(session_id, "node_start", "extractor", {"message": "Extracting structured findings from 14 papers..."})
    await _emit(session_id, "tool_result", "extractor", {"findings_extracted": len(findings), "papers_processed": 14})
    await _emit(session_id, "node_end", "extractor", {"total_findings": len(findings)})
    await _emit(session_id, "node_start", "analyst", {"message": f"Analyzing {len(findings)} findings...", "findings_count": len(findings), "retry": 0})
    await _emit(session_id, "tool_call", "analyst", {"tool": "aggregate", "findings_count": len(findings)})
    await _emit(session_id, "tool_call", "analyst", {"tool": "compare", "findings_count": len(findings)})
    await _emit(session_id, "node_end", "analyst", {"tools_run": ["aggregate", "compare"], "result_keys": list(analysis.keys())})
    await _emit(session_id, "node_start", "critic", {"message": "Reviewing analysis quality... (attempt 1/3)"})
    await _emit(session_id, "critic_decision", "critic", {"decision": "approve", "reasoning": "Strong multi-metric analysis with consistent directionality.", "feedback": "", "retries_used": 0, "retry_count": 0, "max_retries": 2})
    await _emit(session_id, "node_end", "critic", {"approved": True})
    await _emit(session_id, "node_start", "visualizer", {"message": "Rendering charts..."})
    await _emit(session_id, "chart_ready", "visualizer", {"charts": len(chart_specs), "chart_specs": chart_specs, "message": f"Rendered {len(chart_specs)} chart(s)"})
    await _emit(session_id, "node_end", "visualizer", {"chart_count": len(chart_specs)})
    await _emit(session_id, "node_start", "reporter", {"message": "Generating markdown research report..."})
    await _emit(session_id, "report_ready", "reporter", {"length": len(report), "report": report, "message": "Report ready"})
    await _emit(session_id, "node_end", "reporter", {})


async def _run_microplastic_demo(session_id: str) -> None:
    findings = _microplastic_findings()
    analysis = {
        "tools_used": ["aggregate", "compare"],
        "reasoning": "Multiple gut health markers; critic requested broader comparison after initial inflammation-only pass.",
        "aggregate": aggregate(findings),
        "compare": compare(findings, "metric"),
    }
    chart_specs = _chart_specs(findings, analysis)
    report = (
        "# Research Report\n\n"
        "## Bottom line\n"
        "Microplastic exposure consistently harms gut microbiome health: diversity fell −0.31 Shannon units, "
        "inflammation rose +28%, and beneficial bacteria (Bifidobacterium) declined −24%.\n\n"
        "## Key Findings\n"
        "- **Shannon diversity index**: −0.31 — 10μg/kg/day exposure, n=42, p=0.005\n"
        "- **IL-6 inflammatory marker**: +28% — PET microplastic ingestion, n=38, p=0.001\n"
        "- **Gut permeability (TEER)**: −19% — chronic exposure, n=29, p=0.002\n"
        "- **Bifidobacterium abundance**: −24% — nanoplastic ingestion, n=51, p=0.001\n"
        "- **Butyrate-producing bacteria**: −16.5% — mixed microplastic diet, n=44, p=0.003\n\n"
        "## Critic note\n"
        "Initial analysis focused only on inflammation. Critic rejected it; retry incorporated "
        "diversity, permeability, and bacterial composition — revealing a coherent dysbiosis pattern.\n\n"
        "## Limitations\n"
        "Most evidence is from animal models. Human exposure studies are emerging but doses "
        "and particle sizes vary widely across studies."
    )
    await _emit(session_id, "node_start", "planner", {"message": "Decomposing: microplastics and gut microbiome"})
    await _emit(session_id, "node_end", "planner", {
        "canonical_question": "What is the effect of microplastic exposure on gut microbiome composition and function?",
        "subqueries": ["microplastics gut microbiome diversity", "polystyrene nanoparticles intestinal inflammation", "microplastics dysbiosis butyrate bacteria"],
        "rationale": "Split across diversity, inflammation, and specific bacterial taxa.",
    })
    await _emit(session_id, "node_start", "discovery", {"message": "Searching for 3 subqueries..."})
    await _emit(session_id, "tool_result", "discovery", {"source": "semantic_scholar", "query": "microplastics gut microbiome diversity", "found": 5, "new": 5})
    await _emit(session_id, "node_end", "discovery", {"total_papers": 13})
    await _emit_cached_sources(session_id, findings)
    await _emit(session_id, "node_start", "extractor", {"message": "Extracting structured findings from 13 papers..."})
    await _emit(session_id, "tool_result", "extractor", {"findings_extracted": len(findings), "papers_processed": 13})
    await _emit(session_id, "node_end", "extractor", {"total_findings": len(findings)})
    await _emit(session_id, "node_start", "analyst", {"message": f"Analyzing {len(findings)} findings...", "findings_count": len(findings), "retry": 0})
    await _emit(session_id, "tool_call", "analyst", {"tool": "aggregate", "findings_count": 2})
    await _emit(session_id, "node_end", "analyst", {"tools_run": ["aggregate"], "result_keys": ["tools_used", "reasoning", "aggregate"]})
    await _emit(session_id, "node_start", "critic", {"message": "Reviewing analysis quality... (attempt 1/3)"})
    await _emit(session_id, "critic_decision", "critic", {
        "decision": "reject",
        "reasoning": "Analysis only covered inflammation. Missing diversity, permeability, and bacterial taxa.",
        "feedback": "Re-run with compare across all five gut health metrics.",
        "retries_used": 0, "retry_count": 1, "max_retries": 2,
    })
    await _emit(session_id, "node_end", "critic", {"approved": False})
    await _emit(session_id, "node_start", "analyst", {"message": "Retry 1/2 — expanding to all gut microbiome metrics", "findings_count": len(findings), "retry": 1})
    await _emit(session_id, "tool_call", "analyst", {"tool": "aggregate", "findings_count": len(findings)})
    await _emit(session_id, "tool_call", "analyst", {"tool": "compare", "findings_count": len(findings)})
    await _emit(session_id, "node_end", "analyst", {"tools_run": ["aggregate", "compare"], "result_keys": list(analysis.keys())})
    await _emit(session_id, "node_start", "critic", {"message": "Reviewing analysis quality... (attempt 2/3)"})
    await _emit(session_id, "critic_decision", "critic", {"decision": "approve", "reasoning": "Full comparison across diversity, inflammation, permeability, and taxa.", "feedback": "", "retries_used": 1, "retry_count": 1, "max_retries": 2})
    await _emit(session_id, "node_end", "critic", {"approved": True})
    await _emit(session_id, "node_start", "visualizer", {"message": "Rendering charts..."})
    await _emit(session_id, "chart_ready", "visualizer", {"charts": len(chart_specs), "chart_specs": chart_specs, "message": f"Rendered {len(chart_specs)} chart(s)"})
    await _emit(session_id, "node_end", "visualizer", {"chart_count": len(chart_specs)})
    await _emit(session_id, "node_start", "reporter", {"message": "Generating markdown research report..."})
    await _emit(session_id, "report_ready", "reporter", {"length": len(report), "report": report, "message": "Report ready"})
    await _emit(session_id, "node_end", "reporter", {})


async def _run_vitamind_demo(session_id: str) -> None:
    findings = _vitamind_findings()
    analysis = {
        "tools_used": ["aggregate", "compare"],
        "reasoning": "Multiple depression severity and biomarker outcomes.",
        "aggregate": aggregate(findings),
        "compare": compare(findings, "metric"),
    }
    chart_specs = _chart_specs(findings, analysis)
    report = (
        "# Research Report\n\n"
        "## Bottom line\n"
        "Vitamin D supplementation reduces depression severity: HAM-D scores fell −4.2 points, "
        "response rate reached 42%, and adjunct use added −3.1 PHQ-9 points over antidepressant alone.\n\n"
        "## Key Findings\n"
        "- **Hamilton Depression Scale**: −4.2 points — D3 2000 IU/day, n=120, p=0.001\n"
        "- **Response rate**: 42% — D3 4000 IU/day vs 24% placebo, n=89, p=0.008\n"
        "- **Remission rate**: 26% — D3 4000 IU/day vs 14% placebo, n=89, p=0.02\n"
        "- **Serum 25(OH)D change**: +18 ng/mL — across supplemented arms, n=134, p=0.001\n"
        "- **PHQ-9 (adjunct)**: −3.1 points — Vitamin D + antidepressant vs antidepressant alone, n=76, p=0.001\n\n"
        "## Evidence\n"
        "Higher-dose supplementation (4000 IU/day) achieves better response and remission rates. "
        "Adjunct use with existing antidepressants shows additive benefit. "
        "The serum 25(OH)D rise confirms adequate bioavailability across trials.\n\n"
        "## Limitations\n"
        "Trial durations vary (8–26 weeks). Baseline 25(OH)D deficiency status was not always controlled."
    )
    await _emit(session_id, "node_start", "planner", {"message": "Decomposing: Vitamin D and depression"})
    await _emit(session_id, "node_end", "planner", {
        "canonical_question": "What is the effect of Vitamin D supplementation on depression severity and outcomes?",
        "subqueries": ["vitamin D supplementation depression randomised trial", "vitamin D antidepressant adjunct PHQ HAM-D", "25-hydroxyvitamin D serum levels mood disorders"],
        "rationale": "Split across clinical outcomes, adjunct use, and biomarker evidence.",
    })
    await _emit(session_id, "node_start", "discovery", {"message": "Searching for 3 subqueries..."})
    await _emit(session_id, "tool_result", "discovery", {"source": "semantic_scholar", "query": "vitamin D supplementation depression randomised trial", "found": 6, "new": 5})
    await _emit(session_id, "node_end", "discovery", {"total_papers": 15})
    await _emit_cached_sources(session_id, findings)
    await _emit(session_id, "node_start", "extractor", {"message": "Extracting structured findings from 15 papers..."})
    await _emit(session_id, "tool_result", "extractor", {"findings_extracted": len(findings), "papers_processed": 15})
    await _emit(session_id, "node_end", "extractor", {"total_findings": len(findings)})
    await _emit(session_id, "node_start", "analyst", {"message": f"Analyzing {len(findings)} findings...", "findings_count": len(findings), "retry": 0})
    await _emit(session_id, "tool_call", "analyst", {"tool": "aggregate", "findings_count": len(findings)})
    await _emit(session_id, "tool_call", "analyst", {"tool": "compare", "findings_count": len(findings)})
    await _emit(session_id, "node_end", "analyst", {"tools_run": ["aggregate", "compare"], "result_keys": list(analysis.keys())})
    await _emit(session_id, "node_start", "critic", {"message": "Reviewing analysis quality... (attempt 1/3)"})
    await _emit(session_id, "critic_decision", "critic", {"decision": "approve", "reasoning": "Strong multi-outcome analysis covering clinical and biomarker evidence.", "feedback": "", "retries_used": 0, "retry_count": 0, "max_retries": 2})
    await _emit(session_id, "node_end", "critic", {"approved": True})
    await _emit(session_id, "node_start", "visualizer", {"message": "Rendering charts..."})
    await _emit(session_id, "chart_ready", "visualizer", {"charts": len(chart_specs), "chart_specs": chart_specs, "message": f"Rendered {len(chart_specs)} chart(s)"})
    await _emit(session_id, "node_end", "visualizer", {"chart_count": len(chart_specs)})
    await _emit(session_id, "node_start", "reporter", {"message": "Generating markdown research report..."})
    await _emit(session_id, "report_ready", "reporter", {"length": len(report), "report": report, "message": "Report ready"})
    await _emit(session_id, "node_end", "reporter", {})


# ── Dispatcher ───────────────────────────────────────────────────────────────

async def run_cached_demo(session_id: str, query: str) -> bool:
    normalized = _normalize(query)
    if normalized == _normalize(SLEEP_QUERY):
        await _run_sleep_demo(session_id)
        return True
    if normalized == _normalize(WAGE_QUERY):
        await _run_wage_demo(session_id)
        return True
    if normalized == _normalize(GLP1_QUERY):
        await _run_glp1_demo(session_id)
        return True
    if normalized == _normalize(MICROPLASTIC_QUERY):
        await _run_microplastic_demo(session_id)
        return True
    if normalized == _normalize(VITAMIND_QUERY):
        await _run_vitamind_demo(session_id)
        return True
    return False
