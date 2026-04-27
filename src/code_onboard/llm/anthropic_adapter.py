"""Anthropic Claude LLM adapter using httpx."""

from __future__ import annotations

import httpx

from code_onboard.llm.base import LLMAdapter


class AnthropicAdapter(LLMAdapter):
    def _chat(self, user_prompt: str) -> str:
        response = httpx.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": self.model,
                "max_tokens": 1024,
                "system": self.system_prompt,
                "messages": [
                    {"role": "user", "content": user_prompt},
                ],
            },
            timeout=120.0,
        )
        response.raise_for_status()
        data = response.json()
        return data["content"][0]["text"].strip()
