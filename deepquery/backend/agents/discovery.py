import asyncio
from agents.state import AgentState
from events import AgentEvent
from runtime import emit
from tools.papers import search_papers


async def discovery_node(state: AgentState) -> dict:
    sid = state["session_id"]
    await emit(sid, AgentEvent(
        type="node_start", agent="discovery",
        payload={"message": f"Searching Semantic Scholar for {len(state['subqueries'])} subqueries..."}
    ))

    seen: set[str] = set()
    all_papers: list[dict] = []

    for sq in state["subqueries"]:
        await emit(sid, AgentEvent(
            type="tool_call", agent="discovery",
            payload={"tool": "semantic_scholar_search", "query": sq}
        ))
        try:
            papers = await search_papers(sq, limit=6)
            new = 0
            for p in papers:
                key = p["paper_id"] or p["title"]
                if key not in seen:
                    seen.add(key)
                    all_papers.append(p)
                    new += 1
            await emit(sid, AgentEvent(
                type="tool_result", agent="discovery",
                payload={"query": sq, "found": len(papers), "new": new}
            ))
        except Exception as exc:
            await emit(sid, AgentEvent(
                type="error", agent="discovery",
                payload={"message": f"Search failed for '{sq}': {exc}"}
            ))
        await asyncio.sleep(0.4)  # Semantic Scholar free tier rate limit

    await emit(sid, AgentEvent(
        type="node_end", agent="discovery",
        payload={"total_papers": len(all_papers)}
    ))
    return {"papers": all_papers}
