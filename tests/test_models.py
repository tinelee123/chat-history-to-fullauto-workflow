"""Pydantic model validation tests."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from chwflow.models import Step, Workflow


class TestStep:
    def test_valid_step(self) -> None:
        s = Step(id="init", title="Initialize", objective="Set up")
        assert s.id == "init"
        assert s.title == "Initialize"

    def test_empty_id_raises(self) -> None:
        with pytest.raises(ValidationError):
            Step(id="  ", title="Bad")

    def test_default_objective(self) -> None:
        s = Step(id="a", title="A")
        assert s.objective == ""

    def test_acceptance_list(self) -> None:
        s = Step(id="a", title="A", acceptance=["Check 1", "Check 2"])
        assert len(s.acceptance) == 2

    def test_depends_on_defaults(self) -> None:
        s = Step(id="a", title="A")
        assert s.depends_on == []

    def test_extra_fields_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            Step(id="a", title="A", unknown_field="nope")


class TestWorkflow:
    def test_valid_workflow(self, sample_workflow: dict) -> None:
        wf = Workflow.model_validate(sample_workflow)
        assert wf.name == "test-workflow"
        assert len(wf.steps) == 3

    def test_empty_steps_raises(self) -> None:
        with pytest.raises(ValidationError, match="at least one step"):
            Workflow(steps=[])

    def test_duplicate_step_ids_raises(self) -> None:
        with pytest.raises(ValidationError, match="Duplicate step id"):
            Workflow(
                steps=[
                    Step(id="same", title="A"),
                    Step(id="same", title="B"),
                ]
            )

    def test_depends_on_unknown_step_raises(self) -> None:
        with pytest.raises(ValidationError, match="unknown step"):
            Workflow(steps=[Step(id="a", title="A", depends_on=["nonexistent"])])

    def test_method_validates_from_json(self, tmp_workflow_file) -> None:
        import json

        data = json.loads(tmp_workflow_file.read_text())
        wf = Workflow.model_validate(data)
        assert wf.name == "test-workflow"

    def test_defaults(self) -> None:
        wf = Workflow(steps=[Step(id="one", title="One")])
        assert wf.name == "workflow"
        assert wf.goal == ""
        assert wf.constraints == []

    def test_missing_steps_field_raises(self) -> None:
        with pytest.raises(ValidationError):
            Workflow.model_validate({"name": "no-steps"})


class TestReviewStatus:
    def test_valid_statuses(self) -> None:
        from chwflow.models import ReviewStatus

        assert ReviewStatus.OK.value == "ok"
        assert ReviewStatus.NEEDS_REVISION.value == "needs_revision"
        assert ReviewStatus.BLOCKED.value == "blocked"
