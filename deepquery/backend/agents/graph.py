from langgraph.graph import StateGraph, END

from agents.state import AgentState
from agents.ingestor import ingestor_node
from agents.orchestrator import orchestrator_node
from agents.discovery import discovery_node
from agents.datafinder import datafinder_node
from agents.validator import validator_node
from agents.extractor import extractor_node
from agents.analyst import analyst_node
from agents.reasoner import reasoner_node
from agents.economist import economist_node
from agents.factchecker import factchecker_node
from agents.visualizer import visualizer_node
from agents.reporter import reporter_node


def build_graph():
    builder = StateGraph(AgentState)

    builder.add_node("ingestor",   ingestor_node)
    builder.add_node("orchestrator", orchestrator_node)
    builder.add_node("discovery",    discovery_node)
    builder.add_node("datafinder",   datafinder_node)
    builder.add_node("validator",    validator_node)
    builder.add_node("extractor",    extractor_node)
    builder.add_node("analyst",      analyst_node)
    builder.add_node("reasoner",     reasoner_node)
    builder.add_node("economist",    economist_node)
    builder.add_node("factchecker",  factchecker_node)
    builder.add_node("visualizer",   visualizer_node)
    builder.add_node("reporter",     reporter_node)

    builder.set_entry_point("ingestor")
    builder.add_edge("ingestor",     "orchestrator")
    builder.add_edge("orchestrator", "discovery")
    builder.add_edge("discovery",    "datafinder")
    builder.add_edge("datafinder",   "validator")
    builder.add_edge("validator",    "extractor")
    builder.add_edge("extractor",    "analyst")
    builder.add_edge("analyst",      "reasoner")
    builder.add_edge("reasoner",     "economist")
    builder.add_edge("economist",    "factchecker")
    builder.add_edge("factchecker",  "visualizer")
    builder.add_edge("visualizer",   "reporter")
    builder.add_edge("reporter",     END)

    return builder.compile()
