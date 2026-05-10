import asyncio
from agents.state import AgentState
from events import AgentEvent
from runtime import emit
from tools.papers import search_papers
from tools.pubmed import search_pubmed
from tools.arxiv_search import search_arxiv
from tools.openalex import search_openalex
from tools.web_search import web_search, enrich_web_results

# ── Query-type classifiers ────────────────────────────────────────────────────

_MEDICAL_TERMS = {
    "mortality", "morbidity", "disease", "syndrome", "infection", "virus", "bacteria",
    "cancer", "tumor", "vaccine", "clinical", "patient", "treatment", "therapy",
    "drug", "symptom", "diagnosis", "epidemiology", "prevalence", "incidence",
    "death", "fatal", "survival", "risk factor", "children", "pediatric", "rabies",
    "covid", "flu", "hiv", "diabetes", "obesity", "depression", "anxiety",
    "stroke", "heart", "blood", "hospital", "surgery", "medicine", "health",
    "dose", "side effect", "placebo", "trial", "cohort", "randomized",
}

_CS_AI_TERMS = {
    "machine learning", "deep learning", "neural network", "transformer",
    "large language model", "llm", "gpt", "bert", "reinforcement learning",
    "computer vision", "nlp", "natural language", "algorithm", "software",
    "artificial intelligence", "ai model", "diffusion model", "attention mechanism",
    "graph neural", "federated learning", "quantum computing", "semiconductor",
    "robotics", "autonomous", "recommendation system", "knowledge graph",
}


def _is_medical(text: str) -> bool:
    t = text.lower()
    return any(term in t for term in _MEDICAL_TERMS)


def _is_cs_ai(text: str) -> bool:
    t = text.lower()
    return any(term in t for term in _CS_AI_TERMS)


def _detect_type(query: str, subqueries: list[str]) -> str:
    all_text = " ".join([query] + subqueries)
    if _is_medical(all_text):
        return "medical"
    if _is_cs_ai(all_text):
        return "cs_ai"
    return "general"


# ── Source search helpers ─────────────────────────────────────────────────────

async def _try_scholar(sq: str, limit: int) -> list[dict]:
    try:
        return await search_papers(sq, limit=limit)
    except Exception:
        return []


async def _fetch_for_type(sq: str, query_type: str) -> list[dict]:
    """
    Run the right sources in parallel based on query type.
    Returns combined deduplicated results.
    Fallback hierarchy:
      medical  → PubMed + Semantic Scholar → OpenAlex → web
      cs/ai    → arXiv + Semantic Scholar  → OpenAlex → web
      general  → Semantic Scholar           → OpenAlex → web
    """
    if query_type == "medical":
        results = await asyncio.gather(
            search_pubmed(sq, limit=5),
            _try_scholar(sq, limit=4),
            return_exceptions=True,
        )
    elif query_type == "cs_ai":
        results = await asyncio.gather(
            search_arxiv(sq, limit=5),
            _try_scholar(sq, limit=4),
            return_exceptions=True,
        )
    else:
        results = await asyncio.gather(
            _try_scholar(sq, limit=6),
            return_exceptions=True,
        )

    papers: list[dict] = []
    for r in results:
        if not isinstance(r, Exception):
            papers.extend(r)
    return papers


async def _search_one(sq: str, seen: set, sid: str, query_type: str) -> list[dict]:
    """Search one subquery. Falls back to OpenAlex then web if primary sources return nothing."""
    papers = await _fetch_for_type(sq, query_type)

    # Deduplicate against already-seen keys
    new_papers = []
    for p in papers:
        key = p.get("paper_id") or p.get("title", "")
        if key and key not in seen:
            seen.add(key)
            new_papers.append(p)

    if new_papers:
        source_label = {"medical": "PubMed+Scholar", "cs_ai": "arXiv+Scholar"}.get(query_type, "Semantic Scholar")
        await emit(sid, AgentEvent(
            type="tool_result", agent="discovery",
            payload={"source": source_label, "query": sq, "new": len(new_papers)}
        ))
        await asyncio.sleep(1.5)
        return new_papers

    # Fallback 1: OpenAlex (broad academic index, no rate limits)
    oa_results = await search_openalex(sq, limit=5)
    for p in oa_results:
        key = p.get("paper_id") or p.get("title", "")
        if key and key not in seen:
            seen.add(key)
            new_papers.append(p)

    if new_papers:
        await emit(sid, AgentEvent(
            type="tool_result", agent="discovery",
            payload={"source": "openalex", "query": sq, "new": len(new_papers)}
        ))
        await asyncio.sleep(1.0)
        return new_papers

    # Fallback 2: DuckDuckGo web search + full page fetch
    raw_web = web_search(sq, max_results=6)
    web_papers = await enrich_web_results(raw_web)
    for p in web_papers:
        key = p.get("paper_id") or p.get("title", "")
        if key and key not in seen:
            seen.add(key)
            new_papers.append(p)

    if new_papers:
        await emit(sid, AgentEvent(
            type="tool_result", agent="discovery",
            payload={"source": "web", "query": sq, "new": len(new_papers)}
        ))

    await asyncio.sleep(1.0)
    return new_papers


# ── Discovery node ────────────────────────────────────────────────────────────

async def discovery_node(state: AgentState) -> dict:
    sid = state["session_id"]
    is_retry = state.get("discovery_retries", 0) > 0
    query_type = _detect_type(state.get("query", ""), state.get("subqueries", []))

    source_label = {
        "medical": "PubMed + Semantic Scholar",
        "cs_ai":   "arXiv + Semantic Scholar",
    }.get(query_type, "Semantic Scholar → OpenAlex → Web")

    if is_retry:
        subqueries = state.get("fallback_queries") or state["subqueries"]
        existing = [p for p in (state.get("papers") or []) if (p.get("paper_id") or "").startswith("file:")]
        await emit(sid, AgentEvent(
            type="node_start", agent="discovery",
            payload={"message": "Re-searching with broader queries..."}
        ))
    else:
        subqueries = state["subqueries"]
        existing = state.get("papers") or []
        await emit(sid, AgentEvent(
            type="node_start", agent="discovery",
            payload={"message": f"Searching via {source_label}..."}
        ))

    seen: set[str] = set(p.get("paper_id") or p.get("title", "") for p in existing)
    all_papers: list[dict] = list(existing)

    for sq in subqueries:
        await emit(sid, AgentEvent(
            type="tool_call", agent="discovery",
            payload={"tool": "search", "query": sq}
        ))
        new_papers = await _search_one(sq, seen, sid, query_type)
        all_papers.extend(new_papers)

    # Auto-widen: if still empty, run fallback queries immediately
    if not all_papers and not is_retry:
        fallback_queries = state.get("fallback_queries") or []
        if fallback_queries:
            await emit(sid, AgentEvent(
                type="node_start", agent="discovery",
                payload={"message": "Primary search empty — widening to fallback queries..."}
            ))
            for sq in fallback_queries:
                new_papers = await _search_one(sq, seen, sid, query_type)
                all_papers.extend(new_papers)

    # Build sources list for the frontend panel
    source_list = []
    for p in all_papers:
        paper_id = p.get("paper_id", "")
        url = (
            p.get("url")
            or (f"https://www.semanticscholar.org/paper/{paper_id}"
                if paper_id and not paper_id.startswith(("file:", "pmid:", "arxiv:", "oa:"))
                else "")
        )
        if not url:
            continue
        provider = (
            "PubMed" if p.get("source") == "pubmed" else
            "arXiv"  if p.get("source") == "arxiv"  else
            "OpenAlex" if p.get("source") == "openalex" else
            "Web"    if p.get("source") == "web"    else
            "Semantic Scholar"
        )
        source_list.append({
            "title":         p.get("title", "Untitled"),
            "provider":      provider,
            "url":           url,
            "year":          p.get("year"),
            "citationCount": p.get("citation_count"),
        })

    await emit(sid, AgentEvent(
        type="sources_ready", agent="discovery",
        payload={"sources": source_list}
    ))
    await emit(sid, AgentEvent(
        type="node_end", agent="discovery",
        payload={"total_papers": len(all_papers), "query_type": query_type}
    ))
    return {
        "papers": all_papers,
        "discovery_retries": state.get("discovery_retries", 0) + (1 if is_retry else 0),
    }
