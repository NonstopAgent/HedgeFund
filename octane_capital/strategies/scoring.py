"""
Octane Capital Lab - Deterministic swing score
Turns technicals into an auditable 0-10 confidence. No LLM in the number, so the
risk engine's MIN_CONFIDENCE_BUY gate means something testable.

Designed for SWING long setups: trade established uptrends with momentum, avoid
overextended/overbought entries, prefer liquid, normal-volatility names.
"""

from __future__ import annotations

from dataclasses import dataclass

# weights sum to 1.0
WEIGHTS = {
    "trend": 0.30,
    "momentum": 0.25,
    "not_overextended": 0.15,
    "liquidity": 0.15,
    "volatility": 0.15,
}


@dataclass
class SwingInputs:
    close: float
    sma50: float
    sma200: float
    rsi14: float
    atr14: float
    ret_5d: float                 # 5-day return, e.g. 0.04 = +4%
    avg_dollar_volume: float


def _clip(x: float, lo: float = 0.0, hi: float = 10.0) -> float:
    return max(lo, min(hi, x))


def _trend(i: SwingInputs) -> float:
    # Stacked uptrend (close>50>200) scores best; below 50 scores low.
    score = 5.0
    if i.sma50 > 0:
        score += 3.0 if i.close > i.sma50 else -3.0
    if i.sma200 > 0:
        score += 2.0 if i.sma50 > i.sma200 else -2.0
    return _clip(score)


def _momentum(i: SwingInputs) -> float:
    # Reward positive 5d momentum and a healthy (not extreme) RSI.
    m = 5.0 + i.ret_5d * 60.0          # +5% over 5d ≈ +3
    if i.rsi14 >= 75:                  # overbought — fade the score
        m -= 2.5
    elif 55 <= i.rsi14 < 70:           # momentum sweet spot
        m += 1.5
    elif i.rsi14 < 45:                 # no momentum
        m -= 2.0
    return _clip(m)


def _not_overextended(i: SwingInputs) -> float:
    # Penalize entries stretched far above the 50-day (mean-reversion risk).
    if i.sma50 <= 0:
        return 5.0
    ext = (i.close - i.sma50) / i.sma50      # how far above the MA
    if ext <= 0:
        return 6.0                           # at/below MA — fine for swing pullback
    return _clip(9.0 - ext * 60.0)           # +10% extended ≈ score 3


def _liquidity(i: SwingInputs) -> float:
    adv = i.avg_dollar_volume
    if adv >= 100_000_000:
        return 10.0
    if adv >= 20_000_000:
        return 8.0
    if adv >= 5_000_000:
        return 5.0
    return 2.0


def _volatility(i: SwingInputs) -> float:
    # Moderate ATR% is ideal; too placid = no move, too wild = whipsaw.
    if i.close <= 0:
        return 5.0
    atr_pct = i.atr14 / i.close
    if atr_pct < 0.01:
        return 5.0
    if atr_pct <= 0.05:
        return 9.0
    if atr_pct <= 0.08:
        return 6.0
    return 3.0


def swing_score(i: SwingInputs) -> float:
    parts = {
        "trend": _trend(i),
        "momentum": _momentum(i),
        "not_overextended": _not_overextended(i),
        "liquidity": _liquidity(i),
        "volatility": _volatility(i),
    }
    return round(sum(parts[k] * WEIGHTS[k] for k in WEIGHTS), 2)


def score_breakdown(i: SwingInputs) -> dict:
    return {
        "trend": _trend(i),
        "momentum": _momentum(i),
        "not_overextended": _not_overextended(i),
        "liquidity": _liquidity(i),
        "volatility": _volatility(i),
        "composite": swing_score(i),
    }
