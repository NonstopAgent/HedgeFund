"""
Octane Global Trust - Perplexity API Client
Wrapper for Perplexity Sonar API interactions
"""

from openai import OpenAI
from typing import Dict, Any, List
import json
from config import config


class PerplexityClient:
    """Client for interacting with Perplexity Sonar API"""
    
    def __init__(self):
        self.client = OpenAI(
            api_key=config.PERPLEXITY_API_KEY,
            base_url=config.PERPLEXITY_BASE_URL
        )
    
    def query(self, model: str, query: str, **kwargs) -> Dict[str, Any]:
        """
        Execute a query against Perplexity API
        
        Args:
            model: The model to use (e.g., sonar-reasoning-pro)
            query: The query string
            **kwargs: Additional parameters for the API call
            
        Returns:
            Dictionary containing the response
        """
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": kwargs.get("system_prompt", "You are a sophisticated financial research assistant.")
                    },
                    {
                        "role": "user",
                        "content": query
                    }
                ],
                temperature=kwargs.get("temperature", 0.7),
                max_tokens=kwargs.get("max_tokens", 4000)
            )
            
            return {
                "success": True,
                "content": response.choices[0].message.content,
                "model": response.model,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "content": None
            }
    
    def extract_json(self, text: str) -> Dict[str, Any]:
        """Extract JSON from text response"""
        try:
            # Try to find JSON in the text
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(text[start:end])
        except:
            pass
        return {}


# Global client instance
perplexity_client = PerplexityClient()
