"""Settings and environment variable loading."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Settings:
    repo_path: Path = field(default_factory=lambda: Path("."))
    output: Path = field(default_factory=lambda: Path("ONBOARDING.md"))
    top_n: int = 10
    max_files: int = 500
    provider: str = "auto"
    model: str | None = None
    no_llm: bool = False
    html: bool = False
    verbose: bool = False

    def detect_provider(self) -> str:
        """Auto-detect LLM provider from environment variables."""
        if self.no_llm or self.provider == "none":
            return "none"
        if self.provider not in ("auto", "none", "openai", "anthropic"):
            return self.provider
        if self.provider == "auto":
            if os.environ.get("ANTHROPIC_API_KEY"):
                return "anthropic"
            if os.environ.get("OPENAI_API_KEY"):
                return "openai"
            return "none"
        return self.provider

    def get_api_key(self) -> str | None:
        provider = self.detect_provider()
        if provider == "anthropic":
            return os.environ.get("ANTHROPIC_API_KEY")
        if provider == "openai":
            return os.environ.get("OPENAI_API_KEY")
        return None

    def get_model_name(self) -> str:
        if self.model:
            return self.model
        provider = self.detect_provider()
        if provider == "anthropic":
            return "claude-sonnet-4-20250514"
        if provider == "openai":
            return "gpt-4o"
        return ""
