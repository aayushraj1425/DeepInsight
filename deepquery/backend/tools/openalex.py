import httpx

_BASE = "https://api.openalex.org/works"
_HEADERS = {
    "User-Agent": "DeepQuery research demo (mailto:research@deepquery.app)",
}


def _reconstruct_abstract(inverted_index: dict | None) -> str:
    """OpenAlex stores abstracts as {word: [positions]}. Reconstruct to plain text."""
    if not inverted_index:
        return ""
    positions: list[tuple[int, str]] = []
    for word, pos_list in inverted_index.items():
        for pos in pos_list:
            positions.append((pos, word))
    positions.sort(key=lambda x: x[0])
    return " ".join(word for _, word in positions)


async def search_openalex(query: str, limit: int = 6) -> list[dict]:
    """
    Search OpenAlex — broad academic index, free, no auth, no rate limiting.
    Good fallback when Semantic Scholar is rate-limited.
    """
    async with httpx.AsyncClient(timeout=20.0, headers=_HEADERS) as http:
        resp = await http.get(
            _BASE,
            params={
                "search": query,
                "per-page": min(limit * 2, 20),
                "select": "id,title,abstract_inverted_index,publication_year,cited_by_count,doi,primary_location,type",
                "sort": "relevance_score:desc",
            },
        )
        resp.raise_for_status()

    results = resp.json().get("results", [])
    papers = []

    for r in results:
        title = (r.get("title") or "").strip()
        abstract = _reconstruct_abstract(r.get("abstract_inverted_index"))
        year = r.get("publication_year")
        citations = r.get("cited_by_count") or 0
        doi = r.get("doi") or ""
        url = doi if doi.startswith("http") else (f"https://doi.org/{doi}" if doi else "")

        venue = ""
        loc = r.get("primary_location") or {}
        source = loc.get("source") or {}
        if isinstance(source, dict):
            venue = source.get("display_name") or ""

        work_type = r.get("type") or ""
        pub_types = ["JournalArticle"] if work_type in ("article", "review") else []

        if not title or len(abstract) < 150:
            continue
        if citations < 2 and not pub_types:
            continue

        papers.append({
            "paper_id":      f"oa:{r.get('id', '').split('/')[-1]}",
            "title":         title,
            "abstract":      abstract,
            "tldr":          "",
            "year":          year,
            "citation_count": citations,
            "venue":         venue,
            "pub_types":     pub_types,
            "openAccessPdf": None,
            "externalIds":   {"DOI": doi} if doi else {},
            "url":           url,
            "source":        "openalex",
        })

    return papers[:limit]
