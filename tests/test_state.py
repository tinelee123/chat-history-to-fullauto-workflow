"""StateMachine unit tests."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

import pytest

from chwflow.state import StateMachine


@pytest.fixture
def sm(sample_workflow: dict[str, Any]) -> StateMachine:
    return StateMachine(sample_workflow)


class TestStateMachineInit:
    def test_initial_state(self, sm: StateMachine) -> None:
        assert sm.current_step == 0
        assert sm.status == "active"
        assert sm.history == []

    def test_workflow_name(self, sm: StateMachine) -> None:
        assert sm.to_dict()["workflow_name"] == "test-workflow"


class TestStateMachineAdvance:
    def test_advance(self, sm: StateMachine) -> None:
        sm.advance()
        assert sm.current_step == 1

    def test_record_ok_advances(self, sm: StateMachine) -> None:
        sm.record(0, "init", "ok", "done", "")
        assert sm.current_step == 1
        assert len(sm.history) == 1

    def test_record_needs_revision_stays(self, sm: StateMachine) -> None:
        sm.record(0, "init", "needs_revision", "incomplete", "redo")
        assert sm.current_step == 0
        assert sm.status == "active"

    def test_record_blocked(self, sm: StateMachine) -> None:
        sm.record(0, "init", "blocked", "", "missing input")
        assert sm.status == "blocked"

    def test_record_preserves_output(self, sm: StateMachine) -> None:
        sm.record(0, "init", "ok", "result text", "review text")
        entry = sm.last_entry()
        assert entry is not None
        assert entry["output"] == "result text"
        assert entry["review"] == "review text"


class TestStateMachineFileIO:
    def test_save_and_load(self, sm: StateMachine, sample_workflow: dict[str, Any]) -> None:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            path = Path(f.name)

        sm.record(0, "init", "ok", "out", "rev")
        sm.save(path)

        loaded = StateMachine.from_file(path)
        assert loaded.current_step == 1
        assert loaded.history[0]["output"] == "out"

    def test_from_dict(self) -> None:
        data = {
            "workflow_name": "dict-test",
            "current_step": 3,
            "status": "complete",
            "history": [],
        }
        sm = StateMachine.from_dict(data)
        assert sm.to_dict()["workflow_name"] == "dict-test"
        assert sm.current_step == 3


class TestStateMachineRollback:
    def test_rollback_resets_step(self, sm: StateMachine) -> None:
        sm.record(0, "init", "ok")
        sm.record(1, "run", "ok")
        assert sm.current_step == 2

        sm.rollback(0)
        assert sm.current_step == 0
        assert sm.status == "active"

    def test_rollback_clears_history(self, sm: StateMachine) -> None:
        sm.record(0, "init", "ok")
        sm.record(1, "run", "ok")
        sm.record(2, "verify", "ok")
        sm.rollback(1)
        assert len(sm.history) == 1
        assert sm.history[0]["step"] == 0

    def test_rollback_negative_raises(self, sm: StateMachine) -> None:
        with pytest.raises(ValueError, match="must be >= 0"):
            sm.rollback(-1)


class TestStateMachineComplete:
    def test_is_complete(self, sm: StateMachine) -> None:
        assert not sm.is_complete(3)
        sm.advance()
        sm.advance()
        sm.advance()
        assert sm.is_complete(3)

    def test_complete_method(self, sm: StateMachine) -> None:
        sm.complete()
        assert sm.status == "complete"

    def test_fail_method(self, sm: StateMachine) -> None:
        sm.fail()
        assert sm.status == "failed"


class TestStateMachineBranch:
    def test_start_branch(self, sm: StateMachine) -> None:
        sm.start_branch("b1", [2, 3, 4])
        assert "b1" in sm.branches
        assert sm.branches["b1"]["status"] == "running"

    def test_advance_branch(self, sm: StateMachine) -> None:
        sm.start_branch("b1", [2, 3])
        sm.advance_branch("b1")
        sm.advance_branch("b1")
        assert sm.branch_completed("b1")

    def test_all_branches_done_empty(self, sm: StateMachine) -> None:
        assert sm.all_branches_done()

    def test_all_branches_done_with_branches(self, sm: StateMachine) -> None:
        sm.start_branch("b1", [1])
        sm.start_branch("b2", [1])
        assert not sm.all_branches_done()
        sm.advance_branch("b1")
        sm.advance_branch("b2")
        assert sm.all_branches_done()
