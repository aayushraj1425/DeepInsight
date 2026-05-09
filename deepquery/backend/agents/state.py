from typing import TypedDict, Optional


class AgentState(TypedDict):
    session_id: str
    query: str
    subqueries: list[str]
    uploaded_docs: list[dict]   # [{filename, chunks: [{title, abstract, ...}]}]
    papers: list[dict]
    findings: list[dict]
    analysis: dict
    critic_feedback: str
    critic_retries: int
    approved: bool
    chart_specs: list[dict]
    report: str
    error: Optional[str]
