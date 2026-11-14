"""
Conditional edge router for the LangGraph pipeline.
"""

from pipeline.state import AgentState
from config.settings import MAX_RETRIES


def route_after_evaluate(state: AgentState) -> str:
    """
    After evaluation, decide whether to:
    - output_lesson (if passed OR max retries reached)
    - regenerate_lesson (if failed and retries remaining)
    """
    evaluation = state.get("evaluation")
    retry_count = state.get("retry_count", 0)

    if evaluation is None:
        # Safety fallback — should not happen
        return "output_lesson"

    if evaluation.passed:
        return "output_lesson"

    if retry_count >= MAX_RETRIES:
        # Force output with whatever we have; rejection log records the failures
        return "output_lesson"

    return "regenerate_lesson"

