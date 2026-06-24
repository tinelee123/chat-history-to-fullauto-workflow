"""HybridController — alternating script execution and human/agent review checkpoints."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from chwflow.engine import StepResult, WorkflowEngine
from chwflow.state import StateMachine


class HybridCheckpoint:
    """A checkpoint in a hybrid workflow where human/agent review is required."""

    def __init__(
        self,
        step_id: str,
        title: str,
        objective: str,
        acceptance: list[str],
    ) -> None:
        self.step_id = step_id
        self.title = title
        self.objective = objective
        self.acceptance = acceptance
        self.output: str = ""
        self.status: str = "pending"

    def approve(self) -> None:
        self.status = "ok"

    def reject(self, reason: str = "") -> None:
        self.status = "needs_revision"
        self.output = reason


class HybridController:
    """Mix of automated script steps and human/agent review checkpoints.

    Steps where `review_required: true` pause for manual/agent approval before continuing.
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
        self.checkpoints: list[HybridCheckpoint] = []
        self._pending: HybridCheckpoint | None = None

    @classmethod
    def from_files(
        cls,
        workflow_path: str,
        workdir: str | None = None,
        state_path: str | None = None,
    ) -> HybridController:
        import json

        wf = json.loads(Path(workflow_path).read_text(encoding="utf-8-sig"))
        return cls(wf, workdir, state_path)

    def run_automated(self, dry_run: bool = False) -> list[StepResult]:
        """Execute all non-review steps up to the next checkpoint."""
        steps: list[dict[str, Any]] = self.workflow.get("steps", [])
        results: list[StepResult] = []

        self._pending = None

        for step in steps:
            if step.get("review_required"):
                self._pending = HybridCheckpoint(
                    step_id=step.get("id", ""),
                    title=step.get("title", ""),
                    objective=step.get("objective", ""),
                    acceptance=step.get("acceptance", []),
                )
                self.checkpoints.append(self._pending)
                return results

            result = self.engine._execute_step(step, dry_run)
            results.append(result)
            if not result.ok:
                return results

        return results

    @property
    def pending_checkpoint(self) -> HybridCheckpoint | None:
        return self._pending

    def approve_checkpoint(self, review_notes: str = "") -> None:
        if self._pending is None:
            raise RuntimeError("No pending checkpoint to approve")
        self._pending.approve()
        self._pending.output = review_notes

    def reject_checkpoint(self, reason: str) -> None:
        if self._pending is None:
            raise RuntimeError("No pending checkpoint to reject")
        self._pending.reject(reason)
