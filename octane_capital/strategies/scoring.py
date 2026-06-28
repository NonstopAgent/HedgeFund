"""
Octane Capital Lab - Deterministic swing score (v2, data-driven).

Rebuilt from a feature study of ~1,700 historical setups. The only entry
features with predictive power were MOMENTUM (5/10/20-day returns) and TREND
EXTENSION (price vs its 50- and 200-day averages). RSI, proximity-to-52w-high,
and the old "overextension penalty" were noise or backwards, so they're dropped.

Still 0-10 and fully deterministic. Higher score => historically higher win
rate AND average return (monotonic), so the risk engine's threshold is now a
meaningful selectivity knob — unlike v1, where it wasn't.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SwingInputs:
    close: float
    sma50: float
    sma200: float
    rsi14: float
    atr14: float
    ret_5d: float
    avg_dollar_volume: float
    ret_10d: float = 0.0
    ret_20d: float = 0.0


def _clip(x: float, lo: float = 0.0, hi: float = 10.0) -> float:
    return max(lo, min(hi, x))


def _momentum(i: SwingInputs) -> float:
    # Weighted recent momentum; a +12.5% blended move maps to ~10.
    blend = 0.5 * i.ret_5d + 0.3 * i.ret_10d + 0.2 * i.ret_20d
    return _clip(5 + blend * 40)


def _trend(i: SwingInputs) -> float:
    # Extension above the 50/200-day averages. The data showed MORE extension
    # was better, so this rewards it (the v1 penalty was backwards).
    ext50 = (i.close / i.sma50 - 1) if i.sma50 > 0 else 0.0
    ext200 = (i.close / i.sma200 - 1) if i.sma200 > 0 else 0.0
    return _clip(5 + (0.5 * ext50 + 0.5 * ext200) * 40)


def swing_score(i: SwingInputs) -> float:
    # Momentum weighted above trend (it carried the stronger signal).
    return round(0.6 * _momentum(i) + 0.4 * _trend(i), 2)


def score_breakdown(i: SwingInputs) -> dict:
    return {
        "momentum": round(_momentum(i), 2),
        "trend": round(_trend(i), 2),
        "composite": swing_score(i),
    }
