"""Perplexity LLM wrapper for CrewAI."""

from langchain_openai import ChatOpenAI

from octane_capital.config import config


def create_perplexity_llm(model: str | None = None, temperature: float = 0.7) -> ChatOpenAI:
    """Create a LangChain chat model configured for Perplexity."""
    model_name = model or config.SCOUT_MODEL

    return ChatOpenAI(
        model=model_name,
        base_url=config.PERPLEXITY_BASE_URL,
        api_key=config.require_perplexity_api_key(),
        temperature=temperature,
        max_tokens=4000,
    )
