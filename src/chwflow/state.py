"""StateMachine — load/save/advance/branch/rollback workflow state."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from chwflow.models import HistoryEntry, ReviewStatus, now_iso


class StateMachine:
    """Mutable runtime state for a workflow execution.

    Persisted as JSON. Supports linear, branch, and parallel step execution.
    """

    def __init__(self, workflow: dict[str, Any]) -> None:
        self._data: dict[str, Any] = {
            "workflow_name": workflow.get("name", "workflow"),
            "version": workflow.get("version", 1),
            "current_step": 0,
            "status": "active",
            "history": [],
            "branches": {},
            "updated_at": now_iso(),
        }

    @classmethod
    def from_file(cls, path: str | Path) -> StateMachine:
        sm = cls.__new__(cls)
        raw = json.loads(Path(path).read_text(encoding="utf-8-sig"))
        sm._data = raw
        sm._ensure_compat()
        return sm

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StateMachine:
        sm = cls.__new__(cls)
        sm._data = data
        sm._ensure_compat()
        return sm

    def _ensure_compat(self) -> None:
        self._data.setdefault("branches", {})
        self._data.setdefault("version", 1)

    def save(self, path: str | Path) -> None:
        self._data["updated_at"] = now_iso()
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(
            json.dumps(self._data, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    def to_dict(self) -> dict[str, Any]:
        return self._data

    @property
    def current_step(self) -> int:
        return int(self._data.get("current_step", 0))

    @property
    def status(self) -> str:
        return str(self._data.get("status", "active"))

    @property
    def history(self) -> list[dict[str, Any]]:
        return list(self._data.get("history", []))

    @property
    def branches(self) -> dict[str, Any]:
        return dict(self._data.get("branches", {}))

    def advance(self) -> None:
        self._data["current_step"] = self.current_step + 1
        self._data["status"] = "active"

    def retry(self) -> None:
        self._data["status"] = "active"

    def block(self) -> None:
        self._data["status"] = "blocked"

    def complete(self) -> None:
        self._data["status"] = "complete"

    def fail(self) -> None:
        self._data["status"] = "failed"

    def rollback(self, target_step: int) -> None:
        """Roll back to a specific step, removing history entries after it."""
        if target_step < 0:
            raise ValueError(f"target_step must be >= 0, got {target_step}")
        self._data["current_step"] = target_step
        self._data["status"] = "active"
        self._data["history"] = [h for h in self.history if int(h.get("step", -1)) < target_step]

    def is_complete(self, total_steps: int) -> bool:
        return self.current_step >= total_steps

    def start_branch(self, branch_id: str, steps: list[int]) -> None:
        self._data.setdefault("branches", {})[branch_id] = {
            "name": branch_id,
            "steps": steps,
            "current": 0,
            "status": "running",
        }

    def advance_branch(self, branch_id: str) -> None:
        branch = self._data["branches"].get(branch_id)
        if branch:
            branch["current"] += 1
            if branch["current"] >= len(branch["steps"]):
                branch["status"] = "done"

    def branch_completed(self, branch_id: str) -> bool:
        return self._data.get("branches", {}).get(branch_id, {}).get("status") == "done"

    def all_branches_done(self) -> bool:
        branches = self._data.get("branches", {})
        if not branches:
            return True
        return all(b.get("status") == "done" for b in branches.values())

    def record(
        self,
        step_index: int,
        step_id: str,
        status: str,
        output: str = "",
        review: str = "",
    ) -> None:
        entry = HistoryEntry(
            step=step_index,
            step_id=step_id,
            status=ReviewStatus(status),
            output=output,
            review=review,
        )
        self._data.setdefault("history", []).append(entry.model_dump())

        if status == "ok":
            self.advance()
        elif status == "blocked":
            self.block()
        else:
            self.retry()

        self._data["updated_at"] = now_iso()

    def last_entry(self) -> dict[str, Any] | None:
        h = self.history
        return h[-1] if h else None
