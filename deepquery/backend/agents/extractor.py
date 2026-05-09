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
    metric: str = Field(description="The outcome or metric being measured")
    value: str = Field(description="Exact numeric value as written in the text, e.g. '23%', '1.5 SD', '$120K'")
    sample_size: Optional[int] = Field(None, description="Number of participants/samples if stated")
    ci: Optional[str] = Field(None, description="Confidence interval if reported")
    p_value: Optional[float] = Field(None, description="p-value if reported")
    intervention: Optional[str] = Field(None, description="Condition or intervention studied")
    source_quote: str = Field(description="EXACT verbatim sentence from the text containing the number")


class PaperFindings(BaseModel):
    findings: list[Finding] = Field(
        description="Findings with numbers explicitly in the source text. Empty list if none."
    )


def _build_source_text(paper: dict) -> str:
    """Layer 1: combine abstract + tldr into one source block."""
    parts = []
    if paper.get("abstract"):
        parts.append(paper["abstract"])
    tldr = paper.get("tldr") or ""
    if tldr and tldr not in (paper.get("abstract") or ""):
        parts.append(tldr)
    return "\n\n".join(parts).strip()


def _validate_findings(findings: list[Finding], source_text: str) -> list[Finding]:
    """
    Layer 2: drop any finding whose source_quote is not a real substring of the
    source text. Normalise whitespace before comparing to survive line breaks.
    Also require the value and quote to both contain a digit.
    """
    haystack = " ".join(source_text.split()).lower()
    valid = []
    for f in findings:
        # Value must contain a digit
        if not _NUMBER_RE.search(f.value):
            continue
        # Quote must contain a digit
        if not _NUMBER_RE.search(f.source_quote):
            continue
        # Quote must actually appear in the source text (substring check)
        needle = " ".join(f.source_quote.split()).lower()
        if len(needle) < 15:
            continue
        if needle not in haystack:
            continue
        valid.append(f)
    return valid


async def _extract_one(paper: dict) -> list[dict]:
    # Layer 1: build source text and skip if too thin
    source_text = _build_source_text(paper)
    if len(source_text) < 200:
        return []

    try:
        result: PaperFindings = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You extract numeric findings from a research paper.\n\n"
                        "RULES — absolute, no exceptions:\n"
                        "1. Only extract a finding if a SPECIFIC NUMBER is explicitly stated in the source text.\n"
                        "2. The `source_quote` field MUST be an EXACT verbatim sentence from the source text. "
                        "Do not paraphrase, summarise, or invent.\n"
                        "3. If the text has no specific numeric findings, return an empty list. "
                        "Returning nothing is correct and expected.\n"
                        "4. Never produce a finding whose number does not appear in the source text.\n"
                        "5. If the text says 'significant effect' or 'improved outcomes' without a "
                        "specific number, do NOT invent one — skip it.\n"
                        "6. Do not convert qualitative words ('majority', 'most', 'significant') into percentages."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Title: {paper['title']}\n"
                        f"Year: {paper.get('year')}\n\n"
                        f"Source text:\n\"\"\"\n{source_text}\n\"\"\""
                    ),
                },
            ],
            response_model=PaperFindings,
        )

        # Layer 2: validate every finding against the source text
        validated = _validate_findings(result.findings, source_text)

        rows = []
        for f in validated:
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
        payload={"message": f"Extracting findings from {len(papers)} sources..."}
    ))

    results = await asyncio.gather(*[_extract_one(p) for p in papers])
    all_findings = [f for paper_findings in results for f in paper_findings]

    await emit(sid, AgentEvent(
        type="tool_result", agent="extractor",
        payload={"findings_extracted": len(all_findings), "papers_processed": len(papers)}
    ))
    await emit(sid, AgentEvent(
        type="node_end", agent="extractor",
        payload={"total_findings": len(all_findings)}
    ))
    return {"findings": all_findings}
