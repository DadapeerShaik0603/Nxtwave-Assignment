"""
main.py — Entry point for the Self-Evaluating Lesson Content Generator.

Usage:
    python main.py --topic "Introduction to RAG"
    python main.py --topic "Introduction to RAG" --demo-fail
    python main.py --stats
"""

import argparse
import sys
import time

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import box

from pipeline.graph import build_graph
from memory.manager import MemoryManager
from config.settings import MAX_RETRIES, OUTPUT_DIR

console = Console()


# ── CLI argument parsing ──────────────────────────────────────────────────────

def parse_args():
    parser = argparse.ArgumentParser(
        description="Self-Evaluating Lesson Content Generator (Groq + LangGraph)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --topic "Introduction to RAG"
  python main.py --topic "Introduction to RAG" --demo-fail
  python main.py --stats
        """,
    )
    parser.add_argument(
        "--topic", "-t",
        type=str,
        default="Introduction to RAG (Retrieval-Augmented Generation)",
        help="Topic to generate a lesson for (default: Introduction to RAG)",
    )
    parser.add_argument(
        "--demo-fail",
        action="store_true",
        default=False,
        help="Force a deliberately bad first generation to demo the evaluator catching errors",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        default=False,
        help="Show memory stats from previous runs and exit",
    )
    return parser.parse_args()


# ── UI helpers ────────────────────────────────────────────────────────────────

def print_banner():
    console.print(Panel.fit(
        "[bold cyan]🧠 Self-Evaluating Lesson Content Generator[/bold cyan]\n"
        "[dim]Powered by LangGraph + Groq (openai/gpt-oss-120b)[/dim]",
        border_style="cyan",
    ))
    console.print()


def print_phase(label: str, icon: str = "🔄"):
    console.print(f"\n[bold yellow]{icon}  {label}[/bold yellow]")


def print_evaluation(evaluation, version: int):
    """Pretty-print evaluation results as a Rich table."""
    passed_icon = "✅ PASSED" if evaluation.passed else "❌ FAILED"
    color = "green" if evaluation.passed else "red"

    console.print(f"\n[bold {color}]Evaluation v{version}: {passed_icon}[/bold {color}]")
    console.print(f"[dim]{evaluation.overall_feedback}[/dim]\n")

    table = Table(box=box.ROUNDED, show_header=True, header_style="bold magenta")
    table.add_column("Checkpoint", style="cyan", no_wrap=True)
    table.add_column("Status", justify="center")
    table.add_column("Reason", max_width=55)
    table.add_column("Suggestion", max_width=35, style="dim")

    for cp in evaluation.checkpoint_results:
        status = "[green]✅ PASS[/green]" if cp.passed else "[red]❌ FAIL[/red]"
        table.add_row(
            cp.name,
            status,
            cp.reason,
            cp.suggestion or "—",
        )

    console.print(table)


def print_success(final_state: dict, retry_count: int):
    lesson_path          = final_state.get("output_lesson_path", "output/lesson_final.md")
    log_path             = final_state.get("output_log_path",    "output/rejection_log.md")
    archived_lesson_path = final_state.get("archived_lesson_path", "")
    archived_log_path    = final_state.get("archived_log_path",    "")
    master_log           = str(OUTPUT_DIR / "all_runs_log.md")

    console.print(Panel(
        f"[bold green]✅ Pipeline complete![/bold green]\n\n"
        f"[bold]Latest (overwritten each run):[/bold]\n"
        f"  📄 Lesson       → [cyan]{lesson_path}[/cyan]\n"
        f"  📋 Eval log     → [cyan]{log_path}[/cyan]\n\n"
        f"[bold]Archived (this run, permanent):[/bold]\n"
        f"  📄 Lesson       → [cyan]{archived_lesson_path}[/cyan]\n"
        f"  📋 Eval log     → [cyan]{archived_log_path}[/cyan]\n\n"
        f"[bold]Cumulative history:[/bold]\n"
        f"  📚 All runs log → [cyan]{master_log}[/cyan]\n\n"
        f"🔁 Retries used  → [yellow]{retry_count} / {MAX_RETRIES}[/yellow]",
        border_style="green",
        title="Output",
    ))


def print_stats(stats: dict):
    console.print(Panel(
        f"[bold]Memory Stats[/bold]\n\n"
        f"Total runs       : [cyan]{stats['total_runs']}[/cyan]\n"
        f"Passed 1st try   : [green]{stats['passed_first_try']}[/green]\n"
        f"First-pass rate  : [yellow]{stats['pass_rate']}[/yellow]",
        border_style="blue",
        title="📊 Self-Evolution Memory",
    ))


# ── Main pipeline runner ──────────────────────────────────────────────────────

def run_pipeline(topic: str, demo_fail: bool):
    print_banner()

    if demo_fail:
        console.print("[bold red]⚠️  DEMO FAIL MODE — first generation will intentionally be bad[/bold red]\n")

    # Load memory-evolved instructions
    memory = MemoryManager()
    memory_instructions = memory.get_evolved_instructions(topic)

    if memory_instructions:
        console.print(Panel(
            memory_instructions,
            title="🧬 Self-Evolved Warnings from Memory",
            border_style="yellow",
        ))

    # Build the LangGraph graph
    graph = build_graph()

    # Initial state
    initial_state = {
        "topic": topic,
        "demo_fail_mode": demo_fail,
        "lesson": None,
        "evaluation": None,
        "retry_count": 0,
        "version_history": [],
        "memory_instructions": memory_instructions,
    }

    # Run the graph with live status updates
    console.print(f"\n[bold]Topic:[/bold] {topic}\n")

    version = 1
    final_state = None

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:

        # Stream events from the graph
        task = progress.add_task("Generating lesson...", total=None)

        for event in graph.stream(initial_state, stream_mode="updates"):
            node_name = list(event.keys())[0]
            node_state = event[node_name]

            if node_name == "generate_lesson":
                progress.update(task, description=f"[cyan]✍️  Generating lesson v{version}...[/cyan]")
                lesson = node_state.get("lesson")
                if lesson:
                    console.print(
                        f"\n[dim]📝 Generated: '{lesson.title}' "
                        f"({lesson.word_count()} words)[/dim]"
                    )

            elif node_name == "evaluate_lesson":
                progress.update(task, description=f"[yellow]🔍 Evaluating lesson v{version}...[/yellow]")
                evaluation = node_state.get("evaluation")
                if evaluation:
                    print_evaluation(evaluation, version)

            elif node_name == "regenerate_lesson":
                version += 1
                progress.update(task, description=f"[magenta]🔄 Regenerating lesson v{version}...[/magenta]")
                console.print(f"\n[magenta]🔄 Regenerating → v{version}[/magenta]")

            elif node_name == "output_lesson":
                progress.update(task, description="[green]💾 Writing output files...[/green]")

            elif node_name == "persist_memory":
                progress.update(task, description="[blue]🧠 Saving to memory...[/blue]")

            final_state = node_state

    # Print final summary
    if final_state:
        retry_count = final_state.get("retry_count", 0)
        print_success(final_state, retry_count)

        # Show a snippet of the final lesson
        lesson = final_state.get("lesson")
        if lesson:
            console.print("\n[bold]📖 Lesson Preview:[/bold]")
            console.print(Panel(
                Markdown(lesson.introduction[:500] + ("…" if len(lesson.introduction) > 500 else "")),
                title=lesson.title,
                border_style="cyan",
            ))


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    args = parse_args()

    if args.stats:
        memory = MemoryManager()
        print_stats(memory.get_stats())
        return

    try:
        run_pipeline(
            topic=args.topic,
            demo_fail=args.demo_fail,
        )
    except KeyboardInterrupt:
        console.print("\n[red]Interrupted by user.[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[bold red]Error:[/bold red] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

