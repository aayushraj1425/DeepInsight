import asyncio
import xml.etree.ElementTree as ET
import httpx

_BASE = "https://export.arxiv.org/api/query"
_NS = {"atom": "http://www.w3.org/2005/Atom"}
_HEADERS = {"User-Agent": "DeepQuery research demo"}


async def search_arxiv(query: str, limit: int = 6) -> list[dict]:
    """Search arXiv via the public Atom API. No auth needed."""
    async with httpx.AsyncClient(timeout=20.0, headers=_HEADERS) as http:
        resp = await http.get(
            _BASE,
            params={
                "search_query": f"all:{query}",
                "max_results": min(limit * 2, 20),
                "sortBy": "relevance",
            },
        )
        resp.raise_for_status()

    root = ET.fromstring(resp.text)
    papers = []

    for entry in root.findall("atom:entry", _NS):
        title_el = entry.find("atom:title", _NS)
        summary_el = entry.find("atom:summary", _NS)
        published_el = entry.find("atom:published", _NS)
        id_el = entry.find("atom:id", _NS)

        title = (title_el.text or "").strip().replace("\n", " ") if title_el is not None else ""
        abstract = (summary_el.text or "").strip().replace("\n", " ") if summary_el is not None else ""
        arxiv_url = (id_el.text or "").strip() if id_el is not None else ""
        arxiv_id = arxiv_url.split("/abs/")[-1] if "/abs/" in arxiv_url else ""

        year = None
        if published_el is not None and published_el.text:
            try:
                year = int(published_el.text[:4])
            except ValueError:
                pass

        if not title or len(abstract) < 150:
            continue

        papers.append({
            "paper_id":      f"arxiv:{arxiv_id}",
            "title":         title,
            "abstract":      abstract,
            "tldr":          "",
            "year":          year,
            "citation_count": 0,
            "venue":         "arXiv",
            "pub_types":     ["JournalArticle"],
            "openAccessPdf": {"url": f"https://arxiv.org/pdf/{arxiv_id}.pdf"} if arxiv_id else None,
            "externalIds":   {"ArXiv": arxiv_id} if arxiv_id else {},
            "url":           arxiv_url,
            "source":        "arxiv",
        })

    await asyncio.sleep(0.5)
    return papers[:limit]
