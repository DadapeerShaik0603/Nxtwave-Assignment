"""
LangGraph pipeline nodes: regenerate_lesson
"""

import json
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

from pipeline.state import AgentState
from models.lesson import Lesson, Section
from prompts.regenerate_prompt import REGENERATE_SYSTEM_PROMPT, REGENERATE_USER_PROMPT
from config.settings import (
    PRIMARY_MODEL, TEMPERATURE, GROQ_API_KEY,
    MIN_WORD_COUNT, MAX_WORD_COUNT,
)


def _get_llm() -> ChatGroq:
    return ChatGroq(
        model=PRIMARY_MODEL,
        temperature=TEMPERATURE,
        api_key=GROQ_API_KEY,
    )


def _parse_lesson_json(raw: str, version: int) -> Lesson:
    text = raw.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    data = json.loads(text)
    sections = [
        Section(heading=s["heading"], content=s["content"])
        for s in data.get("sections", [])
    ]
    return Lesson(
        title=data.get("title", "Untitled Lesson"),
        introduction=data.get("introduction", ""),
        sections=sections,
        summary=data.get("summary", ""),
        version=version,
    )


def regenerate_lesson(state: AgentState) -> AgentState:
    """
    Node: Regenerate the lesson incorporating evaluation failure feedback.
    Increments retry_count and lesson version.
    """
    lesson = state["lesson"]
    evaluation = state["evaluation"]
    retry_count = state.get("retry_count", 0)
    next_version = lesson.version + 1

    failure_summary = evaluation.failure_summary()
    lesson_md = lesson.to_markdown()

    llm = _get_llm()

    system_msg = SystemMessage(
        content=REGENERATE_SYSTEM_PROMPT.format(
            min_words=MIN_WORD_COUNT,
            max_words=MAX_WORD_COUNT,
        )
    )
    user_msg = HumanMessage(
        content=REGENERATE_USER_PROMPT.format(
            failure_summary=failure_summary,
            version=lesson.version,
            lesson_markdown=lesson_md,
            next_version=next_version,
        )
    )

    response = llm.invoke([system_msg, user_msg])
    improved_lesson = _parse_lesson_json(response.content, version=next_version)

    return {
        **state,
        "lesson": improved_lesson,
        "retry_count": retry_count + 1,
        "evaluation": None,  # Reset evaluation for the new version
    }

