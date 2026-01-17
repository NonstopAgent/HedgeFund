"""
Octane Global Trust - Perplexity LLM Wrapper for CrewAI
Custom LLM integration maintaining PerplexityClient logic
Uses LangChain ChatOpenAI with Perplexity base URL
"""

from langchain_openai import ChatOpenAI
from config import config


def create_perplexity_llm(model: str = None, temperature: float = 0.7) -> ChatOpenAI:
    """
    Create a LangChain LLM configured for Perplexity API
    This maintains our Deep Research advantage while integrating with CrewAI
    """
    model_name = model or config.SCOUT_MODEL
    
    llm = ChatOpenAI(
        model=model_name,
        base_url=config.PERPLEXITY_BASE_URL,
        api_key=config.PERPLEXITY_API_KEY,
        temperature=temperature,
        max_tokens=4000
    )
    
    return llm
