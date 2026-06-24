"""AbstractLLMAdapter — protocol for LLM integration in closed-loop workflows."""

from __future__ import annotations

from typing import Protocol


class AbstractLLMAdapter(Protocol):
    """Minimal interface for an LLM API adapter.

    If openai/anthropic SDKs are not installed, a helpful error message
    is raised rather than crashing at import time.
    """

    def call(self, prompt: str, *, max_tokens: int = 4096) -> str:
        """Send a prompt to the LLM and return the response text."""
        ...

    def supports_streaming(self) -> bool:
        """Return True if the adapter supports streaming responses."""
        ...
