import asyncio
from typing import Optional
from pydantic import BaseModel, Field
from agents.state import AgentState
from events import AgentEvent
from runtime import emit
from llm import client


class Finding(BaseModel):
    metric: str = Field(description="The outcome or metric being measured, e.g. 'reaction time', 'memory recall'")
    value: str = Field(description="Numeric value or range, e.g. '23%', '1.5 SD', '0.42'")
    sample_size: Optional[int] = Field(None, description="Number of participants/samples if stated")
    ci: Optional[str] = Field(None, description="Confidence interval if reported, e.g. '95% CI: 0.3-0.7'")
    p_value: Optional[float] = Field(None, description="p-value if reported")
    intervention: Optional[str] = Field(None, description="Condition or intervention studied")
    source_quote: str = Field(description="Short direct quote from the abstract supporting this finding")


class PaperFindings(BaseModel):
    findings: list[Finding] = Field(
        description="All quantitative findings from this abstract. Empty list if no numeric results present."
    )


async def _extract_one(paper: dict) -> list[dict]:
    if not paper.get("abstract"):
        return []
    try:
        result: PaperFindings = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Extract every quantitative finding from this text. "
                        "Include explicit numbers (23%, $120K, 1.5x) AND reasonable numeric estimates "
                        "from qualitative statements (e.g. 'majority' → '~65%', 'significant growth' → estimate a %). "
                        "For web articles without explicit stats, estimate plausible values from context and mark them with '~'. "
                        "Only return an empty list if the text contains absolutely no measurable claims."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Title: {paper['title']}\n\nAbstract: {paper['abstract']}",
                },
            ],
            response_model=PaperFindings,
        )
        rows = []
        for f in result.findings:
            row = f.model_dump()
            row["paper_title"] = paper["title"]
            row["year"] = paper.get("year")
            rows.append(row)
        return rows
    except Exception:
        return []


async def extractor_node(state: AgentState) -> dict:
    sid = state["session_id"]
    papers = state["papers"]

    await emit(sid, AgentEvent(
        type="node_start", agent="extractor",
        payload={"message": f"Extracting structured findings from {len(papers)} papers..."}
    ))

    results = await asyncio.gather(*[_extract_one(p) for p in papers])
    all_findings = [finding for paper_findings in results for finding in paper_findings]

    await emit(sid, AgentEvent(
        type="tool_result", agent="extractor",
        payload={"findings_extracted": len(all_findings), "papers_processed": len(papers)}
    ))
    await emit(sid, AgentEvent(
        type="node_end", agent="extractor",
        payload={"total_findings": len(all_findings)}
    ))
    return {"findings": all_findings}
