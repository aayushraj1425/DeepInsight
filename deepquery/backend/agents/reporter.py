from collections import Counter

from pydantic import BaseModel, Field

from agents.state import AgentState
from events import AgentEvent
from llm import client
from runtime import emit
from tools.prompting import clip_text, compact_json, slim_datasets, slim_findings, slim_paper_sources


class ResearchReport(BaseModel):
    markdown: str = Field(description="Professional markdown intelligence report for the user")


def _grouped_findings(findings: list[dict], source_type: str) -> list[dict]:
    return [finding for finding in findings if finding.get("source_type") == source_type]


async def reporter_node(state: AgentState) -> dict:
    sid = state["session_id"]
    chart_summaries = [
        {
            "template": chart.get("template"),
            "title": chart.get("title"),
            "insight": chart.get("insight"),
            "explanation": chart.get("explanation"),
            "source_titles": chart.get("source_titles", []),
            "caveat": chart.get("caveat"),
            "confidence": chart.get("confidence"),
        }
        for chart in state.get("chart_specs", [])
    ]
    findings = state.get("findings", [])
    upload_findings = _grouped_findings(findings, "upload")
    scholar_findings = _grouped_findings(findings, "semantic_scholar")
    openalex_findings = _grouped_findings(findings, "openalex")
    arxiv_findings = _grouped_findings(findings, "arxiv")
    crossref_findings = _grouped_findings(findings, "crossref")
    dataset_findings = _grouped_findings(findings, "dataset")
    source_counts = Counter(finding.get("source_title", "Unknown") for finding in findings)

    await emit(sid, AgentEvent(
        type="node_start", agent="reporter",
        payload={"message": "Generating markdown research report..."}
    ))

    result: ResearchReport = await client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": (
                    "Write a professional intelligence report, not a chatbot answer. Use the provided evidence only. "
                    "Every major factual or numerical claim must cite source titles inline in parentheses. "
                    "Every bullet in ## Key Findings must contain at least one source-title citation. "
                    "Data-backed claims should state the dataset/report/paper title supporting them; if the evidence only "
                    "supports a hypothesis, label it as a hypothesis rather than a finding. "
                    "Do not invent citations, percentages, forecasts, or causal claims. If the evidence is weak, say so. "
                    "Do not use sensational language. Separate facts, interpretation, scenarios, and uncertainty.\n\n"
                    "Use this exact section structure:\n"
                    "## Executive Summary\n"
                    "## Key Findings\n"
                    "## Data Analysis\n"
                    "## Contradictory Evidence\n"
                    "## Historical Comparisons\n"
                    "## Future Scenarios\n"
                    "## Confidence Levels\n"
                    "## Citations\n"
                    "## Appendix: Data and Methodology\n\n"
                    "The Citations section must list the source titles used, grouped by datasets, papers, uploaded files, and reports. "
                    "The Appendix must explain what was searched, what was validated, and what was not strong enough to support. "
                    "If a claim appears in the fact-check red flags, do not present it as true."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Research question: {clip_text(state['query'], 1200)}\n"
                    f"Research plan: {compact_json(state.get('research_plan', {}), max_chars=9000)}\n"
                    f"Fact-check approved: {state.get('approved')}\n"
                    f"Fact-check report: {compact_json(state.get('fact_check_report', {}), max_chars=12000)}\n"
                    f"Deep reasoning synthesis: {compact_json(state.get('reasoning', {}), max_chars=14000)}\n"
                    f"Economic/scenario model: {compact_json(state.get('economic_model', {}), max_chars=14000)}\n"
                    f"Validation report: {compact_json(state.get('validation_report', {}), max_chars=12000)}\n"
                    f"Uploaded document brief: {clip_text(state.get('document_brief') or 'none', 3500)}\n"
                    f"Research paper sources searched: {compact_json(slim_paper_sources(state.get('paper_sources', []), limit=12), max_chars=9000)}\n"
                    f"Public dataset candidates: {compact_json(slim_datasets(state.get('datasets', []), limit=10), max_chars=9000)}\n"
                    f"Findings from uploaded files: {compact_json(slim_findings(upload_findings, limit=10), max_chars=9000)}\n"
                    f"Findings from Semantic Scholar: {compact_json(slim_findings(scholar_findings, limit=10), max_chars=9000)}\n"
                    f"Findings from OpenAlex: {compact_json(slim_findings(openalex_findings, limit=10), max_chars=9000)}\n"
                    f"Findings from arXiv: {compact_json(slim_findings(arxiv_findings, limit=8), max_chars=7000)}\n"
                    f"Findings from Crossref: {compact_json(slim_findings(crossref_findings, limit=8), max_chars=7000)}\n"
                    f"Computed findings from public datasets: {compact_json(slim_findings(dataset_findings, limit=12), max_chars=10000)}\n"
                    f"Dataset analysis profiles: {compact_json(state.get('dataset_analysis', {}), max_chars=12000)}\n"
                    f"Analysis: {compact_json(state.get('analysis', {}), max_chars=14000)}\n"
                    f"Charts: {compact_json(chart_summaries, max_chars=5000)}\n"
                    f"Source finding counts: {compact_json(dict(source_counts), max_chars=4000)}"
                ),
            },
        ],
        response_model=ResearchReport,
    )

    report = result.markdown
    await emit(sid, AgentEvent(
        type="report_ready", agent="reporter",
        payload={"length": len(report), "report": report, "message": "Report ready"}
    ))
    await emit(sid, AgentEvent(
        type="node_end", agent="reporter",
        payload={}
    ))
    return {"report": report}
