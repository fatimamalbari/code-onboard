"""OpenAI-compatible LLM adapter using httpx."""

from __future__ import annotations

import os

import httpx

from code_onboard.llm.base import LLMAdapter


class OpenAIAdapter(LLMAdapter):
    def __init__(self, api_key: str, model: str) -> None:
        super().__init__(api_key, model)
        self.base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")

    def _chat(self, user_prompt: str) -> str:
        response = httpx.post(
            f"{self.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "messages": [
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "max_tokens": 1024,
                "temperature": 0.3,
            },
            timeout=120.0,
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()
