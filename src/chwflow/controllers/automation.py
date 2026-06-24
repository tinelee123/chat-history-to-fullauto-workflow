"""AutomationController — execute deterministic shell/script/Python steps sequentially."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from chwflow.engine import StepResult, WorkflowEngine
from chwflow.state import StateMachine


class AutomationController:
    """Execute a workflow as a deterministic automation pipeline.

    Supports shell commands, inline Python, and file checks. No LLM calls.
    Can run in dry-run mode for preview.
    """

    def __init__(
        self,
        workflow: dict[str, Any],
        workdir: str | None = None,
        state_path: str | None = None,
    ) -> None:
        self.workflow = workflow
        self.engine = WorkflowEngine(workflow, workdir)
        self.state_path = Path(state_path) if state_path else None
        self.state: StateMachine | None = None

    @classmethod
    def from_files(
        cls,
        workflow_path: str,
        workdir: str | None = None,
        state_path: str | None = None,
    ) -> AutomationController:
        import json

        wf = json.loads(Path(workflow_path).read_text(encoding="utf-8-sig"))
        return cls(wf, workdir, state_path)

    def execute(self, dry_run: bool = False) -> list[StepResult]:
        if self.state_path and self.state_path.exists():
            self.state = StateMachine.from_file(self.state_path)

        results = self.engine.execute(dry_run=dry_run)

        if self.state:
            for r in results:
                self.state.record(
                    self.state.current_step,
                    r.step_id,
                    r.status,
                    r.output,
                    r.error,
                )
            self.state.save(self.state_path)

        return results

    def succeeded(self) -> bool:
        return all(r.ok for r in self.engine.results)

    def summary(self) -> str:
        parts: list[str] = []
        for r in self.engine.results:
            icon = "✓" if r.ok else "✗"
            parts.append(f"  {icon} {r.step_id}: {r.output[:80]}")
        return "\n".join(parts)
