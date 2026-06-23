"""
Octane Capital Lab - Perplexity LLM Wrapper for CrewAI
Uses LangChain ChatOpenAI with Perplexity base URL.
"""

from langchain_openai import ChatOpenAI

from octane_capital.config import config


def create_perplexity_llm(model: str = None, temperature: float = 0.7) -> ChatOpenAI:
    """Create a LangChain LLM configured for the Perplexity API."""
    config.require_perplexity_key()
    model_name = model or config.SCOUT_MODEL

    return ChatOpenAI(
        model=model_name,
        base_url=config.PERPLEXITY_BASE_URL,
        api_key=config.PERPLEXITY_API_KEY,
        temperature=temperature,
        max_tokens=4000,
    )
