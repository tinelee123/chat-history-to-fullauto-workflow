"""CLI integration tests via Typer test runner."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from typer.testing import CliRunner

from chwflow.cli import app

runner = CliRunner()


class TestSample:
    def test_sample_stdout(self) -> None:
        result = runner.invoke(app, ["sample"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["name"] == "example-agent-workflow"
        assert len(data["steps"]) == 3

    def test_sample_to_file(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = Path(f.name)

        result = runner.invoke(app, ["sample", "--out", str(path)])
        assert result.exit_code == 0
        assert path.exists()
        data = json.loads(path.read_text())
        assert data["name"] == "example-agent-workflow"


class TestInit:
    def test_init_creates_state(self) -> None:
        with (
            tempfile.NamedTemporaryFile(suffix=".json", delete=False) as wf,
            tempfile.NamedTemporaryFile(suffix=".json", delete=False) as st,
        ):
            wf_path = Path(wf.name)
            st_path = Path(st.name)
            json.dump(
                {
                    "name": "cli-test",
                    "steps": [{"id": "a", "title": "A"}],
                },
                open(wf_path, "w"),
            )
            # Remove the state file first so init won't complain
            st_path.unlink(missing_ok=True)

        result = runner.invoke(
            app,
            [
                "init",
                "--workflow",
                str(wf_path),
                "--state",
                str(st_path),
            ],
        )
        assert result.exit_code == 0
        data = json.loads(st_path.read_text())
        assert data["workflow_name"] == "cli-test"
        assert data["current_step"] == 0

    def test_init_duplicate_requires_force(self) -> None:
        with (
            tempfile.NamedTemporaryFile(suffix=".json", delete=False) as wf,
            tempfile.NamedTemporaryFile(suffix=".json", delete=False) as st,
        ):
            wf_path = Path(wf.name)
            st_path = Path(st.name)
            json.dump(
                {
                    "name": "dup-test",
                    "steps": [{"id": "a", "title": "A"}],
                },
                open(wf_path, "w"),
            )

        runner.invoke(app, ["init", "--workflow", str(wf_path), "--state", str(st_path)])
        result = runner.invoke(app, ["init", "--workflow", str(wf_path), "--state", str(st_path)])
        assert result.exit_code != 0  # Fails without --force

        result2 = runner.invoke(
            app,
            [
                "init",
                "--workflow",
                str(wf_path),
                "--state",
                str(st_path),
                "--force",
            ],
        )
        assert result2.exit_code == 0


class TestNext:
    def test_next_generates_prompt(self) -> None:
        with (
            tempfile.NamedTemporaryFile(suffix=".json", delete=False) as wf,
            tempfile.NamedTemporaryFile(suffix=".json", delete=False) as st,
        ):
            wf_path = Path(wf.name)
            st_path = Path(st.name)
            json.dump(
                {
                    "name": "prompt-test",
                    "steps": [{"id": "s1", "title": "Step 1", "objective": "Do it"}],
                },
                open(wf_path, "w"),
            )
            # Create a valid state file
            state_data = {
                "workflow_name": "prompt-test",
                "current_step": 0,
                "status": "active",
                "history": [],
            }
            json.dump(state_data, open(st_path, "w"))

        result = runner.invoke(
            app,
            [
                "next",
                "--workflow",
                str(wf_path),
                "--state",
                str(st_path),
            ],
        )
        assert result.exit_code == 0
        assert "Step 1" in result.stdout
        assert "Self-review gate" in result.stdout

    def test_next_to_file(self) -> None:
        with (
            tempfile.NamedTemporaryFile(suffix=".json", delete=False) as wf,
            tempfile.NamedTemporaryFile(suffix=".json", delete=False) as st,
            tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as out,
        ):
            wf_path = Path(wf.name)
            st_path = Path(st.name)
            out_path = Path(out.name)
            json.dump(
                {
                    "name": "file-test",
                    "steps": [{"id": "s1", "title": "Step 1", "objective": "Do it"}],
                },
                open(wf_path, "w"),
            )
            state_data = {
                "workflow_name": "file-test",
                "current_step": 0,
                "status": "active",
                "history": [],
            }
            json.dump(state_data, open(st_path, "w"))

        result = runner.invoke(
            app,
            [
                "next",
                "--workflow",
                str(wf_path),
                "--state",
                str(st_path),
                "--out",
                str(out_path),
            ],
        )
        assert result.exit_code == 0
        content = out_path.read_text()
        assert "Step 1" in content


class TestRecord:
    def test_record_ok(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as st:
            st_path = Path(st.name)
            state_data = {
                "workflow_name": "rec-test",
                "current_step": 0,
                "status": "active",
                "history": [],
                "steps": [{"id": "s1", "title": "S1"}],
            }
            json.dump(state_data, open(st_path, "w"))

        result = runner.invoke(
            app,
            [
                "record",
                "--state",
                str(st_path),
                "--status",
                "ok",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(st_path.read_text())
        assert data["current_step"] == 1


class TestStatus:
    def test_status_shows_table(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as st:
            st_path = Path(st.name)
            state_data = {
                "workflow_name": "status-test",
                "current_step": 2,
                "status": "active",
                "history": [{"step": 0, "status": "ok"}],
                "updated_at": "2026-01-01T00:00:00Z",
            }
            json.dump(state_data, open(st_path, "w"))

        result = runner.invoke(app, ["status", "--state", str(st_path)])
        assert result.exit_code == 0


class TestVersion:
    def test_version(self) -> None:
        result = runner.invoke(app, ["version"])
        assert result.exit_code == 0
        assert "0.2.0" in result.stdout


class TestRun:
    def test_run_dry(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as wf:
            wf_path = Path(wf.name)
            json.dump(
                {
                    "name": "dry",
                    "steps": [{"id": "e", "title": "Echo", "action": "echo hi"}],
                },
                open(wf_path, "w"),
            )

        result = runner.invoke(app, ["run", "--workflow", str(wf_path), "--dry-run"])
        assert result.exit_code == 0
        assert "Would execute" in result.stdout
