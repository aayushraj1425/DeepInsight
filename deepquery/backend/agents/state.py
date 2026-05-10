from typing import TypedDict, Optional


class AgentState(TypedDict):
    session_id: str
    query: str
    subqueries: list[str]
    fallback_queries: list[str]       # broader queries used when primary sources fail
    uploaded_docs: list[dict]
    papers: list[dict]
    findings: list[dict]
    analysis: dict
    critic_feedback: str
    critic_rejection_type: str        # "hallucinated" | "weak_analysis" | "off_topic" | ""
    critic_retries: int
    discovery_retries: int            # how many times discovery was re-run
    approved: bool
    synthesis: dict
    chart_specs: list[dict]
    report: str
    error: Optional[str]
