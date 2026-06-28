"""
Octane Capital Lab - Configuration (drop-in replacement)
Fail-closed defaults. Retuned for a $200 swing-trading account: "a little risky
but never zeroed." All sizing is bounded; live trading stays off by default.
"""

import os
from dotenv import load_dotenv

load_dotenv()

_VALID_MODES = {"research", "paper", "proposal", "live_manual", "live_limited"}


def _env_bool(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).lower() == "true"


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except ValueError:
        return default


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


class Config:
    # ---- AI providers (optional for swing; needed for Scout/Auditor) ----
    PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
    PERPLEXITY_BASE_URL = os.getenv("PERPLEXITY_BASE_URL", "https://api.perplexity.ai")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    SCOUT_MODEL = "sonar-reasoning-pro"
    AUDITOR_MODEL = "sonar-deep-research"

    # ---- Supabase (optional) ----
    SUPABASE_URL = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

    # ---- Research ----
    CONFIDENCE_THRESHOLD = 8.0
    SCOUT_TARGET_TICKERS = 3
    GHOST_MODE = _env_bool("GHOST_MODE")

    # ---- Trading mode (validated; fail closed) ----
    TRADING_MODE = os.getenv("TRADING_MODE", "research")
    if TRADING_MODE not in _VALID_MODES:
        TRADING_MODE = "research"
    ENABLE_LIVE_TRADING = _env_bool("ENABLE_LIVE_TRADING")
    REQUIRE_HUMAN_APPROVAL = _env_bool("REQUIRE_HUMAN_APPROVAL", "true")

    # ---- Account / sizing ($200 swing defaults) ----
    STARTING_PAPER_CASH = _env_float("STARTING_PAPER_CASH", 200.0)
    MAX_POSITION_PCT = _env_float("MAX_POSITION_PCT", 0.25)          # <= 25% per name
    MAX_SINGLE_TRADE_DOLLARS = _env_float("MAX_SINGLE_TRADE_DOLLARS", 50.0)
    RISK_PER_TRADE_PCT = _env_float("RISK_PER_TRADE_PCT", 0.02)      # ~2% at the stop
    MAX_DAILY_LOSS_PCT = _env_float("MAX_DAILY_LOSS_PCT", 0.06)
    MAX_WEEKLY_LOSS_PCT = _env_float("MAX_WEEKLY_LOSS_PCT", 0.12)
    MAX_OPEN_POSITIONS = _env_int("MAX_OPEN_POSITIONS", 4)

    # ---- Asset permissions (options OFF for now, per plan) ----
    ALLOW_OPTIONS = _env_bool("ALLOW_OPTIONS")
    ALLOW_MARGIN = _env_bool("ALLOW_MARGIN")
    ALLOW_SHORTS = _env_bool("ALLOW_SHORTS")
    ALLOW_CRYPTO = _env_bool("ALLOW_CRYPTO")

    # ---- Swing strategy / indicators ----
    ATR_PERIOD = _env_int("ATR_PERIOD", 14)
    ATR_STOP_MULT = _env_float("ATR_STOP_MULT", 2.0)   # refined: wider stop cuts noise stop-outs
    RSI_PERIOD = _env_int("RSI_PERIOD", 14)
    SWING_MIN_SCORE = _env_float("SWING_MIN_SCORE", 7.5)   # align w/ risk gate; v2 score => lower drawdown
    SWING_MIN_HOLD_DAYS = _env_int("SWING_MIN_HOLD_DAYS", 3)
    SWING_MAX_HOLD_DAYS = _env_int("SWING_MAX_HOLD_DAYS", 30)
    SWING_TARGET_R = _env_float("SWING_TARGET_R", 2.5)             # take-profit at 2.5R
    REQUIRE_STACKED_UPTREND = _env_bool("REQUIRE_STACKED_UPTREND", "true")  # close > SMA200
    USE_REGIME_FILTER = _env_bool("USE_REGIME_FILTER", "true")     # only buy when SPY > 200dma

    # ---- Quality / "no junk" screen ----
    MIN_PRICE = _env_float("MIN_PRICE", 5.0)
    MIN_AVG_DOLLAR_VOLUME = _env_float("MIN_AVG_DOLLAR_VOLUME", 20_000_000.0)
    MIN_MARKET_CAP = _env_float("MIN_MARKET_CAP", 2_000_000_000.0)
    EARNINGS_BLACKOUT_DAYS = _env_int("EARNINGS_BLACKOUT_DAYS", 3)
    # Skip the slow per-name yfinance .info/.calendar calls during live scans
    # (the curated universe is already large-cap; keeps broad scans fast).
    QUALITY_FAST = _env_bool("QUALITY_FAST", "true")

    WATCHLIST = [
        t.strip().upper()
        for t in os.getenv(
            "WATCHLIST",
            "NVDA,AMD,AVGO,TSM,QCOM,MU,MRVL,ARM,SMCI,ASML,AAPL,MSFT,GOOGL,META,"
            "AMZN,NFLX,TSLA,ORCL,CRM,ADBE,PLTR,NOW,PANW,CRWD,NET,DDOG,SNOW,UBER,"
            "SHOP,LLY,UNH,JPM,V,MA,COST,WMT,HD,CAT,GE"
        ).split(",")
        if t.strip()
    ]

    # ---- Robinhood MCP ----
    ROBINHOOD_MCP_SERVER = os.getenv(
        "ROBINHOOD_MCP_SERVER", "https://agent.robinhood.com/mcp/trading"
    )

    @classmethod
    def require_perplexity_key(cls) -> str:
        if not cls.PERPLEXITY_API_KEY:
            raise ValueError(
                "PERPLEXITY_API_KEY is not set. Copy .env.example to .env and add your key."
            )
        return cls.PERPLEXITY_API_KEY

    @classmethod
    def is_live(cls) -> bool:
        return cls.ENABLE_LIVE_TRADING and cls.TRADING_MODE in {"live_manual", "live_limited"}


config = Config()
