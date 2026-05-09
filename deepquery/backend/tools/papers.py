import httpx

_BASE = "https://api.semanticscholar.org/graph/v1"
_FIELDS = "title,abstract,year,authors,citationCount,paperId"


async def search_papers(query: str, limit: int = 6) -> list[dict]:
    params = {"query": query, "fields": _FIELDS, "limit": limit}
    async with httpx.AsyncClient(timeout=15.0) as http:
        resp = await http.get(f"{_BASE}/paper/search", params=params)
        resp.raise_for_status()
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
