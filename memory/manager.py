"""
Memory Manager — persists run history and generates evolved prompt instructions.
Learns from repeated failures to sharpen generation prompts across runs.
"""

import json
import datetime
from pathlib import Path
from typing import List, Dict, Any
from collections import Counter

from config.settings import RUN_HISTORY_FILE


class MemoryManager:
    """
    Reads and writes run history to disk.
    Analyses past failures to inject targeted warnings into future generation prompts.
    """

    def __init__(self):
        self.history_file = RUN_HISTORY_FILE
        self._ensure_history_file()

    # ── File I/O ──────────────────────────────────────────────────────────────

    def _ensure_history_file(self):
        if not self.history_file.exists():
            self.history_file.write_text(json.dumps({"runs": []}, indent=2))

    def _load(self) -> Dict[str, Any]:
        try:
            return json.loads(self.history_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {"runs": []}

    def _save(self, data: Dict[str, Any]):
        self.history_file.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )

    # ── Persist a completed run ───────────────────────────────────────────────

    def save_run(
        self,
        topic: str,
        final_passed: bool,
        retry_count: int,
        version_history: List[dict],
    ):
        """Append a run record to history."""
        data = self._load()
        run_record = {
            "timestamp": datetime.datetime.now().isoformat(),
            "topic": topic,
            "final_passed": final_passed,
            "retry_count": retry_count,
            "versions": [],
        }

        for entry in version_history:
            eval_result = entry.get("evaluation")
            if eval_result:
                failed = [
                    {
                        "checkpoint_id": cp["checkpoint_id"],
                        "name": cp["name"],
                        "reason": cp["reason"],
                        "suggestion": cp["suggestion"],
                    }
                    for cp in eval_result.get("checkpoint_results", [])
                    if not cp["passed"]
                ]
            else:
                failed = []

            run_record["versions"].append({
                "version": entry.get("version", 1),
                "failed_checkpoints": failed,
            })

        data["runs"].append(run_record)
        self._save(data)

    # ── Self-evolution: analyse past failures ─────────────────────────────────

    def get_evolved_instructions(self, topic: str) -> str:
        """
        Read past failure patterns for this topic (and similar topics) and
        return a warning block to inject into the generation prompt.
        """
        data = self._load()
        runs = data.get("runs", [])

        if not runs:
            return ""  # No history yet — no extra instructions

        # Gather all failed checkpoint IDs across relevant runs
        failure_counter: Counter = Counter()
        suggestion_map: Dict[str, str] = {}

        for run in runs:
            # Match by topic substring (case-insensitive)
            if topic.lower() not in run.get("topic", "").lower() and \
               run.get("topic", "").lower() not in topic.lower():
                continue
            for version in run.get("versions", []):
                for cp in version.get("failed_checkpoints", []):
                    cid = cp["checkpoint_id"]
                    failure_counter[cid] += 1
                    if cid not in suggestion_map and cp.get("suggestion"):
                        suggestion_map[cid] = cp["suggestion"]

        if not failure_counter:
            return ""

        lines = [
            "\n⚠️  SELF-EVOLVED WARNINGS (learned from previous failed runs on this topic):",
            "   Address these proactively — they have failed before:\n",
        ]
        for cid, count in failure_counter.most_common():
            suggestion = suggestion_map.get(cid, "")
            lines.append(
                f"   • [{cid}] failed {count} time(s). "
                + (f"Fix: {suggestion}" if suggestion else "")
            )

        return "\n".join(lines)

    # ── Stats helper ──────────────────────────────────────────────────────────

    def get_stats(self) -> Dict[str, Any]:
        data = self._load()
        runs = data.get("runs", [])
        total = len(runs)
        passed_first_try = sum(
            1 for r in runs if r.get("final_passed") and r.get("retry_count", 0) == 0
        )
        return {
            "total_runs": total,
            "passed_first_try": passed_first_try,
            "pass_rate": f"{(passed_first_try / total * 100):.0f}%" if total else "N/A",
        }

