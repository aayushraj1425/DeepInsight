import asyncio

import httpx

_BASE = "https://api.semanticscholar.org/graph/v1"
_FIELDS = "title,abstract,year,authors,citationCount,paperId"
_HEADERS = {"User-Agent": "DeepQuery hackathon research demo"}
_RETRY_STATUSES = {429, 500, 502, 503, 504}


async def search_papers(query: str, limit: int = 6) -> list[dict]:
    params = {"query": query, "fields": _FIELDS, "limit": limit}
    async with httpx.AsyncClient(timeout=20.0, headers=_HEADERS) as http:
        for attempt in range(3):
            resp = await http.get(f"{_BASE}/paper/search", params=params)
            if resp.status_code not in _RETRY_STATUSES:
                resp.raise_for_status()
                break

            if attempt == 2:
                resp.raise_for_status()

            retry_after = resp.headers.get("retry-after")
            try:
                delay = float(retry_after) if retry_after else 1.5 * (attempt + 1)
            except ValueError:
                delay = 1.5 * (attempt + 1)
            await asyncio.sleep(delay)

    papers = []
    for p in resp.json().get("data", []):
        if p.get("abstract"):
            papers.append({
                "paper_id":      p.get("paperId", ""),
                "title":         p.get("title", ""),
                "abstract":      p.get("abstract", ""),
                "year":          p.get("year"),
                "citation_count": p.get("citationCount", 0),
            })
    return papers
