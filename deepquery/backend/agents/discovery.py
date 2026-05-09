import asyncio

from agents.state import AgentState
from events import AgentEvent
from runtime import emit
from tools.papers import (
    SemanticScholarRateLimitError,
    rerank_papers,
    search_arxiv_papers,
    search_crossref_works,
    search_openalex_papers,
    search_papers,
)


ACADEMIC_PROVIDERS = [
    ("semantic_scholar_search", "Semantic Scholar", search_papers, 6),
    ("openalex_search", "OpenAlex", search_openalex_papers, 5),
    ("arxiv_search", "arXiv", search_arxiv_papers, 5),
    ("crossref_search", "Crossref", search_crossref_works, 4),
]


async def discovery_node(state: AgentState) -> dict:
    sid = state["session_id"]
    document_keywords = [
        keyword
        for document in state.get("documents", [])
        for keyword in document.get("keywords", [])
    ]
    await emit(sid, AgentEvent(
        type="node_start", agent="discovery",
        payload={"message": f"Searching academic indexes and primary-source leads for {len(state['subqueries'])} subqueries..."}
    ))

    seen: set[str] = set()
    all_papers: list[dict] = []
    rate_limited = False

    for sq in state["subqueries"][:6]:
        for tool_name, provider, search_fn, limit in ACADEMIC_PROVIDERS:
            if provider == "Semantic Scholar" and len([paper for paper in all_papers if paper.get("provider") == "Semantic Scholar"]) >= 10:
                continue
            await emit(sid, AgentEvent(
                type="tool_call", agent="discovery",
                payload={"tool": tool_name, "provider": provider, "query": sq}
            ))
            try:
                papers = await search_fn(sq, limit=limit, document_keywords=document_keywords)
                new = 0
                for p in papers:
                    key = (p.get("paper_id") or p.get("title") or "").lower()
                    if key and key not in seen:
                        seen.add(key)
                        all_papers.append(p)
                        new += 1
                await emit(sid, AgentEvent(
                    type="tool_result", agent="discovery",
                    payload={"query": sq, "provider": provider, "found": len(papers), "new": new}
                ))
            except SemanticScholarRateLimitError as exc:
                rate_limited = True
                await emit(sid, AgentEvent(
                    type="tool_result", agent="discovery",
                    payload={"query": sq, "provider": provider, "found": 0, "new": 0, "message": str(exc)}
                ))
            except Exception as exc:
                await emit(sid, AgentEvent(
                    type="tool_result", agent="discovery",
                    payload={"query": sq, "provider": provider, "found": 0, "new": 0, "message": str(exc)}
                ))
            await asyncio.sleep(0.15)

    ranked_papers = rerank_papers(
        all_papers,
        state["query"],
        document_keywords=document_keywords,
        limit=12,
    )
    source_index = dict(state.get("source_index", {}))
    for paper in ranked_papers:
        source_index[paper["source_id"]] = {
            "source_id": paper["source_id"],
            "source_type": paper.get("source_type", "semantic_scholar"),
            "provider": paper.get("provider", "Semantic Scholar"),
            "title": paper["title"],
            "year": paper.get("year"),
            "citation_count": paper.get("citation_count", 0),
            "authors": paper.get("authors", []),
            "url": paper.get("url", ""),
        }

    await emit(sid, AgentEvent(
        type="sources_ready", agent="discovery",
        payload={
            "count": len(ranked_papers),
            "papers": [
                {
                    "source_id": paper["source_id"],
                    "paper_id": paper.get("paper_id", ""),
                    "provider": paper.get("provider", "Semantic Scholar"),
                    "source_type": paper.get("source_type", "semantic_scholar"),
                    "title": paper["title"],
                    "year": paper.get("year"),
                    "citation_count": paper.get("citation_count", 0),
                    "authors": paper.get("authors", []),
                    "url": paper.get("url", ""),
                }
                for paper in ranked_papers
            ],
            "message": (
                f"Selected {len(ranked_papers)} scholarly sources"
                if not rate_limited
                else f"Selected {len(ranked_papers)} scholarly sources after Semantic Scholar rate-limited retries"
            ),
        }
    ))

    if rate_limited and not ranked_papers:
        await emit(sid, AgentEvent(
            type="error", agent="discovery",
            payload={
                "message": (
                    "Semantic Scholar is rate-limiting this run. Wait a bit before retrying, "
                    "or add SEMANTIC_SCHOLAR_API_KEY to backend/.env for more reliable live searches."
                )
            }
        ))

    await emit(sid, AgentEvent(
        type="node_end", agent="discovery",
        payload={"total_papers": len(ranked_papers)}
    ))
    return {
        "papers": ranked_papers,
        "paper_sources": ranked_papers,
        "source_index": source_index,
    }
