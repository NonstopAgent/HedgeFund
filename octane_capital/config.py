"""Configuration for Octane Capital Lab.

Configuration is environment-only for secrets. The defaults keep the system in
research mode with live trading disabled.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


class ConfigError(RuntimeError):
    """Raised when required configuration is missing for a requested feature."""


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return float(value)


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return int(value)


@dataclass(frozen=True)
class Config:
    """Centralized configuration class."""

    # AI provider configuration. Never provide secret fallbacks here.
    PERPLEXITY_API_KEY: str | None = os.getenv("PERPLEXITY_API_KEY")
    PERPLEXITY_BASE_URL: str = os.getenv(
        "PERPLEXITY_BASE_URL", "https://api.perplexity.ai"
    )
    ANTHROPIC_API_KEY: str | None = os.getenv("ANTHROPIC_API_KEY")

    # Model configuration.
    SCOUT_MODEL: str = os.getenv("SCOUT_MODEL", "sonar-reasoning-pro")
    AUDITOR_MODEL: str = os.getenv("AUDITOR_MODEL", "sonar-deep-research")

    # Supabase configuration.
    SUPABASE_URL: str | None = os.getenv("SUPABASE_URL")
    SUPABASE_KEY: str | None = os.getenv("SUPABASE_KEY")

    # Trading safety defaults.
    TRADING_MODE: str = os.getenv("TRADING_MODE", "research")
    ENABLE_LIVE_TRADING: bool = _env_bool("ENABLE_LIVE_TRADING", False)
    REQUIRE_HUMAN_APPROVAL: bool = _env_bool("REQUIRE_HUMAN_APPROVAL", True)

    # Risk limit defaults for later phases.
    STARTING_PAPER_CASH: float = _env_float("STARTING_PAPER_CASH", 10_000.0)
    MAX_POSITION_PCT: float = _env_float("MAX_POSITION_PCT", 0.05)
    MAX_SINGLE_TRADE_DOLLARS: float = _env_float("MAX_SINGLE_TRADE_DOLLARS", 250.0)
    MAX_DAILY_LOSS_PCT: float = _env_float("MAX_DAILY_LOSS_PCT", 0.02)
    MAX_WEEKLY_LOSS_PCT: float = _env_float("MAX_WEEKLY_LOSS_PCT", 0.05)
    MAX_OPEN_POSITIONS: int = _env_int("MAX_OPEN_POSITIONS", 5)
    ALLOW_OPTIONS: bool = _env_bool("ALLOW_OPTIONS", False)
    ALLOW_MARGIN: bool = _env_bool("ALLOW_MARGIN", False)
    ALLOW_SHORTS: bool = _env_bool("ALLOW_SHORTS", False)
    ALLOW_CRYPTO: bool = _env_bool("ALLOW_CRYPTO", False)

    # Existing research configuration.
    CONFIDENCE_THRESHOLD: float = _env_float("CONFIDENCE_THRESHOLD", 8.0)
    SCOUT_TARGET_TICKERS: int = _env_int("SCOUT_TARGET_TICKERS", 3)
    GHOST_MODE: bool = _env_bool("GHOST_MODE", False)

    # Future Robinhood MCP configuration. Phase 1 does not use this.
    ROBINHOOD_MCP_SERVER: str = os.getenv(
        "ROBINHOOD_MCP_SERVER", "https://agent.robinhood.com/mcp/trading"
    )

    def require_perplexity_api_key(self) -> str:
        """Return the Perplexity key or raise a clear configuration error."""
        if not self.PERPLEXITY_API_KEY:
            raise ConfigError(
                "PERPLEXITY_API_KEY is required to run a research cycle. "
                "Copy .env.example to .env and add your rotated key."
            )
        return self.PERPLEXITY_API_KEY

    def validate_live_trading_disabled_by_default(self) -> None:
        """Fail closed if live trading is requested without both safety switches."""
        if self.ENABLE_LIVE_TRADING and self.TRADING_MODE != "live_manual":
            raise ConfigError(
                "ENABLE_LIVE_TRADING=true requires TRADING_MODE=live_manual."
            )


config = Config()
