"""
Pydantic models for the Evaluation result produced by the evaluator.
"""

from pydantic import BaseModel, Field
from typing import List


class CheckpointResult(BaseModel):
    checkpoint_id: str = Field(description="Unique ID of this checkpoint")
    name: str = Field(description="Human-readable checkpoint name")
    passed: bool = Field(description="True if checkpoint passes, False otherwise")
    reason: str = Field(description="Explanation of why it passed or failed")
    suggestion: str = Field(
        default="",
        description="Actionable suggestion for improvement (only on failure)"
    )


class EvaluationResult(BaseModel):
    passed: bool = Field(
        description="True only if ALL checkpoints pass"
    )
    checkpoint_results: List[CheckpointResult] = Field(
        description="Per-checkpoint pass/fail results"
    )
    overall_feedback: str = Field(
        description="One-paragraph summary of the evaluation"
    )

    def failed_checkpoints(self) -> List[CheckpointResult]:
        return [cp for cp in self.checkpoint_results if not cp.passed]

    def passed_checkpoints(self) -> List[CheckpointResult]:
        return [cp for cp in self.checkpoint_results if cp.passed]

    def failure_summary(self) -> str:
        """Return a compact string listing all failures with reasons and suggestions."""
        failures = self.failed_checkpoints()
        if not failures:
            return "All checkpoints passed."
        lines = []
        for cp in failures:
            lines.append(
                f"- [{cp.name}] FAILED: {cp.reason} "
                f"→ Suggestion: {cp.suggestion}"
            )
        return "\n".join(lines)

