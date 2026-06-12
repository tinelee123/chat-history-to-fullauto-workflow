#!/usr/bin/env python3
"""Generate compact, self-reviewing prompts for multi-step agent workflows.

This script does not call an LLM. It keeps workflow state in JSON and emits the
next prompt to send to any agent. Each prompt asks the agent to review the
previous step's output before continuing.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from textwrap import dedent
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError:
        raise SystemExit(f"File not found: {path}")
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON in {path}: {exc}")


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def default_state(workflow: dict[str, Any]) -> dict[str, Any]:
    return {
        "workflow_name": workflow.get("name", "workflow"),
        "current_step": 0,
        "status": "active",
        "history": [],
        "last_output": "",
        "last_review": "",
        "updated_at": now_iso(),
    }


def step_list(workflow: dict[str, Any]) -> list[dict[str, Any]]:
    steps = workflow.get("steps")
    if not isinstance(steps, list) or not steps:
        raise SystemExit("Workflow JSON must contain a non-empty 'steps' array.")
    normalized = []
    for index, step in enumerate(steps, start=1):
        if isinstance(step, str):
            normalized.append({"id": f"step-{index}", "title": step, "objective": step})
        elif isinstance(step, dict):
            normalized.append(step)
        else:
            raise SystemExit(f"Invalid step at index {index}: expected string or object.")
    return normalized


def compact(value: Any, fallback: str = "Not specified.") -> str:
    if value is None:
        return fallback
    if isinstance(value, list):
        return "\n".join(f"- {item}" for item in value) if value else fallback
    if isinstance(value, dict):
        return "\n".join(f"- {key}: {val}" for key, val in value.items()) if value else fallback
    text = str(value).strip()
    return text if text else fallback


def truncate(text: str, limit: int) -> str:
    text = text.strip()
    if len(text) <= limit:
        return text
    return text[: limit - 80].rstrip() + "\n\n[truncated by prompt_loop_runner]"


def render_next_prompt(workflow: dict[str, Any], state: dict[str, Any], max_chars: int) -> str:
    steps = step_list(workflow)
    current_index = int(state.get("current_step", 0))
    if current_index >= len(steps):
        return dedent(
            f"""
            Workflow `{workflow.get('name', 'workflow')}` is complete.

            Produce a final concise summary:
            1. What was completed.
            2. Evidence that the result satisfies the goal.
            3. Any residual risks or follow-up actions.
            """
        ).strip() + "\n"

    current = steps[current_index]
    previous = steps[current_index - 1] if current_index > 0 else None
    last_output = truncate(state.get("last_output", ""), max_chars)
    last_review = truncate(state.get("last_review", ""), max_chars // 2)

    review_block = "No previous step. Start by checking the goal and assumptions."
    if previous:
        review_block = "\n".join(
            [
                "Review the previous step before doing new work.",
                f"Previous step: {previous.get('id', current_index)} - {previous.get('title', previous.get('objective', 'Untitled'))}",
                "Previous acceptance criteria:",
                compact(previous.get("acceptance")),
                "",
                "Previous output:",
                last_output or "No previous output was recorded.",
                "",
                "Prior review notes:",
                last_review or "No prior review notes were recorded.",
                "",
                "Decide whether the previous output is OK, partially OK, or needs revision. If it needs revision, fix the issue before advancing.",
            ]
        )

    prompt_lines = [
        "You are executing a multi-step workflow from a compact controller prompt.",
        "",
        f"Workflow: {workflow.get('name', 'workflow')}",
        "Goal:",
        compact(workflow.get("goal")),
        "",
        "Stable constraints:",
        compact(workflow.get("constraints")),
        "",
        "Self-review gate:",
        review_block,
        "",
        f"Current step: {current.get('id', f'step-{current_index + 1}')} - {current.get('title', current.get('objective', 'Untitled'))}",
        "Objective:",
        compact(current.get("objective")),
        "",
        "Instructions:",
        compact(current.get("prompt") or current.get("instructions")),
        "",
        "Acceptance criteria:",
        compact(current.get("acceptance")),
        "",
        "Output format:",
        "1. Previous-step review: OK / partially OK / needs revision, with brief evidence.",
        "2. Work performed for the current step.",
        "3. Result or artifact.",
        "4. Suggested status for this step: ok / needs_revision / blocked.",
        "5. If blocked, name the exact missing input.",
    ]
    return "\n".join(prompt_lines).strip() + "\n"


def cmd_init(args: argparse.Namespace) -> int:
    workflow = load_json(Path(args.workflow))
    state_path = Path(args.state)
    if state_path.exists() and not args.force:
        raise SystemExit(f"State already exists: {state_path}. Use --force to overwrite.")
    write_json(state_path, default_state(workflow))
    print(f"Initialized state: {state_path}")
    return 0


def cmd_next(args: argparse.Namespace) -> int:
    workflow = load_json(Path(args.workflow))
    state = load_json(Path(args.state))
    prompt = render_next_prompt(workflow, state, args.max_chars)
    if args.out:
        Path(args.out).write_text(prompt, encoding="utf-8")
        print(f"Wrote prompt: {args.out}")
    else:
        print(prompt, end="")
    return 0


def read_optional_text(path: str | None) -> str:
    if not path:
        return ""
    return Path(path).read_text(encoding="utf-8-sig")


def cmd_record(args: argparse.Namespace) -> int:
    state_path = Path(args.state)
    state = load_json(state_path)
    output = read_optional_text(args.output)
    review = read_optional_text(args.review)
    status = args.status
    current_step = int(state.get("current_step", 0))

    state.setdefault("history", []).append(
        {
            "step": current_step,
            "status": status,
            "output": output,
            "review": review,
            "recorded_at": now_iso(),
        }
    )
    state["last_output"] = output
    state["last_review"] = review
    if status == "ok":
        state["current_step"] = current_step + 1
    elif status == "blocked":
        state["status"] = "blocked"
    else:
        state["status"] = "active"
    state["updated_at"] = now_iso()
    write_json(state_path, state)
    print(f"Recorded {status} for step {current_step}. Current step: {state.get('current_step')}")
    return 0


def cmd_sample(args: argparse.Namespace) -> int:
    sample = {
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
    text = json.dumps(sample, indent=2, ensure_ascii=False) + "\n"
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"Wrote sample workflow: {args.out}")
    else:
        print(text, end="")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init", help="Initialize state for a workflow JSON file.")
    init.add_argument("--workflow", required=True)
    init.add_argument("--state", required=True)
    init.add_argument("--force", action="store_true")
    init.set_defaults(func=cmd_init)

    next_cmd = sub.add_parser("next", help="Emit the next compact agent prompt.")
    next_cmd.add_argument("--workflow", required=True)
    next_cmd.add_argument("--state", required=True)
    next_cmd.add_argument("--out")
    next_cmd.add_argument("--max-chars", type=int, default=6000)
    next_cmd.set_defaults(func=cmd_next)

    record = sub.add_parser("record", help="Record an agent result and advance or retry.")
    record.add_argument("--state", required=True)
    record.add_argument("--status", choices=["ok", "needs_revision", "blocked"], required=True)
    record.add_argument("--output", help="Path to the previous agent output text.")
    record.add_argument("--review", help="Path to review notes text.")
    record.set_defaults(func=cmd_record)

    sample = sub.add_parser("sample", help="Print or write a sample workflow JSON.")
    sample.add_argument("--out")
    sample.set_defaults(func=cmd_sample)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
