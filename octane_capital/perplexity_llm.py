"""Octane Capital Lab - Perplexity LLM wrapper for CrewAI.

Builds a CrewAI ``LLM`` pointed at the Perplexity API. Perplexity exposes an
OpenAI-compatible Chat Completions endpoint, so we use CrewAI's native
``openai`` provider with a custom ``base_url``.
"""

from crewai import LLM

from .config import config


def create_perplexity_llm(model: str = None, temperature: float = 0.7) -> LLM:
    """Create a CrewAI LLM configured for the Perplexity API."""
    config.require_perplexity()
    model_name = model or config.SCOUT_MODEL

    return LLM(
        model=model_name,
        provider="openai",
        base_url=config.PERPLEXITY_BASE_URL,
        api_key=config.PERPLEXITY_API_KEY,
        temperature=temperature,
        max_tokens=4000,
    )
