"""Common AI client implementation."""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any

import anthropic
import google.generativeai as genai
from dotenv import load_dotenv
from openai import AsyncOpenAI

from db.supabase_client import SupabaseClient

LOGGER = logging.getLogger(__name__)

SUPPORTED_PROVIDERS = {"anthropic", "openai", "google"}
MAX_RETRIES = 3
REQUEST_TIMEOUT_SECONDS = 30


class AIClient:
    """Provide a unified interface for AI providers."""

    def __init__(self, provider: str, model: str) -> None:
        """Initialize a concrete provider client with shared config."""
        load_dotenv()

        normalized_provider = provider.strip().lower()
        if normalized_provider not in SUPPORTED_PROVIDERS:
            raise ValueError(
                f"Unsupported provider '{provider}'. Supported providers: {sorted(SUPPORTED_PROVIDERS)}"
            )

        self.provider = normalized_provider
        self.model = model
        self.action_name = "unknown"

        if self.provider == "anthropic":
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY is not configured in .env.")
            self.client = anthropic.AsyncAnthropic(api_key=api_key)
        elif self.provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY is not configured in .env.")
            self.client = AsyncOpenAI(api_key=api_key)
        else:
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                raise ValueError("GOOGLE_API_KEY is not configured in .env.")
            genai.configure(api_key=api_key)
            self.client = genai.GenerativeModel(model_name=self.model)

    async def chat(
        self,
        system_prompt: str,
        messages: list[dict],
        max_tokens: int = 2000,
        use_cache: bool = True,
    ) -> str:
        """Call an AI provider through a unified interface and return text output."""
        if self.provider == "anthropic":
            return await self._with_retry(
                lambda: self._anthropic_chat(
                    system_prompt=system_prompt,
                    messages=messages,
                    max_tokens=max_tokens,
                    use_cache=use_cache,
                )
            )
        if self.provider == "openai":
            return await self._with_retry(
                lambda: self._openai_chat(
                    system_prompt=system_prompt,
                    messages=messages,
                    max_tokens=max_tokens,
                )
            )
        return await self._with_retry(
            lambda: self._google_chat(
                system_prompt=system_prompt,
                messages=messages,
                max_tokens=max_tokens,
            )
        )

    async def chat_with_history(
        self,
        system_prompt: str,
        history: list[dict],
        new_message: str,
        max_tokens: int = 2000,
    ) -> str:
        """Call the provider while preserving conversation history."""
        conversation = [*history, {"role": "user", "content": new_message}]
        return await self.chat(
            system_prompt=system_prompt,
            messages=conversation,
            max_tokens=max_tokens,
            use_cache=True,
        )

    async def _anthropic_chat(
        self,
        system_prompt: str,
        messages: list[dict],
        max_tokens: int,
        use_cache: bool,
    ) -> str:
        system_block: dict[str, Any] = {"type": "text", "text": system_prompt}
        if use_cache:
            system_block["cache_control"] = {"type": "ephemeral"}

        response = await asyncio.wait_for(
            self.client.messages.create(
                model=self.model,
                system=[system_block],
                messages=messages,
                max_tokens=max_tokens,
            ),
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        text = "".join(
            block.text for block in response.content if getattr(block, "type", "") == "text"
        )

        usage = getattr(response, "usage", None)
        input_tokens = getattr(usage, "input_tokens", 0) if usage else 0
        output_tokens = getattr(usage, "output_tokens", 0) if usage else 0
        self._log_api_call(token_count=input_tokens + output_tokens)
        return text

    async def _openai_chat(self, system_prompt: str, messages: list[dict], max_tokens: int) -> str:
        response = await asyncio.wait_for(
            self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "system", "content": system_prompt}, *messages],
                max_tokens=max_tokens,
            ),
            timeout=REQUEST_TIMEOUT_SECONDS,
        )

        content = response.choices[0].message.content or ""
        usage = getattr(response, "usage", None)
        token_count = getattr(usage, "total_tokens", 0) if usage else 0
        self._log_api_call(token_count=token_count)
        return content

    async def _google_chat(self, system_prompt: str, messages: list[dict], max_tokens: int) -> str:
        prompt_text = self._google_prompt_from_messages(system_prompt=system_prompt, messages=messages)

        response = await asyncio.wait_for(
            asyncio.to_thread(
                self.client.generate_content,
                prompt_text,
                generation_config=genai.GenerationConfig(max_output_tokens=max_tokens),
            ),
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        usage = getattr(response, "usage_metadata", None)
        token_count = getattr(usage, "total_token_count", 0) if usage else 0
        self._log_api_call(token_count=token_count)
        return getattr(response, "text", "") or ""

    @staticmethod
    def _google_prompt_from_messages(system_prompt: str, messages: list[dict]) -> str:
        lines = [f"[System]\n{system_prompt}\n"]
        for message in messages:
            role = message.get("role", "user").capitalize()
            content = message.get("content", "")
            lines.append(f"[{role}]\n{content}\n")
        lines.append("[Assistant]\n")
        return "\n".join(lines)

    async def _with_retry(self, operation: Any) -> str:
        for attempt in range(MAX_RETRIES):
            try:
                return await operation()
            except asyncio.TimeoutError as exc:
                raise TimeoutError(
                    f"AI provider request timed out after {REQUEST_TIMEOUT_SECONDS} seconds."
                ) from exc
            except Exception as exc:
                if not self._is_rate_limit_error(exc) or attempt == MAX_RETRIES - 1:
                    raise
                await asyncio.sleep(2**attempt)
        raise RuntimeError("Retry loop finished unexpectedly.")

    @staticmethod
    def _is_rate_limit_error(exc: Exception) -> bool:
        status_code = getattr(exc, "status_code", None)
        message = str(exc)
        return status_code == 429 or "429" in message or "rate limit" in message.lower()

    def _log_api_call(self, token_count: int) -> None:
        LOGGER.info(
            "AI call completed: action_name=%s provider=%s model=%s tokens=%s",
            self.action_name,
            self.provider,
            self.model,
            token_count,
        )


async def get_client_for_action(action_name: str) -> AIClient:
    """Resolve provider/model from Supabase and return a configured AI client."""
    supabase = SupabaseClient()
    response = (
        supabase.client.table("ai_action_models")
        .select("ai_provider,ai_model")
        .eq("action_name", action_name)
        .limit(1)
        .execute()
    )
    records = response.data or []
    if not records:
        raise ValueError(f"No AI model mapping found for action_name '{action_name}'.")

    record = records[0]
    client = AIClient(provider=record["ai_provider"], model=record["ai_model"])
    client.action_name = action_name
    return client
