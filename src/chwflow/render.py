"""Rich-based rendering for CLI output: tables, progress, color, status."""

from __future__ import annotations

from rich import box
from rich.console import Console
from rich.table import Table
from rich.text import Text

console = Console()

_STATUS_COLORS: dict[str, str] = {
    "active": "cyan",
    "complete": "green",
    "failed": "red",
    "ok": "green",
    "needs_revision": "yellow",
}


def status_color(status: str) -> str:
    return _STATUS_COLORS.get(status, "white")


def render_status(state: dict) -> None:
    """Print a colorful status table for the current workflow state."""
    table = Table(title=f"Workflow: {state.get('workflow_name', 'unknown')}", box=box.ROUNDED)
    table.add_column("Field", style="bold cyan")
    table.add_column("Value", style="white")

    table.add_row("Current Step", str(state.get("current_step", 0)))
    table.add_row(
        "Status",
        Text(state.get("status", "active"), style=status_color(state.get("status", "active"))),
    )
    table.add_row("History Entries", str(len(state.get("history", []))))
    table.add_row("Last Updated", state.get("updated_at", "N/A"))

    if state.get("history"):
        last = state["history"][-1]
        table.add_row(
            "Last Step Status",
            Text(last.get("status", ""), style=status_color(last.get("status", ""))),
        )

    console.print(table)


def render_step(step_index: int, step: dict, status: str = "active") -> None:
    """Render a single step with color-coded status."""
    color = status_color(status)
    icon = {"ok": "✓", "active": "●", "needs_revision": "↻", "blocked": "⊘", "failed": "✗"}.get(
        status, "○"
    )
    line = Text(f"  {icon} [{step_index}] {step.get('title', step.get('id', '???'))}", style=color)
    console.print(line)


def render_progress(current: int, total: int, status: str) -> None:
    """Render a progress bar for multi-step workflows."""
    from rich.progress import Progress

    with Progress() as progress:
        task = progress.add_task("[cyan]Workflow progress", total=total)
        progress.update(
            task, completed=current, description=f"[{status_color(status)}]Step {current}/{total}"
        )
