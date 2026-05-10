from langgraph.graph import StateGraph, END

from agents.state import AgentState
from agents.planner import planner_node
from agents.file_ingestor import file_ingestor_node
from agents.discovery import discovery_node
from agents.extractor import extractor_node
from agents.analyst import analyst_node
from agents.critic import critic_node, route_after_critic
from agents.visualizer import visualizer_node
from agents.reporter import reporter_node


def build_graph():
    builder = StateGraph(AgentState)

    builder.add_node("planner",       planner_node)
    builder.add_node("file_ingestor", file_ingestor_node)
    builder.add_node("discovery",     discovery_node)
    builder.add_node("extractor",     extractor_node)
    builder.add_node("analyst",       analyst_node)
    builder.add_node("critic",        critic_node)
    builder.add_node("visualizer",    visualizer_node)
    builder.add_node("reporter",      reporter_node)

    builder.set_entry_point("planner")
    builder.add_edge("planner",       "file_ingestor")
    builder.add_edge("file_ingestor", "discovery")
    builder.add_edge("discovery",     "extractor")
    builder.add_edge("extractor",     "analyst")
    builder.add_edge("analyst",       "critic")

    # Critic routes to:
    #   "visualizer" — approved or max retries hit
    #   "analyst"    — valid findings but weak analysis (retry with different tools)
    #   "discovery"  — hallucinated or off-topic findings (need better source papers)
    builder.add_conditional_edges(
        "critic",
        route_after_critic,
        {
            "visualizer": "visualizer",
            "analyst":    "analyst",
            "discovery":  "discovery",   # re-runs discovery → extractor → analyst → critic
        },
    )

    builder.add_edge("visualizer", "reporter")
    builder.add_edge("reporter",   END)

    return builder.compile()
