import asyncio
from agents.state import AgentState
from events import AgentEvent
from runtime import emit
from tools.papers import search_papers
from tools.web_search import web_search, enrich_web_results


async def discovery_node(state: AgentState) -> dict:
    sid = state["session_id"]
    await emit(sid, AgentEvent(
        type="node_start", agent="discovery",
        payload={"message": f"Searching for {len(state['subqueries'])} subqueries..."}
    ))

    # Preserve file-ingestor papers already in state
    existing = state.get("papers") or []
    seen: set[str] = set(p.get("paper_id") or p["title"] for p in existing)
    all_papers: list[dict] = list(existing)

    for sq in state["subqueries"]:
        await emit(sid, AgentEvent(
            type="tool_call", agent="discovery",
            payload={"tool": "semantic_scholar_search", "query": sq}
        ))

        scholar_papers = []
        try:
            scholar_papers = await search_papers(sq, limit=6)
        except Exception:
            pass  # Rate-limited or network error — fall through to web search

        if scholar_papers:
            new = 0
            for p in scholar_papers:
                key = p["paper_id"] or p["title"]
                if key not in seen:
                    seen.add(key)
                    all_papers.append(p)
                    new += 1
            await emit(sid, AgentEvent(
                type="tool_result", agent="discovery",
                payload={"source": "semantic_scholar", "query": sq, "found": len(scholar_papers), "new": new}
            ))
        else:
            # Fallback: web search + fetch full page content
            await emit(sid, AgentEvent(
                type="tool_call", agent="discovery",
                payload={"tool": "web_search", "query": sq}
            ))
            raw_web = web_search(sq, max_results=6)
            web_papers = await enrich_web_results(raw_web)

            new = 0
            for p in web_papers:
                key = p["paper_id"] or p["title"]
                if key not in seen:
                    seen.add(key)
                    all_papers.append(p)
                    new += 1
            await emit(sid, AgentEvent(
                type="tool_result", agent="discovery",
                payload={"source": "web_search", "query": sq, "found": len(web_papers), "new": new}
            ))

        await asyncio.sleep(2.0)

    # Build source list for the frontend Sources panel
    source_list = []
    for p in all_papers:
        paper_id = p.get("paper_id", "")
        url = (
            p.get("url")                                          # web result
            or (f"https://www.semanticscholar.org/paper/{paper_id}" if paper_id and not paper_id.startswith("file:") else "")
        )
        if not url:
            continue
        source_list.append({
            "title":         p.get("title", "Untitled"),
            "provider":      "Web" if p.get("source") == "web" else "Semantic Scholar",
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
        payload={"total_papers": len(all_papers)}
    ))
    return {"papers": all_papers}
