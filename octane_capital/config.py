"""
Octane Capital Lab - Configuration Module
Centralized configuration management with fail-closed defaults.
"""

import os
from dotenv import load_dotenv

load_dotenv()


def _env_bool(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).lower() == "true"


class Config:
    """Centralized configuration class."""

    # AI providers
    PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
    PERPLEXITY_BASE_URL = os.getenv("PERPLEXITY_BASE_URL", "https://api.perplexity.ai")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

    # Model configuration
    SCOUT_MODEL = "sonar-reasoning-pro"
    AUDITOR_MODEL = "sonar-deep-research"

    # Supabase configuration
    SUPABASE_URL = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

    # Research configuration
    CONFIDENCE_THRESHOLD = 8.0
    SCOUT_TARGET_TICKERS = 3
    GHOST_MODE = _env_bool("GHOST_MODE")

    # Trading safety (defaults: research-only, no live trading)
    TRADING_MODE = os.getenv("TRADING_MODE", "research")
    ENABLE_LIVE_TRADING = _env_bool("ENABLE_LIVE_TRADING")
    REQUIRE_HUMAN_APPROVAL = _env_bool("REQUIRE_HUMAN_APPROVAL", "true")

    # Risk limits (used in later phases)
    STARTING_PAPER_CASH = float(os.getenv("STARTING_PAPER_CASH", "10000"))
    MAX_POSITION_PCT = float(os.getenv("MAX_POSITION_PCT", "0.05"))
    MAX_SINGLE_TRADE_DOLLARS = float(os.getenv("MAX_SINGLE_TRADE_DOLLARS", "250"))
    MAX_DAILY_LOSS_PCT = float(os.getenv("MAX_DAILY_LOSS_PCT", "0.02"))
    MAX_WEEKLY_LOSS_PCT = float(os.getenv("MAX_WEEKLY_LOSS_PCT", "0.05"))
    MAX_OPEN_POSITIONS = int(os.getenv("MAX_OPEN_POSITIONS", "5"))
    ALLOW_OPTIONS = _env_bool("ALLOW_OPTIONS")
    ALLOW_MARGIN = _env_bool("ALLOW_MARGIN")
    ALLOW_SHORTS = _env_bool("ALLOW_SHORTS")
    ALLOW_CRYPTO = _env_bool("ALLOW_CRYPTO")

    # Robinhood MCP (stub for later phases)
    ROBINHOOD_MCP_SERVER = os.getenv(
        "ROBINHOOD_MCP_SERVER",
        "https://agent.robinhood.com/mcp/trading",
    )

    @classmethod
    def require_perplexity_key(cls) -> str:
        """Return Perplexity API key or raise a clear configuration error."""
        if not cls.PERPLEXITY_API_KEY:
            raise ValueError(
                "PERPLEXITY_API_KEY is not set. Copy .env.example to .env and add your key."
            )
        return cls.PERPLEXITY_API_KEY


config = Config()
