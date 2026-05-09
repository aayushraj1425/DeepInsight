import asyncio
import re

import httpx
from ddgs import DDGS


def web_search(query: str, max_results: int = 6) -> list[dict]:
    """Search DuckDuckGo and return results formatted as paper-like dicts."""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
    except Exception:
        return []

    papers = []
    for r in results:
        title = r.get("title", "")
        body = r.get("body", "")
        href = r.get("href", "")
        if title and body:
            papers.append({
                "paper_id": href,
                "title": title,
                "abstract": body,
                "url": href,
                "year": None,
                "citation_count": 0,
                "source": "web",
            })
    return papers


_TAG_RE = re.compile(r"<[^>]+>")
_SPACE_RE = re.compile(r"\s+")


async def _fetch_page_text(url: str, max_chars: int = 2500) -> str:
    try:
        async with httpx.AsyncClient(timeout=6.0, follow_redirects=True,
                                     headers={"User-Agent": "Mozilla/5.0"}) as http:
            resp = await http.get(url)
            if resp.status_code != 200:
                return ""
            text = _TAG_RE.sub(" ", resp.text)
            text = _SPACE_RE.sub(" ", text).strip()
            return text[:max_chars]
    except Exception:
        return ""


async def enrich_web_results(papers: list[dict]) -> list[dict]:
    """
    Fetch full page text for each web result and append it to the abstract.
    Runs all fetches in parallel with a per-page timeout.
    """
    urls = [p.get("url", "") for p in papers]
    page_texts = await asyncio.gather(*[_fetch_page_text(u) for u in urls])

    enriched = []
    for paper, page_text in zip(papers, page_texts):
        if page_text:
            paper = dict(paper)
            paper["abstract"] = paper["abstract"] + "\n\n" + page_text
        enriched.append(paper)
    return enriched
