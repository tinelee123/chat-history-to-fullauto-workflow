"""Controller integration tests."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

from chwflow.controllers.automation import AutomationController
from chwflow.controllers.generator import GeneratorController
from chwflow.controllers.hybrid import HybridController
from chwflow.controllers.prompt_loop import PromptLoopController


class TestPromptLoopController:
    def test_init_and_next(self, sample_workflow: dict[str, Any]) -> None:
        ctrl = PromptLoopController(sample_workflow, "/tmp/test-state.json")
        ctrl.init(force=True)
        assert not ctrl.is_complete()
        prompt = ctrl.next_prompt()
        assert "Initialize" in prompt
        assert "No previous step" in prompt

    def test_record_and_advance(self, sample_workflow: dict[str, Any]) -> None:
        ctrl = PromptLoopController(sample_workflow, "/tmp/test-state2.json")
        ctrl.init(force=True)
        ctrl.record("ok", "done", "good")
        assert ctrl.state.current_step == 1
        prompt = ctrl.next_prompt()
        assert "Review the previous step" in prompt

    def test_complete(self, sample_workflow: dict[str, Any]) -> None:
        ctrl = PromptLoopController(sample_workflow, "/tmp/test-state3.json")
        ctrl.init(force=True)
        ctrl.record("ok")
        ctrl.record("ok")
        ctrl.record("ok")
        assert ctrl.is_complete()

    def test_blocked(self, sample_workflow: dict[str, Any]) -> None:
        ctrl = PromptLoopController(sample_workflow, "/tmp/test-state4.json")
        ctrl.init(force=True)
        ctrl.record("blocked", "", "need input")
        assert ctrl.is_blocked()


class TestAutomationController:
    def test_execute_shell(self) -> None:
        wf = {"name": "auto", "steps": [{"id": "e", "title": "E", "action": "echo hello"}]}
        ctrl = AutomationController(wf)
        results = ctrl.execute()
        assert results[0].ok
        assert "hello" in results[0].output

    def test_succeeded_and_summary(self) -> None:
        wf = {"name": "auto", "steps": [{"id": "e", "title": "E", "action": "echo hi"}]}
        ctrl = AutomationController(wf)
        ctrl.execute()
        assert ctrl.succeeded()
        assert "✓" in ctrl.summary()


class TestHybridController:
    def test_run_automated_no_reviews(self) -> None:
        wf = {"name": "h", "steps": [{"id": "e", "title": "E", "action": "echo ok"}]}
        ctrl = HybridController(wf)
        results = ctrl.run_automated()
        assert results[0].ok

    def test_run_automated_stops_at_review(self) -> None:
        wf = {
            "name": "hybrid-wf",
            "steps": [
                {"id": "auto1", "title": "Auto", "action": "echo step1"},
                {
                    "id": "review1",
                    "title": "Review",
                    "review_required": True,
                    "acceptance": ["Check"],
                },
                {"id": "auto2", "title": "Auto2", "action": "echo step2"},
            ],
        }
        ctrl = HybridController(wf)
        results = ctrl.run_automated()
        assert len(results) == 1
        cp = ctrl.pending_checkpoint
        assert cp is not None
        assert cp.title == "Review"

    def test_approve_review(self) -> None:
        wf = {
            "name": "hybrid-wf",
            "steps": [
                {"id": "r1", "title": "Review", "review_required": True, "acceptance": ["Check"]}
            ],
        }
        ctrl = HybridController(wf)
        ctrl.run_automated()
        ctrl.approve_checkpoint("LGTM")
        assert ctrl.pending_checkpoint.status == "ok"  # type: ignore[union-attr]

    def test_reject_review(self) -> None:
        wf = {
            "name": "hybrid-wf",
            "steps": [
                {"id": "r1", "title": "Review", "review_required": True, "acceptance": ["Check"]}
            ],
        }
        ctrl = HybridController(wf)
        ctrl.run_automated()
        ctrl.reject_checkpoint("needs fixing")
        assert ctrl.pending_checkpoint.status == "needs_revision"  # type: ignore[union-attr]


class TestGeneratorController:
    def test_generate_json(self) -> None:
        gen = GeneratorController()
        wf = gen.generate_json("gen", "test", [{"id": "s", "title": "S"}])
        assert wf["name"] == "gen"
        assert wf["goal"] == "test"

    def test_generate_json_to_file(self) -> None:
        gen = GeneratorController()
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = Path(f.name)

        gen.generate_json("g", "test", [{"id": "s", "title": "S"}], out_path=str(path))
        assert path.exists()
        import json

        data = json.loads(path.read_text())
        assert data["name"] == "g"

    def test_generate_cli_script(self) -> None:
        gen = GeneratorController()
        script = gen.generate_cli_script("myscript", "desc", [{"name": "run", "help": "run it"}])
        assert "myscript" in script.lower()
        assert "argparse" in script

    def test_generate_cli_script_to_file(self) -> None:
        gen = GeneratorController()
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as f:
            path = Path(f.name)

        gen.generate_cli_script(
            "test-cli", "desc", [{"name": "x", "help": "do x"}], out_path=str(path)
        )
        assert path.exists()
        assert path.stat().st_mode & 0o755  # Check executable
