import asyncio
import httpx

_BASE = "https://api.semanticscholar.org/graph/v1"
_FIELDS = "title,abstract,year,authors,citationCount,paperId,tldr,venue,publicationTypes"
_HEADERS = {"User-Agent": "DeepQuery research demo"}
_RETRY_STATUSES = {429, 500, 502, 503, 504}

# Publication types that are actual peer-reviewed research
_ACCEPTED_TYPES = {"JournalArticle", "Review", "MetaAnalysis", "ClinicalTrial"}


async def search_papers(query: str, limit: int = 6) -> list[dict]:
    # Over-fetch 3x so we have room to filter
    params = {
        "query": query,
        "fields": _FIELDS,
        "limit": min(limit * 3, 20),
        "year": "2010-2026",
    }
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

    raw = resp.json().get("data", [])

    # ── Quality filter ──────────────────────────────────────────────────────
    filtered = []
    for p in raw:
        abstract = p.get("abstract") or ""

        # Must have a real abstract (not a stub)
        if len(abstract) < 300:
            continue

        # Prefer journal articles / reviews; fall back to anything with citations
        pub_types = p.get("publicationTypes") or []
        is_peer_reviewed = any(t in _ACCEPTED_TYPES for t in pub_types)
        has_citations = (p.get("citationCount") or 0) >= 5

        if not (is_peer_reviewed or has_citations):
            continue

        tldr_text = (p.get("tldr") or {}).get("text") or ""

        filtered.append({
            "paper_id":       p.get("paperId", ""),
            "title":          p.get("title", ""),
            "abstract":       abstract,
            "tldr":           tldr_text,
            "year":           p.get("year"),
            "citation_count": p.get("citationCount", 0),
            "venue":          p.get("venue") or "",
            "pub_types":      pub_types,
        })

    # Sort: peer-reviewed first, then by citation count
    filtered.sort(key=lambda p: (
        any(t in _ACCEPTED_TYPES for t in p["pub_types"]),
        p["citation_count"],
    ), reverse=True)

    return filtered[:limit]
