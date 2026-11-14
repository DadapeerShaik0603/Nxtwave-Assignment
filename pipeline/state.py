"""
LangGraph AgentState — the single shared state object passed between all nodes.
"""

from typing import TypedDict, Optional, List
from models.lesson import Lesson
from models.evaluation import EvaluationResult


class AgentState(TypedDict):
    # Input
    topic: str
    demo_fail_mode: bool          # If True, force a bad first generation

    # Pipeline state
    lesson: Optional[Lesson]      # Current lesson version
    evaluation: Optional[EvaluationResult]  # Latest evaluation
    retry_count: int              # How many regenerations so far

    # History for the rejection log
    version_history: List[dict]   # [{version, lesson_md, evaluation}, ...]

    # Memory-evolved instructions injected before first generation
    memory_instructions: str

