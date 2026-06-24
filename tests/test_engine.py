"""WorkflowEngine tests."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from chwflow.engine import StepResult, WorkflowEngine


@pytest.fixture
def shell_workflow() -> dict[str, Any]:
    return {
        "name": "shell-test",
        "steps": [
            {
                "id": "echo",
                "title": "Echo",
                "action": "echo hello world",
            },
            {
                "id": "list",
                "title": "List",
                "action": "ls -la",
            },
        ],
    }


@pytest.fixture
def file_check_workflow(tmp_path: Path) -> dict[str, Any]:
    f = tmp_path / "exists.txt"
    f.write_text("hello")
    return {
        "name": "file-test",
        "steps": [
            {"id": "check-exists", "title": "Check", "action": {"check_file": str(f)}},
            {
                "id": "check-missing",
                "title": "Missing",
                "action": {"check_file": str(tmp_path / "nope.txt")},
            },
        ],
    }


class TestWorkflowEngine:
    def test_shell_command(self, shell_workflow: dict[str, Any]) -> None:
        engine = WorkflowEngine(shell_workflow)
        results = engine.execute()
        assert results[0].ok
        assert "hello world" in results[0].output

    def test_shell_failure(self) -> None:
        wf = {"name": "fail", "steps": [{"id": "f", "title": "F", "action": "exit 1"}]}
        engine = WorkflowEngine(wf)
        results = engine.execute()
        assert not results[0].ok
        assert "Exit 1" in results[0].error

    def test_dry_run(self, shell_workflow: dict[str, Any]) -> None:
        engine = WorkflowEngine(shell_workflow)
        results = engine.execute(dry_run=True)
        assert results[0].ok
        assert "Would execute" in results[0].output

    def test_no_action_skipped(self) -> None:
        wf = {"name": "skip", "steps": [{"id": "s", "title": "S"}]}
        engine = WorkflowEngine(wf)
        results = engine.execute()
        assert results[0].ok
        assert "skipped" in results[0].output

    def test_python_action(self) -> None:
        wf = {
            "name": "py-test",
            "steps": [{"id": "py", "title": "Py", "action": {"python": "result = 2 + 3"}}],
        }
        engine = WorkflowEngine(wf)
        results = engine.execute()
        assert results[0].ok
        assert "5" in results[0].output

    def test_python_error(self) -> None:
        wf = {
            "name": "py-err",
            "steps": [
                {"id": "py", "title": "Py", "action": {"python": "raise ValueError('boom')"}}
            ],
        }
        engine = WorkflowEngine(wf)
        results = engine.execute()
        assert not results[0].ok
        assert "boom" in results[0].error

    def test_file_check_exists(self, file_check_workflow: dict[str, Any]) -> None:
        engine = WorkflowEngine(file_check_workflow)
        results = engine.execute()
        assert results[0].ok
        assert "File exists" in results[0].output

    def test_file_check_missing(self, file_check_workflow: dict[str, Any]) -> None:
        engine = WorkflowEngine(file_check_workflow)
        results = engine.execute()
        assert not results[1].ok
        assert "File not found" in results[1].error

    def test_stops_on_failure(self) -> None:
        wf = {
            "name": "stop-test",
            "steps": [
                {"id": "fail", "title": "Fail", "action": "exit 1"},
                {"id": "never", "title": "Never", "action": "echo unreachable"},
            ],
        }
        engine = WorkflowEngine(wf)
        results = engine.execute()
        assert len(results) == 1

    def test_step_result_properties(self) -> None:
        r = StepResult("test", "ok", "hello", "")
        assert r.ok
        assert r.step_id == "test"
        assert r.output == "hello"

    def test_step_result_not_ok(self) -> None:
        r = StepResult("test", "needs_revision", "", "error")
        assert not r.ok
        assert r.error == "error"
