"""Perplexity Sonar API client helpers."""

from __future__ import annotations

import json
from typing import Any

from openai import OpenAI

from octane_capital.config import ConfigError, config


class PerplexityClient:
    """Client for interacting with Perplexity Sonar API."""

    def __init__(self) -> None:
        self._client: OpenAI | None = None

    @property
    def client(self) -> OpenAI:
        """Create the API client lazily so imports work without secrets."""
        if self._client is None:
            self._client = OpenAI(
                api_key=config.require_perplexity_api_key(),
                base_url=config.PERPLEXITY_BASE_URL,
            )
        return self._client

    def query(self, model: str, query: str, **kwargs: Any) -> dict[str, Any]:
        """Execute a query against Perplexity API."""
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": kwargs.get(
                            "system_prompt",
                            "You are a sophisticated financial research assistant.",
                        ),
                    },
                    {
                        "role": "user",
                        "content": query,
                    },
                ],
                temperature=kwargs.get("temperature", 0.7),
                max_tokens=kwargs.get("max_tokens", 4000),
            )

            return {
                "success": True,
                "content": response.choices[0].message.content,
                "model": response.model,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                },
            }
        except ConfigError as exc:
            return {
                "success": False,
                "error": str(exc),
                "content": None,
            }
        except Exception as exc:
            return {
                "success": False,
                "error": str(exc),
                "content": None,
            }

    def extract_json(self, text: str) -> Any:
        """Extract the first JSON object or array from a text response."""
        stripped = text.strip()
        if not stripped:
            return {}

        try:
            return json.loads(stripped)
        except json.JSONDecodeError:
            pass

        candidates = [
            (stripped.find("{"), stripped.rfind("}") + 1),
            (stripped.find("["), stripped.rfind("]") + 1),
        ]
        for start, end in candidates:
            if start >= 0 and end > start:
                try:
                    return json.loads(stripped[start:end])
                except json.JSONDecodeError:
                    continue

        return {}


perplexity_client = PerplexityClient()
