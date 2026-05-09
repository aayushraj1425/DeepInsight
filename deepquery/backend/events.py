from pydantic import BaseModel, model_validator
from typing import Literal
from datetime import datetime, timezone

EventType = Literal[
    "node_start", "node_end", "tool_call", "tool_result",
    "critic_decision", "chart_ready", "report_ready",
    "error", "done"
]


class AgentEvent(BaseModel):
    type: EventType
    agent: str
    payload: dict
    timestamp: str = ""

    @model_validator(mode="after")
    def set_timestamp(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()
        return self
