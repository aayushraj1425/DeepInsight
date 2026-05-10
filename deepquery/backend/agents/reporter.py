from typing import Literal

from pydantic import BaseModel, Field
from agents.state import AgentState
from events import AgentEvent
from llm import client
from runtime import emit


class ResearchReport(BaseModel):
    executive_summary: str = Field(
        description="One direct, decision-support answer to the research question grounded only in provided evidence"
    )
    confidence: Literal["high", "moderate", "low"] = Field(
        description="Overall confidence based on finding count, sample sizes, statistical support, and source quality"
    )
    most_reliable_result: str = Field(
        description="The strongest or most reliable specific result, mentioning n/p-value when available"
    )
    main_limitation: str = Field(
        description="The most important caveat that should temper interpretation"
    )
    markdown: str = Field(description="Concise markdown research report for the user")


def _paper_summaries(papers: list[dict], max_papers: int = 8) -> str:
    """Build a compact summary of each paper for the reporter to synthesize from."""
    lines = []
    for p in papers[:max_papers]:
        title = p.get("title", "Untitled")
        year = p.get("year") or ""
        venue = p.get("venue") or p.get("source") or ""
        abstract = (p.get("abstract") or "")[:600]
        tldr = p.get("tldr") or ""
        summary = tldr if tldr else abstract
        lines.append(f"• [{year}] {title} ({venue})\n  {summary}")
    return "\n\n".join(lines)


async def reporter_node(state: AgentState) -> dict:
    sid = state["session_id"]
    findings = state.get("findings", [])
    papers = state.get("papers", [])
    chart_summaries = [
        {
            "template": chart.get("template"),
            "title": chart.get("title"),
            "insight": chart.get("insight"),
        }
        for chart in state.get("chart_specs", [])
    ]

    await emit(sid, AgentEvent(
        type="node_start", agent="reporter",
        payload={"message": "Generating markdown research report..."}
    ))

    paper_context = _paper_summaries(papers)
    has_findings = len(findings) >= 2

    result: ResearchReport = await client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": (
                    "Write a decision-support research synthesis grounded in the provided sources.\n\n"
                    "You have two inputs: (A) extracted numeric findings with source quotes, "
                    "and (B) paper/article summaries with their abstracts.\n\n"
                    "RULES:\n"
                    "1. executive_summary must be a direct answer to the research question, not a generic overview. "
                    "Mention the evidence base size when useful.\n"
                    "2. confidence must reflect evidence quality: high only for multiple aligned findings with "
                    "clear p-values/sample sizes; moderate for mixed/sparse evidence; low for weak or mostly qualitative evidence.\n"
                    "3. most_reliable_result should prefer statistically significant findings with larger sample sizes.\n"
                    "4. Use ## Bottom line in markdown for a 1-2 sentence answer to the research question.\n"
                    "5. Use ## Key Findings for bullet points. "
                    "   - If numeric findings exist: cite the number AND the paper title.\n"
                    "     Format: **[metric]**: [value] — [source title], [year]\n"
                    "   - If numeric findings are sparse or absent: synthesize the key takeaways "
                    "     from the paper summaries instead. Name the paper for each point.\n"
                    "6. Use ## What the Research Says for a 2-4 paragraph synthesis drawing on "
                    "   the paper abstracts. Be specific — name studies, describe findings, "
                    "   explain mechanisms mentioned in the abstracts.\n"
                    "7. Use ## Limitations to flag: sparse quantitative data, web-only sources, "
                    "   conflicting findings, or gaps in the literature.\n"
                    "8. NEVER invent numbers. If a number isn't in the findings list, don't cite it.\n"
                    "9. If sources are web articles rather than peer-reviewed papers, say so."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Research question: {state['query']}\n\n"
                    f"=== Numeric findings (extracted & validated) ===\n"
                    f"{findings[:12] if has_findings else 'None extracted.'}\n\n"
                    f"=== Analysis of findings ===\n"
                    f"{state.get('analysis', {})}\n\n"
                    f"=== Paper / article summaries ===\n"
                    f"{paper_context}\n\n"
                    f"=== Chart insights ===\n"
                    f"{chart_summaries}"
                ),
            },
        ],
        response_model=ResearchReport,
    )

    report = result.markdown
    synthesis = {
        "answer": result.executive_summary,
        "confidence": result.confidence,
        "mostReliableResult": result.most_reliable_result,
        "mainLimitation": result.main_limitation,
        "evidenceCount": len(findings),
        "studiesCount": len({f.get("paper_title") for f in findings if f.get("paper_title")}) or len(papers),
    }
    await emit(sid, AgentEvent(
        type="synthesis_ready", agent="reporter",
        payload={"synthesis": synthesis, "message": "Synthesis ready"}
    ))
    await emit(sid, AgentEvent(
        type="report_ready", agent="reporter",
        payload={"length": len(report), "report": report, "synthesis": synthesis, "message": "Report ready"}
    ))
    await emit(sid, AgentEvent(
        type="node_end", agent="reporter",
        payload={}
    ))
    return {"report": report, "synthesis": synthesis}
