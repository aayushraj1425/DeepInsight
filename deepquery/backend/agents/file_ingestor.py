from agents.state import AgentState
from events import AgentEvent
from runtime import emit
from tools.rag import retrieve_top_k


async def file_ingestor_node(state: AgentState) -> dict:
    sid = state["session_id"]
    uploaded_docs = state.get("uploaded_docs") or []

    if not uploaded_docs:
        return {}

    await emit(sid, AgentEvent(
        type="node_start", agent="file_ingestor",
        payload={"message": f"Processing {len(uploaded_docs)} uploaded file(s) with RAG..."}
    ))

    # All chunks across all uploaded files
    all_chunks: list[dict] = []
    for doc in uploaded_docs:
        all_chunks.extend(doc.get("chunks", []))

    if not all_chunks:
        await emit(sid, AgentEvent(
            type="node_end", agent="file_ingestor",
            payload={"chunks_indexed": 0, "retrieved": 0}
        ))
        return {}

    # Embed all chunks and retrieve the most relevant ones for the query
    query = state["query"]
    top_chunks = await retrieve_top_k(query, all_chunks, k=min(10, len(all_chunks)))

    await emit(sid, AgentEvent(
        type="tool_result", agent="file_ingestor",
        payload={
            "message": f"Retrieved {len(top_chunks)} relevant chunks from {len(all_chunks)} total",
            "chunks_indexed": len(all_chunks),
            "retrieved": len(top_chunks),
        }
    ))
    await emit(sid, AgentEvent(
        type="node_end", agent="file_ingestor",
        payload={"chunks_indexed": len(all_chunks), "retrieved": len(top_chunks)}
    ))

    # Prepend file chunks to papers so extractor sees them first
    existing_papers = state.get("papers") or []
    return {"papers": list(top_chunks) + list(existing_papers)}
