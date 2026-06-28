"""
Octane Capital Lab - Market Data + Indicators
Real prices and technicals. yfinance by default; for LIVE quotes prefer the
Robinhood MCP quote tool (see get_live_quote note) so paper and live agree.

Fixes the audit's #1 blocker: nothing may ever trade at a fake $100 again.
A missing price RAISES — it never silently fakes a number.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from functools import lru_cache
from typing import List, Optional

try:
    import yfinance as yf
except Exception:  # pragma: no cover - import guard
    yf = None


@dataclass
class Bar:
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: float


class MarketDataError(RuntimeError):
    """Raised when a price/indicator cannot be obtained. Never fake a value."""


class MarketData:
    """Daily-bar market data with simple indicator helpers.

    Caching: history is cached for `cache_ttl` seconds to avoid hammering the
    provider during a research/paper cycle.
    """

    def __init__(self, cache_ttl: int = 900):
        if yf is None:
            raise MarketDataError(
                "yfinance not installed. `pip install yfinance` or wire a different provider."
            )
        self.cache_ttl = cache_ttl
        self._hist_cache: dict[str, tuple[float, List[Bar]]] = {}

    # ---- core fetch -------------------------------------------------------
    def get_history(self, ticker: str, days: int = 260) -> List[Bar]:
        ticker = ticker.upper().strip()
        now = time.time()
        cached = self._hist_cache.get(ticker)
        if cached and now - cached[0] < self.cache_ttl and len(cached[1]) >= min(days, 200):
            return cached[1][-days:]

        # Pull generously in CALENDAR days so 200 TRADING-day indicators are valid
        # (~290 calendar days ≈ 200 trading days; fetch more and cache).
        period_days = max(days * 2 + 40, 420)
        try:
            df = yf.Ticker(ticker).history(period=f"{period_days}d", auto_adjust=True)
        except Exception as e:  # network / provider error
            raise MarketDataError(f"history fetch failed for {ticker}: {e}") from e
        if df is None or df.empty:
            raise MarketDataError(f"no history returned for {ticker}")

        bars = [
            Bar(
                date=str(idx.date()),
                open=float(row["Open"]),
                high=float(row["High"]),
                low=float(row["Low"]),
                close=float(row["Close"]),
                volume=float(row["Volume"]),
            )
            for idx, row in df.iterrows()
        ]
        self._hist_cache[ticker] = (now, bars)
        return bars[-days:]

    def get_price(self, ticker: str) -> float:
        """Latest close. RAISES on failure — callers must handle, never default."""
        bars = self.get_history(ticker, days=5)
        if not bars:
            raise MarketDataError(f"no price for {ticker}")
        return bars[-1].close

    # ---- indicators -------------------------------------------------------
    def sma(self, ticker: str, window: int = 50) -> float:
        closes = [b.close for b in self.get_history(ticker, days=window + 5)]
        if len(closes) < window:
            raise MarketDataError(f"not enough data for SMA{window} on {ticker}")
        return sum(closes[-window:]) / window

    def atr(self, ticker: str, period: int = 14) -> float:
        """Average True Range (Wilder-style simple mean of true ranges)."""
        bars = self.get_history(ticker, days=period + 30)
        if len(bars) < period + 1:
            raise MarketDataError(f"not enough data for ATR{period} on {ticker}")
        trs: List[float] = []
        for i in range(1, len(bars)):
            h, l, pc = bars[i].high, bars[i].low, bars[i - 1].close
            trs.append(max(h - l, abs(h - pc), abs(l - pc)))
        return sum(trs[-period:]) / period

    def rsi(self, ticker: str, period: int = 14) -> float:
        closes = [b.close for b in self.get_history(ticker, days=period + 50)]
        if len(closes) < period + 1:
            raise MarketDataError(f"not enough data for RSI{period} on {ticker}")
        gains, losses = [], []
        for i in range(1, len(closes)):
            ch = closes[i] - closes[i - 1]
            gains.append(max(ch, 0.0))
            losses.append(max(-ch, 0.0))
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        if avg_loss == 0:
            return 100.0
        rs = avg_gain / avg_loss
        return 100.0 - (100.0 / (1.0 + rs))

    def avg_dollar_volume(self, ticker: str, days: int = 20) -> float:
        bars = self.get_history(ticker, days=days + 5)
        if not bars:
            return 0.0
        recent = bars[-days:]
        return sum(b.close * b.volume for b in recent) / max(len(recent), 1)

    def pct_change(self, ticker: str, lookback_days: int = 2) -> float:
        bars = self.get_history(ticker, days=lookback_days + 5)
        if len(bars) <= lookback_days:
            return 0.0
        old, new = bars[-1 - lookback_days].close, bars[-1].close
        return (new - old) / old if old else 0.0

    # ---- info (best-effort; may be missing) -------------------------------
    @lru_cache(maxsize=256)
    def market_cap(self, ticker: str) -> Optional[float]:
        try:
            info = yf.Ticker(ticker.upper()).info
            mc = info.get("marketCap")
            return float(mc) if mc else None
        except Exception:
            return None

    @lru_cache(maxsize=256)
    def days_to_earnings(self, ticker: str) -> Optional[int]:
        """Best-effort. Returns None if unknown (treated as mild risk upstream)."""
        try:
            from datetime import date
            cal = yf.Ticker(ticker.upper()).calendar
            ed = None
            if isinstance(cal, dict):
                ed = cal.get("Earnings Date")
                if isinstance(ed, (list, tuple)) and ed:
                    ed = ed[0]
            if ed is None:
                return None
            ed = ed.date() if hasattr(ed, "date") else ed
            return (ed - date.today()).days
        except Exception:
            return None


# NOTE for LIVE trading:
#   Once the Robinhood MCP session is connected, fetch the quote from Robinhood
#   instead of yfinance so the price you size against equals the price you trade
#   against. Wrap that call behind a class with the same get_price() signature
#   and inject it in place of MarketData.
