"""
LangGraph StateGraph definition — wires all nodes and edges together.
"""

from langgraph.graph import StateGraph, END

from pipeline.state import AgentState
from pipeline.nodes.generate import generate_lesson
from pipeline.nodes.evaluate import evaluate_lesson
from pipeline.nodes.regenerate import regenerate_lesson
from pipeline.nodes.output import output_lesson
from pipeline.nodes.memory_persist import persist_memory
from pipeline.router import route_after_evaluate


def build_graph() -> StateGraph:
    """
    Build and compile the LangGraph agentic pipeline.

    Flow:
        generate_lesson
            → evaluate_lesson
                → [route] passed?  → output_lesson → persist_memory → END
                         failed?
                           retries < MAX? → regenerate_lesson → evaluate_lesson (loop)
                           retries >= MAX? → output_lesson → persist_memory → END
    """
    graph = StateGraph(AgentState)

    # ── Add nodes ─────────────────────────────────────────────────────────────
    graph.add_node("generate_lesson",   generate_lesson)
    graph.add_node("evaluate_lesson",   evaluate_lesson)
    graph.add_node("regenerate_lesson", regenerate_lesson)
    graph.add_node("output_lesson",     output_lesson)
    graph.add_node("persist_memory",    persist_memory)

    # ── Entry point ───────────────────────────────────────────────────────────
    graph.set_entry_point("generate_lesson")

    # ── Edges ─────────────────────────────────────────────────────────────────
    graph.add_edge("generate_lesson", "evaluate_lesson")

    graph.add_conditional_edges(
        "evaluate_lesson",
        route_after_evaluate,
        {
            "output_lesson":     "output_lesson",
            "regenerate_lesson": "regenerate_lesson",
        },
    )

    graph.add_edge("regenerate_lesson", "evaluate_lesson")   # Loop back
    graph.add_edge("output_lesson",     "persist_memory")
    graph.add_edge("persist_memory",    END)

    return graph.compile()

