"""
LangGraph pipeline nodes: generate_lesson
"""

import json
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

from pipeline.state import AgentState
from models.lesson import Lesson, Section
from prompts.generate_prompt import (
    GENERATE_SYSTEM_PROMPT,
    GENERATE_USER_PROMPT,
    DEMO_FAIL_SYSTEM_PROMPT,
    DEMO_FAIL_USER_PROMPT,
)
from config.settings import (
    PRIMARY_MODEL, FALLBACK_MODEL,
    TEMPERATURE, GROQ_API_KEY,
    MIN_WORD_COUNT, MAX_WORD_COUNT,
)


def _get_llm(temperature: float = TEMPERATURE) -> ChatGroq:
    return ChatGroq(
        model=PRIMARY_MODEL,
        temperature=temperature,
        api_key=GROQ_API_KEY,
    )


def _parse_lesson_json(raw: str, version: int = 1) -> Lesson:
    """Parse raw LLM output into a Lesson object, with cleanup."""
    # Strip markdown code fences if present
    text = raw.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        # Remove opening fence
        lines = lines[1:]
        # Remove closing fence
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


def generate_lesson(state: AgentState) -> AgentState:
    """
    Node: Generate the initial lesson.
    If demo_fail_mode is True, intentionally produce a bad lesson.
    """
    topic = state["topic"]
    demo_fail = state.get("demo_fail_mode", False)
    memory_instructions = state.get("memory_instructions", "")

    llm = _get_llm()

    if demo_fail:
        system_msg = SystemMessage(content=DEMO_FAIL_SYSTEM_PROMPT)
        user_msg = HumanMessage(content=DEMO_FAIL_USER_PROMPT.format(topic=topic))
    else:
        system_content = GENERATE_SYSTEM_PROMPT.format(
            min_words=MIN_WORD_COUNT,
            max_words=MAX_WORD_COUNT,
            memory_instructions=memory_instructions,
        )
        system_msg = SystemMessage(content=system_content)
        user_msg = HumanMessage(
            content=GENERATE_USER_PROMPT.format(topic=topic)
        )

    response = llm.invoke([system_msg, user_msg])
    lesson = _parse_lesson_json(response.content, version=1)

    return {
        **state,
        "lesson": lesson,
        "retry_count": 0,
        "version_history": [],
    }

