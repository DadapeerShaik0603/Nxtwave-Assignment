# Tests for evaluate_lesson node and EvaluationResult model

import pytest
from models.evaluation import EvaluationResult, CheckpointResult
from pipeline.nodes.evaluate import _parse_evaluation_json


SAMPLE_EVAL_JSON = '''
{
  "passed": false,
  "checkpoint_results": [
    {
      "checkpoint_id": "accurate_and_grounded",
      "name": "Accurate & Grounded",
      "passed": true,
      "reason": "All factual claims about RAG are correct.",
      "suggestion": ""
    },
    {
      "checkpoint_id": "beginner_friendly_language",
      "name": "Beginner-Friendly Language",
      "passed": false,
      "reason": "The term 'embedding' is used without explanation.",
      "suggestion": "Define 'embedding' as 'a way to convert text into numbers so a computer can compare meanings' when first used."
    },
    {
      "checkpoint_id": "teaches_by_example",
      "name": "Teaches by Example",
      "passed": false,
      "reason": "No concrete example was given.",
      "suggestion": "Add a real-world analogy like a customer support chatbot using a knowledge base."
    },
    {
      "checkpoint_id": "covers_key_points",
      "name": "Covers Key Points",
      "passed": true,
      "reason": "What, why, and how are all covered.",
      "suggestion": ""
    },
    {
      "checkpoint_id": "coherent_teaching_flow",
      "name": "Coherent Teaching Flow",
      "passed": true,
      "reason": "Sections follow a logical progression.",
      "suggestion": ""
    },
    {
      "checkpoint_id": "no_unexplained_jargon",
      "name": "No Unexplained Jargon",
      "passed": false,
      "reason": "'Vector database' is used without definition.",
      "suggestion": "Add inline definition: vector database (a special storage that finds similar text fast)."
    },
    {
      "checkpoint_id": "appropriate_length",
      "name": "Appropriate Length",
      "passed": true,
      "reason": "Word count is 650, within 400–1200.",
      "suggestion": ""
    }
  ],
  "overall_feedback": "The lesson has the right structure but uses jargon without explanation and lacks a concrete example."
}
'''


class TestParseEvaluationJson:
    def test_parses_correctly(self):
        result = _parse_evaluation_json(SAMPLE_EVAL_JSON)
        assert isinstance(result, EvaluationResult)
        assert result.passed is False
        assert len(result.checkpoint_results) == 7

    def test_failed_checkpoints(self):
        result = _parse_evaluation_json(SAMPLE_EVAL_JSON)
        failed = result.failed_checkpoints()
        assert len(failed) == 3
        ids = {cp.checkpoint_id for cp in failed}
        assert "beginner_friendly_language" in ids
        assert "teaches_by_example" in ids
        assert "no_unexplained_jargon" in ids

    def test_passed_checkpoints(self):
        result = _parse_evaluation_json(SAMPLE_EVAL_JSON)
        passed = result.passed_checkpoints()
        assert len(passed) == 4

    def test_failure_summary_contains_names(self):
        result = _parse_evaluation_json(SAMPLE_EVAL_JSON)
        summary = result.failure_summary()
        assert "Beginner-Friendly Language" in summary
        assert "Teaches by Example" in summary

    def test_invalid_json_raises(self):
        with pytest.raises(Exception):
            _parse_evaluation_json("garbage")

