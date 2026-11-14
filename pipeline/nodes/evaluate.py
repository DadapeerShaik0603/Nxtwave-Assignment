"""
LangGraph pipeline nodes: evaluate_lesson
"""

import json
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

from pipeline.state import AgentState
from models.evaluation import EvaluationResult, CheckpointResult
from prompts.evaluate_prompt import EVALUATE_SYSTEM_PROMPT, EVALUATE_USER_PROMPT
from config.settings import (
    PRIMARY_MODEL, EVAL_TEMPERATURE, GROQ_API_KEY,
    MIN_WORD_COUNT, MAX_WORD_COUNT,
)


def _get_eval_llm() -> ChatGroq:
    return ChatGroq(
        model=PRIMARY_MODEL,
        temperature=EVAL_TEMPERATURE,
        api_key=GROQ_API_KEY,
    )


def _parse_evaluation_json(raw: str) -> EvaluationResult:
    """Parse raw LLM evaluation output into EvaluationResult."""
    text = raw.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    data = json.loads(text)
    checkpoint_results = [
        CheckpointResult(
            checkpoint_id=cp["checkpoint_id"],
            name=cp["name"],
            passed=cp["passed"],
            reason=cp["reason"],
            suggestion=cp.get("suggestion", ""),
        )
        for cp in data.get("checkpoint_results", [])
    ]
    return EvaluationResult(
        passed=data.get("passed", False),
        checkpoint_results=checkpoint_results,
        overall_feedback=data.get("overall_feedback", ""),
    )


def evaluate_lesson(state: AgentState) -> AgentState:
    """
    Node: Evaluate the current lesson against the rubric.
    Stores evaluation result and archives this version in version_history.
    """
    lesson = state["lesson"]
    lesson_md = lesson.to_markdown()
    word_count = lesson.word_count()

    llm = _get_eval_llm()

    system_msg = SystemMessage(
        content=EVALUATE_SYSTEM_PROMPT.format(
            min_words=MIN_WORD_COUNT,
            max_words=MAX_WORD_COUNT,
        )
    )
    user_msg = HumanMessage(
        content=EVALUATE_USER_PROMPT.format(
            lesson_markdown=lesson_md,
            word_count=word_count,
        )
    )

    response = llm.invoke([system_msg, user_msg])
    evaluation = _parse_evaluation_json(response.content)

    # Archive this version
    version_history = list(state.get("version_history", []))
    version_history.append({
        "version": lesson.version,
        "lesson_md": lesson_md,
        "evaluation": evaluation.model_dump(),
    })

    return {
        **state,
        "evaluation": evaluation,
        "version_history": version_history,
    }

