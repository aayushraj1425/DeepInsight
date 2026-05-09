from typing import TypedDict, Optional


class AgentState(TypedDict):
    session_id: str
    query: str
    uploads: list[dict]
    documents: list[dict]
    document_brief: str
    research_plan: dict
    subqueries: list[str]
    papers: list[dict]
    paper_sources: list[dict]
    datasets: list[dict]
    dataset_findings: list[dict]
    dataset_analysis: dict
    validation_report: dict
    source_index: dict[str, dict]
    findings: list[dict]
    analysis: dict
    reasoning: dict
    economic_model: dict
    fact_check_report: dict
    critic_feedback: str
    critic_retries: int
    approved: bool
    chart_specs: list[dict]
    report: str
    error: Optional[str]
