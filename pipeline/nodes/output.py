"""
LangGraph pipeline nodes: output_lesson + persist_memory

Log retention strategy:
  - output/lesson_final.md          → always the LATEST lesson (overwritten)
  - output/rejection_log.md         → always the LATEST rejection log (overwritten)
  - output/runs/YYYYMMDD_HHMMSS_lesson.md      → archived copy of every lesson
  - output/runs/YYYYMMDD_HHMMSS_rejection.md   → archived copy of every rejection log
  - output/all_runs_log.md          → cumulative append-only master log of all runs
"""

import datetime
from pathlib import Path

from pipeline.state import AgentState
from config.settings import OUTPUT_DIR


def output_lesson(state: AgentState) -> AgentState:
    """
    Node: Write final lesson and rejection log to output/ directory.
    - Overwrites the 'latest' files for easy access
    - Archives timestamped copies so no run is ever lost
    - Appends a summary to the cumulative master log
    """
    lesson = state["lesson"]
    evaluation = state["evaluation"]
    version_history = state.get("version_history", [])
    topic = state["topic"]
    retry_count = state.get("retry_count", 0)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    final_passed = evaluation.passed if evaluation else False

    lesson_content = _build_lesson_file(lesson, topic, final_passed, retry_count, timestamp)
    log_content = _build_rejection_log(topic, version_history, evaluation, retry_count, timestamp)

    # ── 1. Overwrite "latest" files (easy access) ─────────────────────────────
    latest_lesson_path = OUTPUT_DIR / "lesson_final.md"
    latest_log_path    = OUTPUT_DIR / "rejection_log.md"
    latest_lesson_path.write_text(lesson_content, encoding="utf-8")
    latest_log_path.write_text(log_content, encoding="utf-8")

    # ── 2. Archive timestamped copies (never overwritten) ─────────────────────
    runs_dir = OUTPUT_DIR / "runs"
    runs_dir.mkdir(exist_ok=True)

    archived_lesson_path = runs_dir / f"{timestamp}_lesson.md"
    archived_log_path    = runs_dir / f"{timestamp}_rejection.md"
    archived_lesson_path.write_text(lesson_content, encoding="utf-8")
    archived_log_path.write_text(log_content, encoding="utf-8")

    # ── 3. Append one-line summary to cumulative master log ───────────────────
    master_log_path = OUTPUT_DIR / "all_runs_log.md"
    _append_to_master_log(
        master_log_path, topic, timestamp,
        final_passed, retry_count, version_history,
        archived_lesson_path, archived_log_path,
    )

    return {
        **state,
        "output_lesson_path":   str(latest_lesson_path),
        "output_log_path":      str(latest_log_path),
        "archived_lesson_path": str(archived_lesson_path),
        "archived_log_path":    str(archived_log_path),
    }


# ── File builders ─────────────────────────────────────────────────────────────

def _build_lesson_file(lesson, topic, passed, retry_count, timestamp) -> str:
    status = "✅ PASSED" if passed else "⚠️ MAX RETRIES REACHED"
    header = f"""---
title: "{lesson.title}"
topic: "{topic}"
status: "{status}"
version: {lesson.version}
retries: {retry_count}
generated_at: "{timestamp}"
---

"""
    return header + lesson.to_markdown()


def _build_rejection_log(topic, version_history, final_evaluation, retry_count, timestamp) -> str:
    lines = [
        "# 📋 Rejection Log — Self-Evaluation Pipeline",
        "",
        f"**Topic:** {topic}  ",
        f"**Generated at:** {timestamp}  ",
        f"**Total retries:** {retry_count}  ",
        f"**Final status:** {'✅ PASSED' if (final_evaluation and final_evaluation.passed) else '❌ FAILED / MAX RETRIES'}",
        "",
        "---",
        "",
    ]

    for entry in version_history:
        version = entry.get("version", "?")
        eval_data = entry.get("evaluation", {})
        checkpoint_results = eval_data.get("checkpoint_results", [])
        overall = eval_data.get("overall_feedback", "")
        overall_passed = eval_data.get("passed", False)

        lines.append(f"## Version {version} Evaluation")
        lines.append("")
        lines.append(f"**Overall:** {'✅ PASSED' if overall_passed else '❌ FAILED'}  ")
        lines.append(f"**Feedback:** {overall}")
        lines.append("")
        lines.append("### Checkpoint Results")
        lines.append("")
        lines.append("| Checkpoint | Status | Reason | Suggestion |")
        lines.append("|---|---|---|---|")

        for cp in checkpoint_results:
            status_icon = "✅ PASS" if cp["passed"] else "❌ FAIL"
            reason     = cp["reason"].replace("|", "\\|")
            suggestion = cp.get("suggestion", "").replace("|", "\\|") or "—"
            lines.append(
                f"| **{cp['name']}** | {status_icon} | {reason} | {suggestion} |"
            )

        lines.append("")

        if version > 1:
            lines.append(f"### What Changed in Version {version}")
            lines.append("")
            failed_in_prev = [cp for cp in checkpoint_results if not cp["passed"]]
            if failed_in_prev:
                lines.append(
                    f"Regenerated to fix {len(failed_in_prev)} failed checkpoint(s). "
                    "See suggestions column above for what was addressed."
                )
            lines.append("")

        lines.append("---")
        lines.append("")

    if final_evaluation:
        lines.append("## Final Evaluation Summary")
        lines.append("")
        passed_cps = final_evaluation.passed_checkpoints()
        failed_cps = final_evaluation.failed_checkpoints()
        lines.append(f"- ✅ Passed: {len(passed_cps)} checkpoint(s)")
        lines.append(f"- ❌ Failed: {len(failed_cps)} checkpoint(s)")
        if failed_cps:
            lines.append("")
            lines.append("### Remaining Failures (shipped with caveats)")
            for cp in failed_cps:
                lines.append(f"- **{cp.name}**: {cp.reason}")

    return "\n".join(lines)


def _append_to_master_log(
    master_log_path: Path,
    topic: str,
    timestamp: str,
    final_passed: bool,
    retry_count: int,
    version_history: list,
    archived_lesson_path: Path,
    archived_log_path: Path,
):
    """
    Append a full run record to the cumulative all_runs_log.md.
    Includes: summary table + all checkpoint results + full lesson content.
    """

    # Create header if file doesn't exist yet
    if not master_log_path.exists():
        master_log_path.write_text(
            "# 📚 All Runs — Cumulative Log\n\n"
            "> Every pipeline run is recorded here. Newest runs appear at the bottom.\n\n"
            "---\n\n",
            encoding="utf-8",
        )

    status_icon = "✅ PASSED" if final_passed else "❌ FAILED"
    num_versions = len(version_history)

    # Format timestamp: YYYYMMDD_HHMMSS → YYYY-MM-DD HH:MM:SS
    dt_display = (
        f"{timestamp[:4]}-{timestamp[4:6]}-{timestamp[6:8]} "
        f"{timestamp[9:11]}:{timestamp[11:13]}:{timestamp[13:15]}"
    )

    lines = []

    # ── Run header ────────────────────────────────────────────────────────────
    lines += [
        f"## 🏃 Run — {dt_display}",
        "",
        f"| Field | Value |",
        f"|---|---|",
        f"| **Topic** | {topic} |",
        f"| **Final Status** | {status_icon} |",
        f"| **Retries used** | {retry_count} / 2 |",
        f"| **Versions generated** | {num_versions} |",
        f"| **Archived lesson** | `runs/{archived_lesson_path.name}` |",
        f"| **Archived eval log** | `runs/{archived_log_path.name}` |",
        "",
    ]

    # ── Per-version evaluation details ───────────────────────────────────────
    lines += ["### 🔍 Evaluation Results (All Versions)", ""]

    for entry in version_history:
        version    = entry.get("version", "?")
        eval_data  = entry.get("evaluation", {})
        cps        = eval_data.get("checkpoint_results", [])
        overall    = eval_data.get("overall_feedback", "—")
        v_passed   = eval_data.get("passed", False)
        v_icon     = "✅ PASSED" if v_passed else "❌ FAILED"

        lines += [
            f"#### Version {version} — {v_icon}",
            "",
            f"> {overall}",
            "",
            "| Checkpoint | Status | Reason | Suggestion |",
            "|---|---|---|---|",
        ]

        for cp in cps:
            s_icon     = "✅ PASS" if cp["passed"] else "❌ FAIL"
            reason     = cp["reason"].replace("|", "\\|")
            suggestion = cp.get("suggestion", "").replace("|", "\\|") or "—"
            lines.append(f"| **{cp['name']}** | {s_icon} | {reason} | {suggestion} |")

        lines.append("")

        if not v_passed:
            failed_cps = [cp for cp in cps if not cp["passed"]]
            lines += [
                f"**{len(failed_cps)} checkpoint(s) failed → lesson regenerated.**",
                "",
            ]

    # ── Full lesson content ───────────────────────────────────────────────────
    lines += [
        "### 📄 Final Lesson Content",
        "",
    ]

    if archived_lesson_path.exists():
        lesson_text = archived_lesson_path.read_text(encoding="utf-8")
        # Strip YAML frontmatter (--- ... ---) for cleaner embedding
        parts = lesson_text.split("---")
        if len(parts) >= 3:
            lesson_body = "---".join(parts[2:]).strip()
        else:
            lesson_body = lesson_text.strip()
        lines.append(lesson_body)
    else:
        lines.append("*(lesson file not found)*")

    lines += ["", "---", ""]

    with open(master_log_path, "a", encoding="utf-8") as f:
        f.write("\n".join(lines))
