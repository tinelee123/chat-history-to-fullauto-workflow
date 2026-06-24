"""WorkflowEngine — deterministic step execution for automation runner pattern."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any


class StepResult:
    def __init__(self, step_id: str, status: str, output: str, error: str = "") -> None:
        self.step_id = step_id
        self.status = status
        self.output = output.strip()
        self.error = error.strip()

    @property
    def ok(self) -> bool:
        return self.status == "ok"


class WorkflowEngine:
    """Executes deterministic workflow steps: shell commands, Python expressions, file checks."""

    def __init__(self, workflow: dict[str, Any], workdir: str | None = None) -> None:
        self.workflow = workflow
        self.workdir = Path(workdir) if workdir else Path.cwd()
        self.results: list[StepResult] = []

    def execute(self, dry_run: bool = False) -> list[StepResult]:
        """Execute all steps sequentially. Returns list of StepResult."""
        steps: list[dict[str, Any]] = self.workflow.get("steps", [])
        self.results = []

        for step in steps:
            result = self._execute_step(step, dry_run)
            self.results.append(result)
            if not result.ok:
                break

        return self.results

    def _execute_step(self, step: dict[str, Any], dry_run: bool) -> StepResult:
        sid = step.get("id", "unknown")
        action = step.get("action") or step.get("run")

        if dry_run:
            return StepResult(sid, "ok", f"[dry-run] Would execute: {action or 'no action'}")

        if action is None:
            return StepResult(sid, "ok", "No action specified — skipped")

        if isinstance(action, str):
            return self._run_shell(sid, action)

        if isinstance(action, dict):
            if "shell" in action:
                return self._run_shell(sid, str(action["shell"]))
            if "python" in action:
                return self._run_python(sid, str(action["python"]))
            if "check_file" in action:
                return self._check_file(sid, str(action["check_file"]))
            return StepResult(sid, "needs_revision", f"Unknown action type: {json.dumps(action)}")

        return StepResult(
            sid, "needs_revision", f"Unsupported action type: {type(action).__name__}"
        )

    def _run_shell(self, sid: str, cmd: str) -> StepResult:
        try:
            proc = subprocess.run(
                cmd,
                shell=True,
                cwd=str(self.workdir),
                capture_output=True,
                text=True,
                timeout=300,
            )
            output = proc.stdout.strip()
            error = proc.stderr.strip()
            if proc.returncode == 0:
                return StepResult(sid, "ok", output, error)
            return StepResult(sid, "needs_revision", output, f"Exit {proc.returncode}: {error}")
        except subprocess.TimeoutExpired as e:
            return StepResult(sid, "needs_revision", "", f"Timeout: {e}")
        except OSError as e:
            return StepResult(sid, "needs_revision", "", f"OS error: {e}")

    def _run_python(self, sid: str, code: str) -> StepResult:
        try:
            local_ns: dict[str, Any] = {}
            exec(code, {"__builtins__": __builtins__}, local_ns)
            output = str(local_ns.get("result", "Python executed successfully."))
            return StepResult(sid, "ok", output)
        except Exception as e:
            return StepResult(sid, "needs_revision", "", f"Python error: {e}")

    def _check_file(self, sid: str, path_str: str) -> StepResult:
        p = self.workdir / path_str
        if p.exists():
            stat = p.stat()
            return StepResult(sid, "ok", f"File exists: {p} ({stat.st_size} bytes)")
        return StepResult(sid, "needs_revision", "", f"File not found: {p}")
