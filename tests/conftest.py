"""shared pytest fixtures for chwflow tests."""

import json
import tempfile
from pathlib import Path
from typing import Any

import pytest


@pytest.fixture
def sample_workflow() -> dict[str, Any]:
    return {
        "name": "test-workflow",
        "goal": "Verify the test infrastructure works correctly.",
        "constraints": ["No side effects.", "Exit cleanly."],
        "steps": [
            {
                "id": "init",
                "title": "Initialize",
                "objective": "Set up the test environment.",
                "acceptance": ["Environment is ready"],
            },
            {
                "id": "run",
                "title": "Execute",
                "objective": "Do the main work.",
                "acceptance": ["Result is produced"],
            },
            {
                "id": "verify",
                "title": "Verify",
                "objective": "Check the output.",
                "acceptance": ["Output passes assertions"],
            },
        ],
    }


@pytest.fixture
def complex_workflow() -> dict[str, Any]:
    return {
        "name": "complex-test",
        "goal": "Test branching and dependencies.",
        "constraints": ["Must handle parallel branches."],
        "steps": [
            {"id": "setup", "title": "Setup", "acceptance": ["Ready"]},
            {
                "id": "branch-a",
                "title": "Branch A",
                "depends_on": ["setup"],
                "acceptance": ["Done"],
            },
            {
                "id": "branch-b",
                "title": "Branch B",
                "depends_on": ["setup"],
                "acceptance": ["Done"],
            },
            {
                "id": "merge",
                "title": "Merge results",
                "depends_on": ["branch-a", "branch-b"],
                "acceptance": ["Merged"],
            },
        ],
    }


@pytest.fixture
def tmp_workflow_file(sample_workflow: dict[str, Any]) -> Path:
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(sample_workflow, f)
        return Path(f.name)


@pytest.fixture
def tmp_state_file() -> Path:
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        f.write("{}")
        return Path(f.name)
