"""
display.py  –  Rich UI helpers for the DSPy Prompt Evolution Demo
=================================================================
Contains all terminal rendering: stage headers, prompt snapshots,
the optimisation summary table, the prompt diff table, and the
Chain-of-Thought live inference section.
"""

from __future__ import annotations

import textwrap

import dspy
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table

# ── Stage colour palette ──────────────────────────────────────
STAGE_COLORS = ["yellow", "cyan", "magenta"]


# ─────────────────────────────────────────────────────────────
# Header
# ─────────────────────────────────────────────────────────────

def print_stage_header(console: Console, stage: int, title: str) -> None:
    color = STAGE_COLORS[stage % len(STAGE_COLORS)]
    console.print()
    console.print(Rule(f"[bold {color}]Stage {stage}: {title}[/bold {color}]", style=color))


# ─────────────────────────────────────────────────────────────
# Prompt snapshot panel
# ─────────────────────────────────────────────────────────────

def print_prompt_snapshot(
    console: Console, stage: int, label: str, snapshots: dict
) -> None:
    color = STAGE_COLORS[stage % len(STAGE_COLORS)]
    for predictor_name, snap in snapshots.items():
        lines = [
            f"[bold]Predictor:[/bold] {predictor_name}",
            f"[bold]Instructions:[/bold]\n  "
            + textwrap.fill(snap["instructions"], width=80, subsequent_indent="  "),
            f"[bold]Few-shot examples included:[/bold] {snap['num_demos']}",
        ]
        if snap["demos"]:
            lines.append("\n[bold]Examples given to the LLM (first 3):[/bold]")
            for i, demo in enumerate(snap["demos"], 1):
                fields = dict(demo.items()) if hasattr(demo, "items") else vars(demo)
                demo_lines = [
                    f"    [{k}]: {textwrap.fill(str(v), width=70, subsequent_indent='      ')}"
                    for k, v in fields.items()
                    if not k.startswith("_")
                ]
                lines.append(f"  Example #{i}:\n" + "\n".join(demo_lines))

        console.print(
            Panel(
                "\n".join(lines),
                title=f"[bold {color}]{label} — Prompt Snapshot[/bold {color}]",
                border_style=color,
                expand=False,
                padding=(1, 2),
            )
        )


# ─────────────────────────────────────────────────────────────
# Optimisation summary table
# ─────────────────────────────────────────────────────────────

def print_comparison_table(console: Console, stages: list[dict]) -> None:
    console.print()
    console.print(Rule("[bold white]📈  Optimization Summary[/bold white]"))
    table = Table(box=box.ROUNDED, show_header=True, header_style="bold white")
    table.add_column("Stage",        style="bold", justify="center")
    table.add_column("Optimizer",    justify="left")
    table.add_column("# Examples",   justify="center")
    table.add_column("Accuracy",     justify="center")
    table.add_column("Δ vs Baseline", justify="center")

    baseline_score = stages[0]["score"] if stages else 0.0
    colors = STAGE_COLORS

    for i, stage in enumerate(stages):
        delta = stage["score"] - baseline_score
        delta_str = f"+{delta:.1%}" if delta > 0 else f"{delta:.1%}"
        delta_color = "green" if delta > 0 else ("red" if delta < 0 else "white")

        table.add_row(
            f"[{colors[i % len(colors)]}]Stage {i}[/{colors[i % len(colors)]}]",
            stage["optimizer"],
            str(stage["num_demos"]),
            f"[bold]{stage['score']:.1%}[/bold]",
            f"[{delta_color}]{delta_str if i > 0 else '—'}[/{delta_color}]",
        )

    console.print(table)


# ─────────────────────────────────────────────────────────────
# Prompt diff table  (Stage 0 vs Stage 2)
# ─────────────────────────────────────────────────────────────

def render_full_prompt(snap: dict) -> str:
    """Takes a snapshot dictionary and renders it as the full prompt text the LLM sees."""
    lines = []
    lines.append(f"[bold]Instructions:[/bold]\n{textwrap.fill(snap['instructions'], width=50)}")
    lines.append("")
    
    if snap["num_demos"] > 0:
        lines.append(f"[bold]Examples (showing {len(snap['demos'])} of {snap['num_demos']}):[/bold]")
        for i, demo in enumerate(snap["demos"], 1):
            lines.append(f"\n[bold]--- Example {i} ---[/bold]")
            fields = dict(demo.items()) if hasattr(demo, "items") else vars(demo)
            for k, v in fields.items():
                if not k.startswith("_") and k != "augmented":
                    # Only show the relevant parts to match the actual prompt
                    val = textwrap.fill(str(v), width=48, subsequent_indent="  ")
                    lines.append(f"[dim]{k}:[/dim] {val}")
    else:
        lines.append("[dim]No few-shot examples provided.[/dim]")
    
    return "\n".join(lines)


def print_prompt_diff(
    console: Console, snap_before: dict, snap_after: dict
) -> None:
    console.print()
    console.print(Rule("[bold white]🔍  Prompt Diff: Stage 0 → Stage 2[/bold white]"))
    console.print(
        "  [dim]Showing the complete assembled prompt text that the LLM receives at each stage.[/dim]\n"
    )

    for name in snap_before:
        before = snap_before[name]
        after  = snap_after.get(name, before)

        table = Table(
            box=box.ROUNDED,
            show_header=True,
            header_style="bold white",
            expand=True,
            show_lines=True,
        )
        table.add_column("Stage 0 · Baseline (Zero-Shot)", style="yellow", ratio=1)
        table.add_column("Stage 2 · Optimized (Few-Shot)", style="magenta", ratio=1)

        full_before = render_full_prompt(before)
        full_after  = render_full_prompt(after)

        table.add_row(full_before, full_after)

        console.print(table)


# ─────────────────────────────────────────────────────────────
# Chain-of-Thought live inference examples
# ─────────────────────────────────────────────────────────────

COT_REVIEWS = [
    "The performances are outstanding, but the third act completely falls apart.",
    "A visually dazzling and emotionally rich experience I won't forget.",
    "A waste of a great premise. Boring, predictable, and deeply disappointing.",
]


def print_cot_examples(
    console: Console, program: dspy.Module, lm: dspy.LM
) -> None:
    console.print()
    console.print(Rule("[bold white]🧠  Chain of Thought — Live Example[/bold white]"))
    console.print(
        "  [dim]Running the best optimised program on fresh reviews\n"
        "  and showing the full intermediate reasoning trace.[/dim]\n"
    )

    label_colors = {"Positive": "green", "Negative": "red", "Mixed": "yellow"}

    with dspy.context(lm=lm):
        for review_text in COT_REVIEWS:
            prediction = program(review=review_text)
            label = prediction.sentiment
            color = label_colors.get(label, "white")

            content = (
                f"[bold]Review:[/bold]\n  {review_text}\n\n"
                "[bold]Chain of Thought (reasoning):[/bold]\n"
                + "\n".join(
                    f"  {line}"
                    for line in textwrap.wrap(prediction.reasoning, width=76)
                )
                + f"\n\n[bold]Prediction:[/bold] [{color}][bold]{label}[/bold][/{color}]"
            )
            console.print(
                Panel(content, border_style="bright_blue", expand=False, padding=(1, 2))
            )
