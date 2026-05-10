import asyncio
import re
from typing import Optional
from pydantic import BaseModel, Field
from agents.state import AgentState
from events import AgentEvent
from runtime import emit
from llm import client
from tools.paper_fetcher import fetch_full_text

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
    """Layer 1: combine abstract + tldr into one source block (used as fallback)."""
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


def _source_url(paper: dict) -> str:
    paper_id = paper.get("paper_id", "")
    if paper.get("url"):
        return paper["url"]
    if paper_id and not paper_id.startswith(("file:", "pmid:", "arxiv:", "oa:")):
        return f"https://www.semanticscholar.org/paper/{paper_id}"
    return ""


async def _extract_one(paper: dict) -> list[dict]:
    # Fetch the best available text: full paper body > abstract+tldr
    source_text = await fetch_full_text(paper)

    # Also keep abstract+tldr for the substring validator (full text contains them)
    abstract_text = _build_source_text(paper)

    # Use whichever is longer as the validation haystack
    validator_text = source_text if len(source_text) >= len(abstract_text) else abstract_text

    if len(source_text) < 200:
        return []

    try:
        result: PaperFindings = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a parser. The paper text already contains the data — locate and copy it out.\n\n"
                        "Extract numeric findings: percentages, counts, scores, effect sizes, p-values, "
                        "dollar amounts, durations, ratios — any explicit number tied to a result.\n\n"
                        "ABSOLUTE RULES:\n"
                        "1. Every number in a finding MUST appear verbatim in the source text — do not estimate, "
                        "round, or infer.\n"
                        "2. `source_quote` MUST be a word-for-word copy of the sentence containing the number. "
                        "Do not paraphrase or shorten.\n"
                        "3. If the text has no explicit numeric results, return an empty list. "
                        "An empty list is correct when there are no numbers.\n"
                        "4. Do not convert qualitative words ('majority', 'most', 'significant') into numbers.\n"
                        "5. Do not invent, estimate, or extrapolate any value."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Title: {paper['title']}\n"
                        f"Year: {paper.get('year')}\n\n"
                        f"Paper text:\n\"\"\"\n{source_text}\n\"\"\"\n\n"
                        "Parse out every numeric finding. Copy each number-containing sentence verbatim into source_quote."
                    ),
                },
            ],
            response_model=PaperFindings,
        )

        # Layer 2: validate every finding against the fetched text
        validated = _validate_findings(result.findings, validator_text)

        rows = []
        for f in validated:
            row = f.model_dump()
            row["paper_title"] = paper["title"]
            row["year"] = paper.get("year")
            row["paper_id"] = paper.get("paper_id", "")
            row["source"] = paper.get("source") or "semantic_scholar"
            row["url"] = _source_url(paper)
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
