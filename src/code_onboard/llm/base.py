"""Abstract LLM adapter and auto-detection factory."""

from __future__ import annotations

from abc import ABC, abstractmethod

from code_onboard.config import Settings
from code_onboard.llm.prompts import (
    ARCHITECTURE_PROMPT,
    ENTRY_POINTS_PROMPT,
    HOTSPOTS_PROMPT,
    MODULE_RESPONSIBILITIES_PROMPT,
    READING_ORDER_PROMPT,
    SYSTEM_PROMPT,
)


class LLMAdapter(ABC):
    def __init__(self, api_key: str, model: str) -> None:
        self.api_key = api_key
        self.model = model
        self.system_prompt = SYSTEM_PROMPT

    @abstractmethod
    def _chat(self, user_prompt: str) -> str:
        """Send a chat message and return the response text."""
        ...

    def generate_narratives(self, context: dict[str, str]) -> dict[str, str]:
        """Generate all narrative sections."""
        narratives: dict[str, str] = {}

        prompts = {
            "entry_points": ENTRY_POINTS_PROMPT.format(**context),
            "architecture": ARCHITECTURE_PROMPT.format(**context),
            "hotspots": HOTSPOTS_PROMPT.format(**context),
            "reading_order": READING_ORDER_PROMPT.format(**context),
            "module_responsibilities": MODULE_RESPONSIBILITIES_PROMPT.format(**context),
        }

        for key, prompt in prompts.items():
            try:
                narratives[key] = self._chat(prompt)
            except Exception as e:
                narratives[key] = f"*LLM generation failed: {e}*"

        return narratives


class NoopAdapter(LLMAdapter):
    """No-op adapter when LLM is disabled."""

    def __init__(self) -> None:
        self.api_key = ""
        self.model = ""
        self.system_prompt = ""

    def _chat(self, user_prompt: str) -> str:
        return ""

    def generate_narratives(self, context: dict[str, str]) -> dict[str, str]:
        return {}


def create_adapter(settings: Settings) -> LLMAdapter:
    provider = settings.detect_provider()
    api_key = settings.get_api_key()
    model = settings.get_model_name()

    if provider == "none" or not api_key:
        return NoopAdapter()

    if provider == "openai":
        from code_onboard.llm.openai_adapter import OpenAIAdapter
        return OpenAIAdapter(api_key=api_key, model=model)

    if provider == "anthropic":
        from code_onboard.llm.anthropic_adapter import AnthropicAdapter
        return AnthropicAdapter(api_key=api_key, model=model)

    return NoopAdapter()
