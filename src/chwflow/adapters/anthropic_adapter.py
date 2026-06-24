"""AnthropicAdapter — call Anthropic Claude APIs from closed-loop workflows.

Install: pip install chwflow[llm]  or  pip install anthropic
Requires: ANTHROPIC_API_KEY environment variable or explicit api_key kwarg.
"""

from __future__ import annotations

import os


class AnthropicAdapter:
    """Send prompts to Anthropic Messages API."""

    def __init__(
        self,
        model: str = "claude-sonnet-4-20250514",
        api_key: str | None = None,
    ) -> None:
        self.model = model
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        self._client = None

    @property
    def _anthropic(self):
        if self._client is None:
            try:
                from anthropic import Anthropic
            except ImportError:
                raise ImportError(
                    "anthropic package required. Install with: pip install chwflow[llm] or pip install anthropic"
                )
            self._client = Anthropic(api_key=self.api_key)
        return self._client

    def call(self, prompt: str, *, max_tokens: int = 4096) -> str:
        if not self.api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY not set. Export it or pass api_key= to the constructor."
            )
        message = self._anthropic.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        for block in message.content:
            if block.type == "text":
                return block.text
        return ""

    def supports_streaming(self) -> bool:
        return True
