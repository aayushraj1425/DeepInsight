import asyncio
from typing import Optional

from pydantic import BaseModel, Field

from agents.state import AgentState
from events import AgentEvent
from llm import client
from runtime import emit
from tools.prompting import clip_text


class Finding(BaseModel):
    metric: str = Field(description="The outcome or metric being measured, e.g. 'reaction time', 'memory recall'")
    value: str = Field(description="Numeric value or range, e.g. '23%', '1.5 SD', '0.42'")
    sample_size: Optional[int] = Field(None, description="Number of participants/samples if stated")
    ci: Optional[str] = Field(None, description="Confidence interval if reported, e.g. '95% CI: 0.3-0.7'")
    p_value: Optional[float] = Field(None, description="p-value if reported")
    intervention: Optional[str] = Field(None, description="Condition or intervention studied")
    source_quote: str = Field(description="Short direct quote from the abstract supporting this finding")
    unit_hint: Optional[str] = Field(None, description="A brief unit label such as percent, score, seconds, or count")


class PaperFindings(BaseModel):
    findings: list[Finding] = Field(
        description="All quantitative findings from this abstract. Empty list if no numeric results present."
    )


def _document_context(document: dict) -> str:
    snippets = document.get("numeric_findings") or []
    excerpt = document.get("excerpt") or ""
    full_text = document.get("full_text_truncated") or ""

    parts = [
        f"Document excerpt:\n{clip_text(excerpt, 900)}",
        "Numeric snippets:\n" + ("\n".join(f"- {snippet}" for snippet in snippets[:16]) if snippets else "- none"),
    ]
    if full_text and full_text != excerpt:
        parts.append(f"Leading text:\n{clip_text(full_text, 7000)}")
    return "\n\n".join(parts)


async def _extract_source_findings(query: str, source: dict, source_type: str, semaphore: asyncio.Semaphore) -> list[dict]:
    if source_type == "upload" and source.get("error"):
        return []

    title = source.get("title") or source.get("name") or "Untitled source"
    year = source.get("year")
    source_id = source.get("source_id", "")
    content = _document_context(source) if source_type == "upload" else clip_text(source.get("abstract", ""), 5000)

    if not content:
        return []

    async with semaphore:
        result: PaperFindings = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Extract every quantitative finding from the provided research text. "
                        "Only include results or numeric claims that are explicitly stated. "
                        "Return an empty list if there are no useful numeric findings. "
                        "Keep source_quote short and preserve the original direction/sign of the value."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Research question: {clip_text(query, 1200)}\n"
                        f"Source type: {source_type}\n"
                        f"Source title: {clip_text(title, 260)}\n\n"
                        f"Content:\n{clip_text(content, 8000)}"
                    ),
                },
            ],
            response_model=PaperFindings,
        )

    rows: list[dict] = []
    for finding in result.findings:
        row = finding.model_dump()
        row["paper_title"] = title
        row["year"] = year
        row["source_type"] = source_type
        row["source_title"] = title
        row["source_id"] = source_id
        rows.append(row)
    return rows


async def extractor_node(state: AgentState) -> dict:
    sid = state["session_id"]
    papers = state["papers"]
    documents = state.get("documents", [])
    dataset_findings = state.get("dataset_findings", [])

    await emit(sid, AgentEvent(
        type="node_start", agent="extractor",
        payload={"message": f"Extracting structured findings from {len(documents)} document(s), {len(papers)} papers, and {len(dataset_findings)} dataset statistic(s)..."}
    ))

    semaphore = asyncio.Semaphore(4)
    tasks = [
        _extract_source_findings(state["query"], document, "upload", semaphore)
        for document in documents
    ] + [
        _extract_source_findings(state["query"], paper, paper.get("source_type", "semantic_scholar"), semaphore)
        for paper in papers
        if paper.get("abstract")
    ]

    all_findings: list[dict] = list(dataset_findings)
    if tasks:
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for result in results:
            if isinstance(result, Exception):
                continue
            all_findings.extend(result)

    await emit(sid, AgentEvent(
        type="tool_result", agent="extractor",
        payload={
            "findings_extracted": len(all_findings),
            "papers_processed": len(papers),
            "documents_processed": len(documents),
        }
    ))
    await emit(sid, AgentEvent(
        type="node_end", agent="extractor",
        payload={"total_findings": len(all_findings)}
    ))
    return {"findings": all_findings}
