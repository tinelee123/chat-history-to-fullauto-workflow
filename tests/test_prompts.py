"""Prompt rendering tests."""

from __future__ import annotations

from typing import Any

import pytest

from chwflow.prompts import render_next_prompt


class TestRenderNextPrompt:
    def test_first_step_no_review(self, sample_workflow: dict[str, Any]) -> None:
        state = {"current_step": 0, "history": []}
        prompt = render_next_prompt(sample_workflow, state)
        assert "No previous step" in prompt
        assert "Clarify scope" not in prompt

    def test_second_step_has_review(self, sample_workflow: dict[str, Any]) -> None:
        state = {
            "current_step": 1,
            "history": [
                {"step": 0, "status": "ok", "output": "Output from step 0", "review": "Looks good"}
            ],
        }
        prompt = render_next_prompt(sample_workflow, state)
        assert "Review the previous step" in prompt
        assert "Output from step 0" in prompt
        assert "Looks good" in prompt

    def test_completion_prompt(self, sample_workflow: dict[str, Any]) -> None:
        state = {"current_step": 3, "history": []}
        prompt = render_next_prompt(sample_workflow, state)
        assert "complete" in prompt.lower()
        assert "summary" in prompt.lower()

    def test_empty_steps_raises(self) -> None:
        wf = {"name": "empty", "steps": []}
        state = {"current_step": 0}
        with pytest.raises(ValueError, match="at least one step"):
            render_next_prompt(wf, state)

    def test_prompt_includes_acceptance_criteria(self, sample_workflow: dict[str, Any]) -> None:
        state = {"current_step": 0, "history": []}
        prompt = render_next_prompt(sample_workflow, state)
        assert "acceptance" in prompt.lower()

    def test_prompt_includes_constraints(self, sample_workflow: dict[str, Any]) -> None:
        state = {"current_step": 0, "history": []}
        prompt = render_next_prompt(sample_workflow, state)
        assert "Stable constraints" in prompt
        assert "No side effects" in prompt

    def test_prompt_includes_goal(self, sample_workflow: dict[str, Any]) -> None:
        state = {"current_step": 0, "history": []}
        prompt = render_next_prompt(sample_workflow, state)
        assert "verify the test infrastructure" in prompt.lower()

    def test_truncation(self, sample_workflow: dict[str, Any]) -> None:
        long_text = "x" * 500
        state = {
            "current_step": 1,
            "history": [{"step": 0, "status": "ok", "output": long_text, "review": ""}],
        }
        prompt = render_next_prompt(sample_workflow, state, max_chars=200)
        assert "[truncated]" in prompt

    def test_output_format_section(self, sample_workflow: dict[str, Any]) -> None:
        state = {"current_step": 0, "history": []}
        prompt = render_next_prompt(sample_workflow, state)
        assert "Output format" in prompt
        assert "Previous-step review" in prompt
