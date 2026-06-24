"""Typer CLI — single entry point `chw` for all workflow operations."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Annotated, Any

import typer
from rich.panel import Panel
from rich.text import Text

from chwflow.models import Workflow
from chwflow.prompts import render_next_prompt
from chwflow.render import console, render_status
from chwflow.state import StateMachine

app = typer.Typer(
    name="chw",
    help="Turn chat history into executable self-reviewing workflow scripts.",
    add_completion=False,
)

SAMPLE_WORKFLOW = {
    "name": "example-agent-workflow",
    "goal": "Turn a rough request into a verified final artifact through short agent prompts.",
    "constraints": [
        "Keep each prompt compact.",
        "Review the previous output before continuing.",
        "Ask for missing inputs only when blocked.",
    ],
    "steps": [
        {
            "id": "scope",
            "title": "Clarify scope",
            "objective": "Extract the goal, inputs, constraints, and done signal.",
            "prompt": "Summarize the task in five bullets and name missing inputs.",
            "acceptance": ["Goal is explicit", "Done signal is testable"],
        },
        {
            "id": "draft",
            "title": "Draft artifact",
            "objective": "Create the first usable version of the requested artifact.",
            "prompt": "Use the scoped requirements to produce the artifact.",
            "acceptance": ["Matches constraints", "No unsupported assumptions"],
        },
        {
            "id": "verify",
            "title": "Verify and refine",
            "objective": "Review the artifact and make targeted improvements.",
            "prompt": "Check the draft against acceptance criteria and revise only what fails.",
            "acceptance": ["Issues are fixed", "Residual risks are listed"],
        },
    ],
}


def _load_json(path: str) -> dict:
    p = Path(path)
    try:
        return json.loads(p.read_text(encoding="utf-8-sig"))
    except FileNotFoundError:
        raise typer.Exit(f"File not found: {path}")
    except json.JSONDecodeError as e:
        raise typer.Exit(f"Invalid JSON in {path}: {e}")


def _read_optional(path: str | None) -> str:
    if not path:
        return ""
    p = Path(path)
    if not p.exists():
        return ""
    return p.read_text(encoding="utf-8-sig")


def _print_error(msg: str) -> None:
    console.print(Panel(Text(msg, style="red"), title="Error", border_style="red"))


def _print_success(msg: str) -> None:
    console.print(Panel(Text(msg, style="green"), title="OK", border_style="green"))


@app.command()
def sample(
    out: Annotated[
        str | None, typer.Option("--out", "-o", help="Write sample workflow JSON to file")
    ] = None,
) -> None:
    """Generate a sample workflow JSON."""
    text = json.dumps(SAMPLE_WORKFLOW, indent=2, ensure_ascii=False) + "\n"
    if out:
        Path(out).write_text(text, encoding="utf-8")
        _print_success(f"Sample workflow written to {out}")
    else:
        console.print_json(text)


@app.command()
def init(
    workflow: Annotated[str, typer.Option(help="Path to workflow JSON file")],
    state: Annotated[str, typer.Option(help="Path for state JSON output")],
    force: Annotated[bool, typer.Option("--force", help="Overwrite existing state")] = False,
) -> None:
    """Initialize workflow state from a workflow definition."""
    if Path(state).exists() and not force:
        _print_error(f"State file already exists: {state}. Use --force to overwrite.")
        raise typer.Exit(1)
    wf = _load_json(workflow)
    Workflow.model_validate(wf)
    sm = StateMachine(wf)
    sm.save(state)
    _print_success(f"State initialized at {state}")


@app.command(name="next")
def next_cmd(
    workflow: Annotated[str, typer.Option(help="Path to workflow JSON file")],
    state: Annotated[str, typer.Option(help="Path to state JSON file")],
    out: Annotated[str | None, typer.Option("--out", "-o", help="Write prompt to file")] = None,
    max_chars: Annotated[
        int, typer.Option("--max-chars", help="Max chars before truncation")
    ] = 6000,
) -> None:
    """Generate the next compact agent prompt."""
    wf = _load_json(workflow)
    st = _load_json(state)
    prompt = render_next_prompt(wf, st, max_chars)
    if out:
        Path(out).write_text(prompt, encoding="utf-8")
        _print_success(f"Prompt written to {out}")
    else:
        console.print(prompt, end="")


@app.command()
def record(
    state: Annotated[str, typer.Option(help="Path to state JSON file")],
    status: Annotated[str, typer.Option(help="Result: ok, needs_revision, blocked")],
    output: Annotated[
        str | None, typer.Option("--output", help="Path to agent output text")
    ] = None,
    review: Annotated[
        str | None, typer.Option("--review", help="Path to review notes text")
    ] = None,
) -> None:
    """Record agent result and advance or retry the step."""
    if status not in ("ok", "needs_revision", "blocked"):
        _print_error(f"Invalid status: {status}. Use ok, needs_revision, or blocked.")
        raise typer.Exit(1)

    sm = StateMachine.from_file(state)
    wf_data = _load_json(state)
    steps: list[dict[str, Any]] = wf_data.get("steps", []) or []
    current = sm.current_step
    step_id = (
        steps[current].get("id", f"step-{current + 1}") if current < len(steps) else "complete"
    )

    sm.record(current, step_id, status, _read_optional(output), _read_optional(review))
    sm.save(state)
    console.print(
        f"[bold]Recorded[/] [cyan]{status}[/] for step {current}. Current step: [cyan]{sm.current_step}[/]"
    )


@app.command(name="status")
def status_cmd(
    state: Annotated[str, typer.Option(help="Path to state JSON file")],
) -> None:
    """Show current workflow state as a table."""
    st = _load_json(state)
    render_status(st)


@app.command()
def run(
    workflow: Annotated[str, typer.Option(help="Path to workflow JSON file")],
    dry_run: Annotated[
        bool, typer.Option("--dry-run", help="Preview actions without executing")
    ] = False,
) -> None:
    """Execute deterministic workflow steps (automation runner pattern)."""
    from chwflow.engine import WorkflowEngine

    wf = _load_json(workflow)
    engine = WorkflowEngine(wf)
    results = engine.execute(dry_run=dry_run)

    for _i, r in enumerate(results):
        icon = "✓" if r.ok else "✗"
        color = "green" if r.ok else "red"
        console.print(f"  {icon} [{color}]{r.step_id}[/{color}]: {r.output}")
        if r.error:
            console.print(f"    [red]💥 {r.error}[/red]")


@app.command()
def watch(
    workflow: Annotated[str, typer.Option(help="Path to workflow JSON file")],
    state: Annotated[str, typer.Option(help="Path to state JSON file")],
    interval: Annotated[
        float, typer.Option("--interval", "-i", help="Poll interval in seconds")
    ] = 5.0,
) -> None:
    """Watch workflow state and auto-generate next prompt when ready."""
    console.print(f"[cyan]Watching {state} every {interval}s...[/cyan]")
    try:
        while True:
            st = _load_json(state)
            render_status(st)
            if st.get("status") == "complete":
                _print_success("Workflow complete.")
                break
            if st.get("status") == "blocked":
                console.print("[yellow]Workflow blocked — waiting for unblock.[/yellow]")
            time.sleep(interval)
    except KeyboardInterrupt:
        console.print("[yellow]Watch stopped.[/yellow]")


@app.command()
def version() -> None:
    """Show chwflow version."""
    from chwflow import __version__

    console.print(f"[bold]chw[/] v{__version__}")
