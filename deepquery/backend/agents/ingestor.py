from pydantic import BaseModel, Field

from agents.state import AgentState
from events import AgentEvent
from llm import client
from runtime import emit
from tools.documents import document_source_index, documents_summary_payload, normalize_uploads
from tools.prompting import clip_text


class DocumentBrief(BaseModel):
    summary: str = Field(description="A concise summary of the uploaded materials relevant to the user's goal")
    search_hints: list[str] = Field(
        default_factory=list,
        description="Important terms, methods, or topic variants worth using in paper search",
    )


def _fallback_brief(query: str, documents: list[dict]) -> str:
    if not documents:
        return ""

    lines = [f"User goal: {query}", "Uploaded materials:"]
    for document in documents:
        if document.get("error"):
            lines.append(f"- {document['name']}: {document['error']}")
            continue
        keywords = ", ".join(document.get("keywords") or []) or "no keywords"
        lines.append(f"- {document['name']}: keywords={keywords}; excerpt={document['excerpt']}")
    return "\n".join(lines)


async def ingestor_node(state: AgentState) -> dict:
    sid = state["session_id"]
    uploads = state.get("uploads", [])

    await emit(sid, AgentEvent(
        type="node_start", agent="ingestor",
        payload={"message": f"Ingesting {len(uploads)} uploaded file(s)..."}
    ))

    documents = normalize_uploads(uploads)
    payload_documents = [
        {
            "source_id": document["source_id"],
            "name": document["name"],
            "kind": document["kind"],
            "excerpt": document["excerpt"],
        }
        for document in documents
    ]

    brief = ""
    if documents:
        try:
            context: DocumentBrief = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You prepare search context from user-uploaded research materials. "
                            "Focus only on ideas that help answer the user's research request. "
                            "Return a concise summary and a short list of search hints."
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            f"User query: {clip_text(state['query'], 1200)}\n\n"
                            f"Uploaded materials:\n{clip_text(documents_summary_payload(documents), 8000)}"
                        ),
                    },
                ],
                response_model=DocumentBrief,
            )
            brief = "\n".join([
                f"Summary: {context.summary}",
                "Search hints: " + (", ".join(context.search_hints) or "none"),
            ])
        except Exception:
            brief = _fallback_brief(state["query"], documents)

    await emit(sid, AgentEvent(
        type="documents_ready", agent="ingestor",
        payload={
            "count": len(documents),
            "documents": payload_documents,
            "message": f"Prepared {len(documents)} uploaded document(s)",
        }
    ))
    await emit(sid, AgentEvent(
        type="node_end", agent="ingestor",
        payload={"document_count": len(documents)}
    ))

    return {
        "documents": documents,
        "document_brief": brief,
        "source_index": document_source_index(documents),
    }
