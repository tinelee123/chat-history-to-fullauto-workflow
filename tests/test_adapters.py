"""LLM adapter mock tests. No real API calls."""

from __future__ import annotations

import importlib

import pytest


class TestOpenAIAdapterImport:
    """Test adapter works when openai is available — skip gracefully when not."""

    def test_import_when_openai_available(self) -> None:
        try:
            importlib.import_module("openai")
        except ImportError:
            pytest.skip("openai not installed (optional dependency)")
            return

        from chwflow.adapters.openai_adapter import OpenAIAdapter

        adapter = OpenAIAdapter(api_key="sk-test")
        assert adapter.model == "gpt-4o"
        assert adapter.supports_streaming()

    def test_api_key_from_env(self, monkeypatch) -> None:
        monkeypatch.setenv("OPENAI_API_KEY", "sk-from-env")
        try:
            importlib.import_module("openai")
        except ImportError:
            pytest.skip("openai not installed")
            return

        from chwflow.adapters.openai_adapter import OpenAIAdapter

        adapter = OpenAIAdapter()
        assert adapter.api_key == "sk-from-env"

    def test_missing_api_key_from_env(self, monkeypatch) -> None:
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        try:
            importlib.import_module("openai")
        except ImportError:
            pytest.skip("openai not installed")
            return

        from chwflow.adapters.openai_adapter import OpenAIAdapter

        adapter = OpenAIAdapter()
        with pytest.raises(RuntimeError, match="OPENAI_API_KEY not set"):
            adapter.call("test prompt")


class TestAnthropicAdapterImport:
    def test_import_when_anthropic_available(self) -> None:
        try:
            importlib.import_module("anthropic")
        except ImportError:
            pytest.skip("anthropic not installed (optional dependency)")
            return

        from chwflow.adapters.anthropic_adapter import AnthropicAdapter

        adapter = AnthropicAdapter(api_key="sk-ant-test")
        assert "claude" in adapter.model
        assert adapter.supports_streaming()

    def test_missing_api_key_from_env(self, monkeypatch) -> None:
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        try:
            importlib.import_module("anthropic")
        except ImportError:
            pytest.skip("anthropic not installed")
            return

        from chwflow.adapters.anthropic_adapter import AnthropicAdapter

        adapter = AnthropicAdapter()
        with pytest.raises(RuntimeError, match="ANTHROPIC_API_KEY not set"):
            adapter.call("test prompt")


class TestAdapterProtocol:
    def test_abstract_interface(self) -> None:
        from chwflow.adapters.base import AbstractLLMAdapter

        assert hasattr(AbstractLLMAdapter, "call")
        assert hasattr(AbstractLLMAdapter, "supports_streaming")
