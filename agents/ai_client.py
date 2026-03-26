"""Common AI client skeleton."""

from typing import Any


class AIClient:
    """Provide a unified interface for AI providers."""

    async def generate_text(self, prompt: str, provider: str, model: str) -> str:
        """Generate text from the selected AI provider and model."""
        return ""

    async def generate_json(self, prompt: str, provider: str, model: str) -> dict[str, Any]:
        """Generate structured JSON from the selected AI provider and model."""
        return {}

