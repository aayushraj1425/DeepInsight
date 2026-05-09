import asyncio
from events import AgentEvent

_queues: dict[str, asyncio.Queue] = {}


def create_session(session_id: str) -> asyncio.Queue:
    q: asyncio.Queue = asyncio.Queue()
    _queues[session_id] = q
    return q


def get_queue(session_id: str) -> asyncio.Queue | None:
    return _queues.get(session_id)


def remove_session(session_id: str) -> None:
    _queues.pop(session_id, None)


async def emit(session_id: str, event: AgentEvent) -> None:
    q = _queues.get(session_id)
    if q:
        await q.put(event)
