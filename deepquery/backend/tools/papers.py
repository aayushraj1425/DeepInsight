import asyncio
import math
import os
import random
import re
import time
import xml.etree.ElementTree as ET
from urllib.parse import quote_plus

import httpx

_BASE = "https://api.semanticscholar.org/graph/v1"
_FIELDS = "title,abstract,year,authors,citationCount,paperId"
_TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9-]{1,}")
_RETRY_STATUSES = {429, 500, 502, 503, 504}
_CACHE_TTL_SECONDS = 15 * 60

_request_lock = asyncio.Lock()
_next_request_at = 0.0
_search_cache: dict[tuple[str, int], tuple[float, list[dict]]] = {}


class SemanticScholarRateLimitError(RuntimeError):
    pass


def _api_key() -> str:
    return (os.getenv("SEMANTIC_SCHOLAR_API_KEY") or "").strip()


def _headers() -> dict[str, str]:
    headers = {"User-Agent": "DeepQuery hackathon research demo"}
    key = _api_key()
    if key:
        headers["x-api-key"] = key
    return headers


def _min_request_interval() -> float:
    return 1.05 if _api_key() else 2.5


async def _wait_for_turn() -> None:
    global _next_request_at

    async with _request_lock:
        now = time.monotonic()
        wait_time = max(0.0, _next_request_at - now)
        if wait_time > 0:
            await asyncio.sleep(wait_time)
        _next_request_at = time.monotonic() + _min_request_interval()


def _cache_key(query: str, limit: int) -> tuple[str, int]:
    return (" ".join(query.lower().split()), limit)


def _get_cached(query: str, limit: int) -> list[dict] | None:
    cached = _search_cache.get(_cache_key(query, limit))
    if not cached:
        return None

    cached_at, papers = cached
    if time.time() - cached_at > _CACHE_TTL_SECONDS:
        _search_cache.pop(_cache_key(query, limit), None)
        return None

    return [dict(paper) for paper in papers]


def _set_cached(query: str, limit: int, papers: list[dict]) -> None:
    _search_cache[_cache_key(query, limit)] = (time.time(), [dict(paper) for paper in papers])


def _tokenize(*parts: str) -> set[str]:
    tokens: set[str] = set()
    for part in parts:
        tokens.update(_TOKEN_RE.findall((part or "").lower()))
    return tokens


def _paper_url(paper_id: str, title: str) -> str:
    if paper_id:
        return f"https://www.semanticscholar.org/paper/{paper_id}"
    return f"https://www.semanticscholar.org/search?q={quote_plus(title)}"


def _paper_source_id(paper_id: str, title: str) -> str:
    return f"paper:{paper_id or quote_plus(title.lower())}"


def _abstract_from_openalex(inverted_index: dict | None) -> str:
    if not inverted_index:
        return ""

    positions: list[tuple[int, str]] = []
    for word, offsets in inverted_index.items():
        for offset in offsets:
            positions.append((int(offset), word))
    positions.sort(key=lambda item: item[0])
    return " ".join(word for _, word in positions)


def _score_paper(paper: dict, query_tokens: set[str], keyword_tokens: set[str]) -> float:
    title_tokens = _tokenize(paper.get("title", ""))
    abstract_tokens = _tokenize(paper.get("abstract", ""))
    citation_count = max(int(paper.get("citation_count", 0) or 0), 0)

    score = 0.0
    score += 3.0 * len(query_tokens & title_tokens)
    score += 1.5 * len(query_tokens & abstract_tokens)
    score += 2.0 * len(keyword_tokens & title_tokens)
    score += 1.0 * len(keyword_tokens & abstract_tokens)
    score += min(math.log10(citation_count + 1), 4.0)
    return score


def rerank_papers(
    papers: list[dict],
    query: str,
    document_keywords: list[str] | None = None,
    limit: int | None = None,
) -> list[dict]:
    query_tokens = _tokenize(query)
    keyword_tokens = _tokenize(*(document_keywords or []))

    ranked = []
    for paper in papers:
        enriched = dict(paper)
        enriched["ranking_score"] = round(_score_paper(enriched, query_tokens, keyword_tokens), 4)
        ranked.append(enriched)

    ranked.sort(
        key=lambda paper: (
            paper.get("ranking_score", 0),
            paper.get("citation_count", 0),
            paper.get("year") or 0,
        ),
        reverse=True,
    )
    return ranked[:limit] if limit is not None else ranked


async def _request_search(query: str, limit: int) -> httpx.Response:
    params = {"query": query, "fields": _FIELDS, "limit": limit}
    last_response: httpx.Response | None = None

    async with httpx.AsyncClient(timeout=25.0, headers=_headers()) as http:
        for attempt in range(5):
            await _wait_for_turn()
            response = await http.get(f"{_BASE}/paper/search", params=params)
            last_response = response

            if response.status_code not in _RETRY_STATUSES:
                response.raise_for_status()
                return response

            if response.status_code == 429 and attempt == 4:
                if _api_key():
                    raise SemanticScholarRateLimitError(
                        "Semantic Scholar rate limit reached. This key is limited to about 1 request/second, so retry in a few seconds."
                    )
                raise SemanticScholarRateLimitError(
                    "Semantic Scholar rate limit reached. Retry shortly or add SEMANTIC_SCHOLAR_API_KEY to backend/.env."
                )

            if attempt == 4:
                response.raise_for_status()

            retry_after = response.headers.get("retry-after")
            try:
                delay = float(retry_after) if retry_after else 2.5 * (attempt + 1)
            except ValueError:
                delay = 2.5 * (attempt + 1)

            jitter = random.uniform(0.15, 0.6)
            await asyncio.sleep(delay + jitter)

    if last_response is None:
        raise RuntimeError("Semantic Scholar request did not return a response.")
    last_response.raise_for_status()
    return last_response


async def search_papers(query: str, limit: int = 6, document_keywords: list[str] | None = None) -> list[dict]:
    cached = _get_cached(query, limit)
    if cached is not None:
        return rerank_papers(cached, query, document_keywords=document_keywords, limit=limit)

    response = await _request_search(query, limit)

    papers = []
    for paper in response.json().get("data", []):
        if paper.get("abstract"):
            paper_id = paper.get("paperId", "")
            title = paper.get("title", "")
            papers.append({
                "source_id": _paper_source_id(paper_id, title),
                "paper_id": paper_id,
                "provider": "Semantic Scholar",
                "source_type": "semantic_scholar",
                "title": title,
                "abstract": paper.get("abstract", ""),
                "year": paper.get("year"),
                "citation_count": paper.get("citationCount", 0),
                "authors": [author.get("name", "") for author in paper.get("authors", []) if author.get("name")],
                "url": _paper_url(paper_id, title),
            })

    _set_cached(query, limit, papers)
    return rerank_papers(papers, query, document_keywords=document_keywords, limit=limit)


async def search_openalex_papers(query: str, limit: int = 5, document_keywords: list[str] | None = None) -> list[dict]:
    params = {
        "search": query,
        "per-page": limit,
        "filter": "has_abstract:true",
        "select": "id,display_name,publication_year,cited_by_count,authorships,abstract_inverted_index,doi,primary_location",
    }
    async with httpx.AsyncClient(timeout=25.0, headers={"User-Agent": "DeepQuery hackathon research demo"}) as http:
        response = await http.get("https://api.openalex.org/works", params=params)
        response.raise_for_status()

    papers = []
    for work in response.json().get("results", []):
        title = work.get("display_name") or ""
        abstract = _abstract_from_openalex(work.get("abstract_inverted_index"))
        if not title or not abstract:
            continue

        authors = []
        for authorship in work.get("authorships", [])[:6]:
            author = (authorship.get("author") or {}).get("display_name")
            if author:
                authors.append(author)

        openalex_id = work.get("id", "")
        location = work.get("primary_location") or {}
        url = location.get("landing_page_url") or work.get("doi") or openalex_id
        papers.append({
            "source_id": f"openalex:{quote_plus(openalex_id or title.lower())}",
            "paper_id": openalex_id,
            "provider": "OpenAlex",
            "source_type": "openalex",
            "title": title,
            "abstract": abstract,
            "year": work.get("publication_year"),
            "citation_count": work.get("cited_by_count", 0),
            "authors": authors,
            "url": url,
        })

    return rerank_papers(papers, query, document_keywords=document_keywords, limit=limit)


async def search_arxiv_papers(query: str, limit: int = 5, document_keywords: list[str] | None = None) -> list[dict]:
    params = {
        "search_query": f"all:{query}",
        "start": 0,
        "max_results": limit,
        "sortBy": "relevance",
        "sortOrder": "descending",
    }
    async with httpx.AsyncClient(timeout=25.0, headers={"User-Agent": "DeepQuery hackathon research demo"}) as http:
        response = await http.get("https://export.arxiv.org/api/query", params=params)
        response.raise_for_status()

    root = ET.fromstring(response.text)
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    papers = []
    for entry in root.findall("atom:entry", ns):
        title = " ".join((entry.findtext("atom:title", default="", namespaces=ns) or "").split())
        abstract = " ".join((entry.findtext("atom:summary", default="", namespaces=ns) or "").split())
        paper_id = entry.findtext("atom:id", default="", namespaces=ns) or ""
        published = entry.findtext("atom:published", default="", namespaces=ns) or ""
        try:
            year = int(published[:4])
        except ValueError:
            year = None
        authors = [
            author.findtext("atom:name", default="", namespaces=ns)
            for author in entry.findall("atom:author", ns)
        ]
        authors = [author for author in authors if author][:6]
        if not title or not abstract:
            continue
        papers.append({
            "source_id": f"arxiv:{quote_plus(paper_id or title.lower())}",
            "paper_id": paper_id,
            "provider": "arXiv",
            "source_type": "arxiv",
            "title": title,
            "abstract": abstract,
            "year": year,
            "citation_count": 0,
            "authors": authors,
            "url": paper_id,
        })

    return rerank_papers(papers, query, document_keywords=document_keywords, limit=limit)


def _strip_crossref_abstract(raw: str) -> str:
    text = re.sub(r"<[^>]+>", " ", raw or "")
    return re.sub(r"\s+", " ", text).strip()


async def search_crossref_works(query: str, limit: int = 5, document_keywords: list[str] | None = None) -> list[dict]:
    params = {
        "query.bibliographic": query,
        "rows": limit,
        "filter": "type:journal-article",
        "select": "DOI,title,abstract,published-print,published-online,author,is-referenced-by-count,URL",
    }
    async with httpx.AsyncClient(timeout=25.0, headers={"User-Agent": "DeepQuery hackathon research demo"}) as http:
        response = await http.get("https://api.crossref.org/works", params=params)
        response.raise_for_status()

    papers = []
    for item in response.json().get("message", {}).get("items", []):
        title = " ".join((item.get("title") or [""])[0].split())
        abstract = _strip_crossref_abstract(item.get("abstract", ""))
        if not title or not abstract:
            continue

        date_parts = (
            (item.get("published-print") or {}).get("date-parts")
            or (item.get("published-online") or {}).get("date-parts")
            or []
        )
        year = None
        try:
            year = int(date_parts[0][0])
        except (IndexError, TypeError, ValueError):
            pass

        authors = []
        for author in item.get("author", [])[:6]:
            name = " ".join(part for part in [author.get("given"), author.get("family")] if part)
            if name:
                authors.append(name)
        doi = item.get("DOI", "")
        papers.append({
            "source_id": f"crossref:{quote_plus(doi or title.lower())}",
            "paper_id": doi,
            "provider": "Crossref",
            "source_type": "crossref",
            "title": title,
            "abstract": abstract,
            "year": year,
            "citation_count": item.get("is-referenced-by-count", 0),
            "authors": authors,
            "url": item.get("URL") or (f"https://doi.org/{doi}" if doi else ""),
        })

    return rerank_papers(papers, query, document_keywords=document_keywords, limit=limit)
