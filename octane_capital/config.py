"""Octane Capital Lab - configuration module.

Centralized, fail-closed configuration. API keys are read from the
environment only. There are NO embedded fallback credentials: the system
must fail closed (raise a clear error) rather than silently ship with a key.
"""

import os

from dotenv import load_dotenv

load_dotenv()


def _get_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


def _get_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _get_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return int(raw)
    except ValueError:
        return default


class Config:
    """Centralized configuration.

    Required secrets default to ``None``/empty so that missing values surface
    as explicit errors instead of being masked by a hardcoded fallback.
    """

    # --- AI providers ---
    PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
    PERPLEXITY_BASE_URL = os.getenv("PERPLEXITY_BASE_URL", "https://api.perplexity.ai")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

    # --- Model selection ---
    SCOUT_MODEL = "sonar-reasoning-pro"
    AUDITOR_MODEL = "sonar-deep-research"

    # --- Supabase (optional; vault runs in standby when absent) ---
    SUPABASE_URL = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

    # --- Research tuning ---
    CONFIDENCE_THRESHOLD = _get_float("CONFIDENCE_THRESHOLD", 8.0)
    SCOUT_TARGET_TICKERS = _get_int("SCOUT_TARGET_TICKERS", 3)
    GHOST_MODE = _get_bool("GHOST_MODE", False)

    # --- Trading safety (fail closed by default) ---
    # These defaults guarantee the system never executes live trades unless a
    # human explicitly opts in via the environment. Live execution itself is
    # not implemented in this phase.
    TRADING_MODE = os.getenv("TRADING_MODE", "research")
    ENABLE_LIVE_TRADING = _get_bool("ENABLE_LIVE_TRADING", False)
    REQUIRE_HUMAN_APPROVAL = _get_bool("REQUIRE_HUMAN_APPROVAL", True)

    def has_perplexity(self) -> bool:
        """Return True when a Perplexity API key is configured."""
        return bool(self.PERPLEXITY_API_KEY)

    def require_perplexity(self) -> None:
        """Raise a clear error when the Perplexity key is missing."""
        if not self.PERPLEXITY_API_KEY:
            raise RuntimeError(
                "PERPLEXITY_API_KEY is not set. Copy .env.example to .env and "
                "add your Perplexity API key before running research."
            )


config = Config()
