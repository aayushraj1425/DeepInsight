import asyncio
import uuid
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from events import AgentEvent
from runtime import create_session, get_queue, remove_session, emit
from agents.graph import build_graph
from demo_cache import run_cached_demo

app = FastAPI(title="DeepQuery")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

graph = build_graph()


class InvestigationRequest(BaseModel):
    query: str


async def run_pipeline(session_id: str, query: str) -> None:
    try:
        initial_state = {
            "session_id": session_id,
            "query": query,
            "subqueries": [],
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
            await q.put(None)  # sentinel closes the SSE stream


@app.post("/api/investigations")
async def create_investigation(req: InvestigationRequest, background_tasks: BackgroundTasks):
    session_id = str(uuid.uuid4())
    create_session(session_id)
    background_tasks.add_task(run_pipeline, session_id, req.query)
    return {"id": session_id}


@app.get("/api/stream/{session_id}")
async def stream_events(session_id: str):
    q = get_queue(session_id)
    if q is None:
        async def not_found():
            yield 'data: {"type":"error","agent":"system","payload":{"message":"session not found"},"timestamp":""}\n\n'
        return StreamingResponse(not_found(), media_type="text/event-stream")

    async def event_generator():
        try:
            while True:
                event = await asyncio.wait_for(q.get(), timeout=120.0)
                if event is None:
                    break
                yield f"data: {event.model_dump_json()}\n\n"
        except asyncio.TimeoutError:
            yield 'data: {"type":"error","agent":"system","payload":{"message":"stream timeout"},"timestamp":""}\n\n'
        finally:
            remove_session(session_id)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
