"""Pydantic v2 models for workflow definitions, state, and history."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Any, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)


class ReviewStatus(StrEnum):
    OK = "ok"
    NEEDS_REVISION = "needs_revision"
    BLOCKED = "blocked"


class WorkflowStatus(StrEnum):
    ACTIVE = "active"
    COMPLETE = "complete"
    BLOCKED = "blocked"
    FAILED = "failed"


class Step(BaseModel):
    """A single step in a workflow."""

    model_config = ConfigDict(extra="forbid")

    id: str
    title: str
    objective: str = ""
    prompt: str | None = None
    instructions: str | None = None
    acceptance: list[str] = Field(default_factory=list)
    depends_on: list[str] = Field(default_factory=list)

    @field_validator("id")
    @classmethod
    def id_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Step id must not be empty")
        return v.strip()


class Constraint(BaseModel):
    """A single constraint in a workflow."""

    model_config = ConfigDict(extra="forbid")
    text: str


class Workflow(BaseModel):
    """Immutable workflow definition loaded from JSON."""

    model_config = ConfigDict(extra="forbid")

    name: str = "workflow"
    version: int = 1
    goal: str = ""
    constraints: list[str] = Field(default_factory=list)
    steps: list[Step]

    @field_validator("steps")
    @classmethod
    def steps_not_empty(cls, v: list[Step]) -> list[Step]:
        if not v:
            raise ValueError("Workflow must contain at least one step")
        return v

    @field_validator("steps")
    @classmethod
    def unique_ids(cls, v: list[Step]) -> list[Step]:
        seen: set[str] = set()
        for step in v:
            if step.id in seen:
                raise ValueError(f"Duplicate step id: {step.id}")
            seen.add(step.id)
        return v

    @model_validator(mode="after")
    def depends_on_exist(self) -> Workflow:
        ids = {s.id for s in self.steps}
        for step in self.steps:
            for dep in step.depends_on:
                if dep not in ids:
                    raise ValueError(f"Step '{step.id}' depends on unknown step '{dep}'")
        return self


class HistoryEntry(BaseModel):
    """One recorded step result in workflow execution history."""

    model_config = ConfigDict(extra="forbid")

    step: int
    step_id: str
    status: ReviewStatus
    output: str = ""
    review: str = ""
    recorded_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


StateType = Literal["linear", "branch"]
BranchStatus = Literal["waiting", "running", "done", "failed"]
StepSource = Step | str
WorkflowSource = Workflow | dict[str, Any]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
