"""PromptRenderer — emit compact, self-reviewing prompts for multi-step agent workflows.

Ported from the original scripts/prompt_loop_runner.py, now with Pydantic models
and clean separation from CLI/state concerns.
"""

from __future__ import annotations

from typing import Any


def _compact(value: Any, fallback: str = "Not specified.") -> str:
    if value is None:
        return fallback
    if isinstance(value, list):
        return "\n".join(f"- {item}" for item in value) if value else fallback
    if isinstance(value, dict):
        return "\n".join(f"- {k}: {v}" for k, v in value.items()) if value else fallback
    text = str(value).strip()
    return text if text else fallback


def _truncate(text: str, limit: int) -> str:
    text = text.strip()
    if len(text) <= limit:
        return text
    return text[: limit - 80].rstrip() + "\n\n[truncated]"


def render_next_prompt(
    workflow: dict[str, Any],
    state: dict[str, Any],
    max_chars: int = 6000,
) -> str:
    """Render the next compact agent prompt, including a self-review gate."""
    steps: list[dict[str, Any]] = workflow.get("steps", [])
    if not steps:
        raise ValueError("Workflow must have at least one step")

    current_index = int(state.get("current_step", 0))
    name = workflow.get("name", "workflow")

    if current_index >= len(steps):
        return _render_completion_prompt(name)

    current = steps[current_index]
    previous = steps[current_index - 1] if current_index > 0 else None

    history_list: list[dict[str, Any]] = state.get("history", [])
    last_output = _truncate(_last_field(history_list, "output"), max_chars)
    last_review = _truncate(_last_field(history_list, "review"), max_chars // 2)

    review_block = _build_review_block(previous, current_index, last_output, last_review)

    lines = [
        "You are executing a multi-step workflow from a compact controller prompt.",
        "",
        f"Workflow: {name}",
        "Goal:",
        _compact(workflow.get("goal")),
        "",
        "Stable constraints:",
        _compact(workflow.get("constraints")),
        "",
        "Self-review gate:",
        review_block,
        "",
        f"Current step: {current.get('id', f'step-{current_index + 1}')} — "
        f"{current.get('title', current.get('objective', 'Untitled'))}",
        "Objective:",
        _compact(current.get("objective")),
        "",
        "Instructions:",
        _compact(current.get("prompt") or current.get("instructions")),
        "",
        "Acceptance criteria:",
        _compact(current.get("acceptance")),
        "",
        "Output format:",
        "1. Previous-step review: OK / partially OK / needs revision, with evidence.",
        "2. Work performed for the current step.",
        "3. Result or artifact.",
        "4. Suggested status: ok / needs_revision / blocked.",
        "5. If blocked, name the exact missing input.",
    ]
    return "\n".join(lines).strip() + "\n"


def _last_field(history: list[dict[str, Any]], field: str) -> str:
    if not history:
        return ""
    return str(history[-1].get(field, ""))


def _build_review_block(
    previous: dict[str, Any] | None,
    current_index: int,
    last_output: str,
    last_review: str,
) -> str:
    if previous is None:
        return "No previous step. Start by checking the goal and assumptions."

    return "\n".join(
        [
            "Review the previous step before doing new work.",
            f"Previous step: {previous.get('id', current_index)} — "
            f"{previous.get('title', previous.get('objective', 'Untitled'))}",
            "Previous acceptance criteria:",
            _compact(previous.get("acceptance")),
            "",
            "Previous output:",
            last_output or "No previous output was recorded.",
            "",
            "Prior review notes:",
            last_review or "No prior review notes were recorded.",
            "",
            "Decide whether the previous output is OK, partially OK, or needs revision. "
            "If it needs revision, fix the issue before advancing.",
        ]
    )


def _render_completion_prompt(name: str) -> str:
    return (
        f"Workflow `{name}` is complete.\n\n"
        "Produce a final concise summary:\n"
        "1. What was completed.\n"
        "2. Evidence that the result satisfies the goal.\n"
        "3. Any residual risks or follow-up actions.\n"
    )
