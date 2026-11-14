# Tests for MemoryManager

import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch

from memory.manager import MemoryManager


SAMPLE_RUN_HISTORY = {
    "runs": [
        {
            "timestamp": "2026-11-13T10:00:00",
            "topic": "Introduction to RAG",
            "final_passed": True,
            "retry_count": 1,
            "versions": [
                {
                    "version": 1,
                    "failed_checkpoints": [
                        {
                            "checkpoint_id": "teaches_by_example",
                            "name": "Teaches by Example",
                            "reason": "No example given.",
                            "suggestion": "Add a real-world analogy.",
                        }
                    ],
                },
                {
                    "version": 2,
                    "failed_checkpoints": [],
                },
            ],
        }
    ]
}


@pytest.fixture
def manager_with_history(tmp_path):
    """MemoryManager pointed at a temp file with sample history."""
    history_file = tmp_path / "run_history.json"
    history_file.write_text(json.dumps(SAMPLE_RUN_HISTORY), encoding="utf-8")
    with patch("memory.manager.RUN_HISTORY_FILE", history_file):
        yield MemoryManager()


@pytest.fixture
def manager_empty(tmp_path):
    """MemoryManager pointed at an empty temp file."""
    history_file = tmp_path / "run_history.json"
    with patch("memory.manager.RUN_HISTORY_FILE", history_file):
        yield MemoryManager()


class TestMemoryManager:
    def test_empty_history_returns_empty_instructions(self, manager_empty):
        instructions = manager_empty.get_evolved_instructions("Introduction to RAG")
        assert instructions == ""

    def test_evolved_instructions_mentions_past_failure(self, manager_with_history):
        instructions = manager_with_history.get_evolved_instructions("Introduction to RAG")
        assert "teaches_by_example" in instructions
        assert "Add a real-world analogy" in instructions

    def test_no_match_on_unrelated_topic(self, manager_with_history):
        instructions = manager_with_history.get_evolved_instructions("Introduction to Docker")
        assert instructions == ""

    def test_save_run_persists(self, manager_empty, tmp_path):
        manager_empty.save_run(
            topic="Test Topic",
            final_passed=True,
            retry_count=0,
            version_history=[
                {
                    "version": 1,
                    "evaluation": {
                        "passed": True,
                        "checkpoint_results": [],
                        "overall_feedback": "Looks good.",
                    },
                }
            ],
        )
        stats = manager_empty.get_stats()
        assert stats["total_runs"] == 1
        assert stats["passed_first_try"] == 1

    def test_stats_empty(self, manager_empty):
        stats = manager_empty.get_stats()
        assert stats["total_runs"] == 0
        assert stats["pass_rate"] == "N/A"

