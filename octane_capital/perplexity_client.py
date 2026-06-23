"""Octane Capital Lab - Perplexity API client.

Thin wrapper around the Perplexity Sonar API. The underlying OpenAI-compatible
client is created lazily so the module can be imported (and helpers like
``extract_json`` can be used) even when no API key is configured.
"""

import json
from typing import Any, Dict

from openai import OpenAI

from .config import config


class PerplexityClient:
    """Client for interacting with the Perplexity Sonar API."""

    def __init__(self):
        self._client = None

    @property
    def client(self) -> OpenAI:
        """Return a lazily-constructed OpenAI-compatible client.

        Raises a clear error if the Perplexity API key is missing, instead of
        failing at import time.
        """
        if self._client is None:
            config.require_perplexity()
            self._client = OpenAI(
                api_key=config.PERPLEXITY_API_KEY,
                base_url=config.PERPLEXITY_BASE_URL,
            )
        return self._client

    def query(self, model: str, query: str, **kwargs) -> Dict[str, Any]:
        """Execute a query against the Perplexity API."""
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
                    {"role": "user", "content": query},
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
        except Exception as e:
            return {"success": False, "error": str(e), "content": None}

    def extract_json(self, text: str) -> Dict[str, Any]:
        """Extract a JSON object from a text response."""
        try:
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(text[start:end])
        except (ValueError, json.JSONDecodeError):
            pass
        return {}


# Global client instance (safe to import without an API key)
perplexity_client = PerplexityClient()
