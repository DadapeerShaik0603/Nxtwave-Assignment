"""
LangGraph pipeline nodes: persist_memory
"""

from pipeline.state import AgentState
from memory.manager import MemoryManager


def persist_memory(state: AgentState) -> AgentState:
    """
    Node: Save this run's history to disk for future self-evolution.
    Always runs at the end of the pipeline (after output_lesson).
    """
    manager = MemoryManager()
    evaluation = state.get("evaluation")
    final_passed = evaluation.passed if evaluation else False

    manager.save_run(
        topic=state["topic"],
        final_passed=final_passed,
        retry_count=state.get("retry_count", 0),
        version_history=state.get("version_history", []),
    )

    return state

