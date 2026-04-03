"""Tests for unified AI client behavior."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agents.ai_client import AIClient, get_client_for_action


@pytest.mark.parametrize(
    ("provider", "env_name"),
    [
        ("anthropic", "ANTHROPIC_API_KEY"),
        ("openai", "OPENAI_API_KEY"),
        ("google", "GOOGLE_API_KEY"),
    ],
)
def test_ai_client_initialization(provider: str, env_name: str, monkeypatch: pytest.MonkeyPatch) -> None:
    """AIClient should initialize for each supported provider."""
    monkeypatch.setenv(env_name, "test-key")

    client = AIClient(provider=provider, model="test-model")

    assert client.provider == provider
    assert client.model == "test-model"


def test_ai_client_missing_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Initialization should fail with a clear error if API key is missing."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        AIClient(provider="openai", model="gpt-test")


def test_chat_mock_openai(monkeypatch: pytest.MonkeyPatch) -> None:
    """chat should return provider output text."""
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    client = AIClient(provider="openai", model="gpt-test")

    async def fake_openai_chat(system_prompt: str, messages: list[dict], max_tokens: int) -> str:
        assert system_prompt == "system"
        assert messages == [{"role": "user", "content": "hello"}]
        assert max_tokens == 123
        return "mocked-response"

    monkeypatch.setattr(client, "_openai_chat", fake_openai_chat)

    result = asyncio.run(
        client.chat(
            system_prompt="system",
            messages=[{"role": "user", "content": "hello"}],
            max_tokens=123,
        )
    )

    assert result == "mocked-response"


def test_get_client_for_action(monkeypatch: pytest.MonkeyPatch) -> None:
    """Model mapping should be loaded from Supabase table."""

    class FakeQuery:
        def select(self, *_args, **_kwargs):
            return self

        def eq(self, *_args, **_kwargs):
            return self

        def limit(self, *_args, **_kwargs):
            return self

        def execute(self):
            return SimpleNamespace(data=[{"ai_provider": "openai", "ai_model": "gpt-test"}])

    class FakeSupabaseClient:
        def __init__(self):
            self.client = SimpleNamespace(table=lambda _table_name: FakeQuery())

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr("agents.ai_client.SupabaseClient", FakeSupabaseClient)

    client = asyncio.run(get_client_for_action("sample_action"))

    assert isinstance(client, AIClient)
    assert client.provider == "openai"
    assert client.model == "gpt-test"
    assert client.action_name == "sample_action"


def test_retry_on_rate_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    """429-like failures should be retried with exponential backoff."""
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    client = AIClient(provider="openai", model="gpt-test")

    attempts = {"count": 0}

    class RateLimitError(Exception):
        status_code = 429

    async def flaky_operation(*_args, **_kwargs):
        attempts["count"] += 1
        if attempts["count"] < 3:
            raise RateLimitError("rate limit")
        return "ok"

    sleep_calls: list[int] = []

    async def fake_sleep(seconds: int) -> None:
        sleep_calls.append(seconds)

    monkeypatch.setattr(client, "_openai_chat", flaky_operation)
    monkeypatch.setattr("agents.ai_client.asyncio.sleep", fake_sleep)

    result = asyncio.run(client.chat(system_prompt="system", messages=[]))

    assert result == "ok"
    assert attempts["count"] == 3
    assert sleep_calls == [1, 2]
