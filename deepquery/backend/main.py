import asyncio
import sys
import uuid
from pathlib import Path
from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

load_dotenv(BACKEND_DIR / ".env")

from fastapi import FastAPI, BackgroundTasks, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from events import AgentEvent
from runtime import create_session, get_queue, remove_session, emit
from agents.graph import build_graph
from demo_cache import run_cached_demo
from tools.document_parser import parse_pdf, parse_csv

app = FastAPI(title="DeepQuery")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[],
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1):517[0-9]$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

graph = build_graph()

# In-memory store: session_id → list of parsed doc dicts
_session_docs: dict[str, list[dict]] = {}


class InvestigationRequest(BaseModel):
    query: str
    session_id: str | None = None  # pre-created session from file upload


@app.get("/api/health")
async def health_check():
    return {"status": "ok"}


@app.post("/api/upload")
async def upload_files(files: list[UploadFile] = File(...)):
    """
    Parse uploaded PDF/CSV files and store chunks under a new session_id.
    Returns session_id + summary of what was parsed.
    """
    session_id = str(uuid.uuid4())
    docs = []

    for f in files:
        content = await f.read()
        name = f.filename or "unknown"

        if name.lower().endswith(".pdf"):
            chunks = parse_pdf(content, name)
        elif name.lower().endswith(".csv"):
            chunks = parse_csv(content, name)
        else:
            # Treat as plain text
            text = content.decode("utf-8", errors="replace")
            from tools.document_parser import _chunk_text
            raw_chunks = _chunk_text(text, size=600, overlap=80)
            chunks = [
                {
                    "title": f"{name} [chunk {i+1}]",
                    "abstract": c,
                    "paper_id": f"file:{name}:chunk{i}",
                    "year": None,
                    "source": "upload",
                }
                for i, c in enumerate(raw_chunks)
            ]

        docs.append({"filename": name, "chunks": chunks})

    _session_docs[session_id] = docs

    return {
        "session_id": session_id,
        "files": [
            {"filename": d["filename"], "chunks": len(d["chunks"])}
            for d in docs
        ],
    }


def sse_data(event: AgentEvent) -> str:
    return f"data: {event.model_dump_json()}\n\n"


async def run_pipeline(session_id: str, query: str, uploaded_docs: list[dict]) -> None:
    try:
        initial_state = {
            "session_id": session_id,
            "query": query,
            "subqueries": [],
            "uploaded_docs": uploaded_docs,
            "papers": [],
            "findings": [],
            "analysis": {},
            "critic_feedback": "",
            "critic_retries": 0,
            "approved": False,
            "chart_specs": [],
            "report": "",
            "error": None,
        }
        if not await run_cached_demo(session_id, query):
            await graph.ainvoke(initial_state)
        await emit(session_id, AgentEvent(
            type="done", agent="system",
            payload={"message": "Research complete"}
        ))
    except Exception as exc:
        await emit(session_id, AgentEvent(
            type="error", agent="system",
            payload={"message": str(exc)}
        ))
    finally:
        q = get_queue(session_id)
        if q:
            await q.put(None)
        _session_docs.pop(session_id, None)


@app.post("/api/investigations")
async def create_investigation(req: InvestigationRequest, background_tasks: BackgroundTasks):
    # If files were pre-uploaded, reuse that session_id and its docs
    if req.session_id and req.session_id in _session_docs:
        session_id = req.session_id
        uploaded_docs = _session_docs[session_id]
        create_session(session_id)
    else:
        session_id = str(uuid.uuid4())
        uploaded_docs = []
        create_session(session_id)

    background_tasks.add_task(run_pipeline, session_id, req.query, uploaded_docs)
    return {"id": session_id}


@app.get("/api/stream/{session_id}")
async def stream_events(session_id: str):
    q = get_queue(session_id)
    if q is None:
        async def not_found():
            yield sse_data(AgentEvent(
                type="error",
                agent="system",
                payload={"message": "session not found"},
            ))
        return StreamingResponse(not_found(), media_type="text/event-stream")

    async def event_generator():
        try:
            while True:
                event = await asyncio.wait_for(q.get(), timeout=120.0)
                if event is None:
                    break
                yield sse_data(event)
        except asyncio.TimeoutError:
            yield sse_data(AgentEvent(
                type="error",
                agent="system",
                payload={"message": "stream timeout"},
            ))
        finally:
            remove_session(session_id)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
