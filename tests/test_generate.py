# Tests for generate_lesson node

import pytest
from unittest.mock import patch, MagicMock
from pipeline.nodes.generate import _parse_lesson_json
from models.lesson import Lesson


SAMPLE_JSON = '''
{
  "title": "Introduction to RAG",
  "introduction": "Have you ever asked an AI chatbot a question and got a completely wrong answer?",
  "sections": [
    {
      "heading": "What is RAG?",
      "content": "RAG stands for Retrieval-Augmented Generation. Think of it as giving your AI a textbook to look up answers from before it responds."
    },
    {
      "heading": "Why Do We Need RAG?",
      "content": "Normal AI models only know what they learned during training. They cannot look up new information."
    },
    {
      "heading": "How Does RAG Work?",
      "content": "Step 1: Retrieve. Step 2: Augment. Step 3: Generate."
    },
    {
      "heading": "Real-World Example",
      "content": "Imagine a customer support bot for a bank. Without RAG it would give outdated answers. With RAG it looks up the latest policies first."
    }
  ],
  "summary": "RAG makes AI smarter by letting it look up real information before answering.",
  "version": 1
}
'''

SAMPLE_JSON_WITH_FENCE = "```json\n" + SAMPLE_JSON.strip() + "\n```"


class TestParseLessonJson:
    def test_parses_plain_json(self):
        lesson = _parse_lesson_json(SAMPLE_JSON, version=1)
        assert isinstance(lesson, Lesson)
        assert lesson.title == "Introduction to RAG"
        assert len(lesson.sections) == 4
        assert lesson.version == 1

    def test_strips_markdown_fences(self):
        lesson = _parse_lesson_json(SAMPLE_JSON_WITH_FENCE, version=1)
        assert lesson.title == "Introduction to RAG"

    def test_word_count_nonzero(self):
        lesson = _parse_lesson_json(SAMPLE_JSON, version=1)
        assert lesson.word_count() > 50

    def test_to_markdown_contains_title(self):
        lesson = _parse_lesson_json(SAMPLE_JSON, version=1)
        md = lesson.to_markdown()
        assert "Introduction to RAG" in md

    def test_version_override(self):
        lesson = _parse_lesson_json(SAMPLE_JSON, version=3)
        assert lesson.version == 3

    def test_invalid_json_raises(self):
        with pytest.raises(Exception):
            _parse_lesson_json("not valid json", version=1)

