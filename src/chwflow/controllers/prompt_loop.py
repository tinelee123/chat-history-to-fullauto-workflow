"""PromptLoopController — self-reviewing multi-turn agent workflow.

The original pattern from the project: store state in JSON, emit compact
next prompts with self-review gates, record results, advance/retry/block.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from chwflow.prompts import render_next_prompt
from chwflow.state import StateMachine


class PromptLoopController:
    """Orchestrates a prompt-loop workflow across multiple turns.

    This is the CLASSICAL pattern — emit a prompt, receive output, review,
    advance or retry. Now backed by Pydantic models and StateMachine.
    """

    def __init__(self, workflow: dict[str, Any], state_path: str | Path) -> None:
        self.workflow = workflow
        self.state_path = Path(state_path)

    @classmethod
    def from_files(cls, workflow_path: str, state_path: str) -> PromptLoopController:
        import json

        wf = json.loads(Path(workflow_path).read_text(encoding="utf-8-sig"))
        return cls(wf, state_path)

    @property
    def state(self) -> StateMachine:
        if self.state_path.exists():
            return StateMachine.from_file(self.state_path)
        return StateMachine(self.workflow)

    def init(self, force: bool = False) -> None:
        sm = StateMachine(self.workflow)
        sm.save(self.state_path)

    def next_prompt(self, max_chars: int = 6000) -> str:
        sm = self.state
        return render_next_prompt(self.workflow, sm.to_dict(), max_chars)

    def record(self, status: str, output: str = "", review: str = "") -> None:
        sm = self.state
        steps: list[dict[str, Any]] = self.workflow.get("steps", [])
        current = sm.current_step
        step_id = (
            steps[current].get("id", f"step-{current + 1}") if current < len(steps) else "complete"
        )
        sm.record(current, step_id, status, output, review)
        sm.save(self.state_path)

    def is_complete(self) -> bool:
        sm = self.state
        return sm.is_complete(len(self.workflow.get("steps", [])))

    def is_blocked(self) -> bool:
        return self.state.status == "blocked"
