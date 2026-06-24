"""OpenAIAdapter — call OpenAI-compatible APIs from closed-loop workflows.

Install: pip install chwflow[llm]  or  pip install openai
Requires: OPENAI_API_KEY environment variable or explicit api_key kwarg.
"""

from __future__ import annotations

import os


class OpenAIAdapter:
    """Send prompts to OpenAI Chat Completions API.

    Works with any OpenAI-compatible endpoint (Azure, Together, Groq, etc.)
    by setting the base_url parameter.
    """

    def __init__(
        self,
        model: str = "gpt-4o",
        api_key: str | None = None,
        base_url: str | None = None,
    ) -> None:
        self.model = model
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self.base_url = base_url
        self._client = None

    @property
    def _openai(self):
        if self._client is None:
            try:
                from openai import OpenAI
            except ImportError:
                raise ImportError(
                    "openai package required. Install with: pip install chwflow[llm] or pip install openai"
                )
            self._client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        return self._client

    def call(self, prompt: str, *, max_tokens: int = 4096) -> str:
        if not self.api_key:
            raise RuntimeError(
                "OPENAI_API_KEY not set. Export it or pass api_key= to the constructor."
            )
        response = self._openai.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
        )
        choice = response.choices[0]
        return choice.message.content or ""

    def supports_streaming(self) -> bool:
        return True
