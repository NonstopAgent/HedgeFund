"""
Octane Global Trust - Configuration Module
Centralized configuration management
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Centralized configuration class"""
    
    # Perplexity API Configuration
    PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY", "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")
    PERPLEXITY_BASE_URL = os.getenv("PERPLEXITY_BASE_URL", "https://api.perplexity.ai")
    
    # Model Configuration
    SCOUT_MODEL = "sonar-reasoning-pro"
    AUDITOR_MODEL = "sonar-deep-research"
    
    # Supabase Configuration
    SUPABASE_URL = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
    
    # Confidence Threshold
    CONFIDENCE_THRESHOLD = 8.0
    
    # Scout Configuration
    SCOUT_TARGET_TICKERS = 3
    
    # Ghost Mode
    GHOST_MODE = os.getenv("GHOST_MODE", "false").lower() == "true"


config = Config()
