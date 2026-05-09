import asyncio
import re
from typing import Optional
from pydantic import BaseModel, Field
from agents.state import AgentState
from events import AgentEvent
from runtime import emit
from llm import client

_NUMBER_RE = re.compile(r"\d")


class Finding(BaseModel):
    metric: str = Field(description="The outcome or metric being measured, e.g. 'reaction time', 'memory recall'")
    value: str = Field(description="Numeric value or range explicitly stated in the text, e.g. '23%', '1.5 SD', '$120K'")
    sample_size: Optional[int] = Field(None, description="Number of participants/samples if stated")
    ci: Optional[str] = Field(None, description="Confidence interval if reported, e.g. '95% CI: 0.3-0.7'")
    p_value: Optional[float] = Field(None, description="p-value if reported")
    intervention: Optional[str] = Field(None, description="Condition or intervention studied")
    source_quote: str = Field(description="Exact short quote from the text that contains the numeric value")


class PaperFindings(BaseModel):
    findings: list[Finding] = Field(
        description="Quantitative findings with numbers explicitly present in the source text. Empty list if no real numbers exist."
    )


def _is_valid(finding: dict) -> bool:
    """Drop findings where the value has no digit (hallucinated estimates like '~moderate')."""
    value = finding.get("value", "")
    quote = finding.get("source_quote", "")
    # Value must contain at least one digit
    if not _NUMBER_RE.search(value):
        return False
    # Source quote must also contain at least one digit — proves the number came from the text
    if not _NUMBER_RE.search(quote):
        return False
    return True


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
                        "Extract quantitative findings that are EXPLICITLY stated with a number in the text. "
                        "Only extract a finding if:\n"
                        "  1. The value contains an actual number (%, $, ratio, count, score, etc.)\n"
                        "  2. That number appears verbatim in the source text\n"
                        "  3. The source_quote field contains the sentence where that number appears\n\n"
                        "DO NOT estimate, infer, or invent numbers. "
                        "DO NOT convert qualitative words ('majority', 'significant') into percentages. "
                        "If the text has no explicit numbers, return an empty list."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Title: {paper['title']}\n\nText: {paper['abstract']}",
                },
            ],
            response_model=PaperFindings,
        )
        rows = []
        for f in result.findings:
            row = f.model_dump()
            row["paper_title"] = paper["title"]
            row["year"] = paper.get("year")
            # Hard filter: discard any finding without a real number in both value and quote
            if _is_valid(row):
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
