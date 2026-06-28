"""
Octane Capital Lab - Strategy refinement harness.
Runs the walk-forward backtest under several variants to find configs that
improve expectancy / drawdown vs the baseline. Evidence-driven tuning.

    python -m octane_capital.backtest.refine --years 2
"""

from __future__ import annotations

import argparse

from octane_capital.data.universe import get_universe
from octane_capital.strategies.scoring import SwingInputs, swing_score
from octane_capital.backtest.walk_forward import (
    _sma, _atr, _rsi, load_bars, Trade, summarize,
    MIN_PRICE, MIN_ADV, ATR_PERIOD, SLIPPAGE,
)


def regime_map(spy_bars: list[dict]) -> dict[str, bool]:
    """date -> True only when SPY is above a RISING 200-day SMA (confirmed uptrend).

    Requiring the 200dma to be RISING (not just price > 200dma) keeps the strategy
    out of bear markets like 2022, where price repeatedly popped above a *falling*
    average on relief rallies and then reversed."""
    closes = [b["close"] for b in spy_bars]
    on = {}
    for i in range(len(spy_bars)):
        if i < 220:
            on[spy_bars[i]["date"]] = True
            continue
        sma_now = sum(closes[i - 199:i + 1]) / 200
        sma_prev = sum(closes[i - 219:i - 19]) / 200  # 200dma as of ~20 sessions ago
        on[spy_bars[i]["date"]] = (closes[i] > sma_now) and (sma_now > sma_prev)
    return on


def simulate(ticker: str, bars: list[dict], p: dict, regime_on: dict) -> list[Trade]:
    trades: list[Trade] = []
    n = len(bars)
    closes = [b["close"] for b in bars]
    highs = [b["high"] for b in bars]
    lows = [b["low"] for b in bars]
    vols = [b["volume"] for b in bars]
    i = 200
    while i < n - 1:
        c = closes[i]
        sma50 = _sma(closes[:i + 1], 50)
        sma200 = _sma(closes[:i + 1], 200)
        adv = sum(closes[k] * vols[k] for k in range(i - 19, i + 1)) / 20
        if c < MIN_PRICE or adv < MIN_ADV:
            i += 1; continue
        prior = closes[i - 5]
        r5 = (c - prior) / prior if prior else 0.0
        if not (c > sma50 and r5 > 0):
            i += 1; continue
        if p["require_sma200"] and not (c > sma200):
            i += 1; continue
        r10 = (c - closes[i - 10]) / closes[i - 10] if closes[i - 10] else 0.0
        r20 = (c - closes[i - 20]) / closes[i - 20] if closes[i - 20] else 0.0
        atr = _atr(highs[:i + 1], lows[:i + 1], closes[:i + 1], ATR_PERIOD)
        rsi = _rsi(closes[:i + 1], 14)
        if p["rsi_ceiling"] and rsi > p["rsi_ceiling"]:
            i += 1; continue
        score = swing_score(SwingInputs(close=c, sma50=sma50, sma200=sma200, rsi14=rsi,
                                        atr14=atr, ret_5d=r5, avg_dollar_volume=adv,
                                        ret_10d=r10, ret_20d=r20))
        if score < p["min_score"]:
            i += 1; continue
        if p["use_regime"] and not regime_on.get(bars[i]["date"], True):
            i += 1; continue
        entry = bars[i + 1]["open"]
        if entry <= 0 or atr <= 0:
            i += 1; continue
        stop = entry - p["atr_mult"] * atr
        target = entry + p["target_mult"] * (entry - stop)
        ex = reason = ei = None
        for j in range(i + 1, min(i + 1 + p["max_hold"], n)):
            if bars[j]["low"] <= stop:
                ex, reason, ei = stop, "stop", j; break
            if bars[j]["high"] >= target:
                ex, reason, ei = target, "target", j; break
        if ex is None:
            ei = min(i + p["max_hold"], n - 1)
            ex, reason = bars[ei]["close"], "maxhold"
        pnl = (ex * (1 - SLIPPAGE) - entry * (1 + SLIPPAGE)) / entry
        trades.append(Trade(ticker, bars[i + 1]["date"], bars[ei]["date"], round(entry, 2),
                            round(ex, 2), round(pnl, 4), ei - (i + 1), score, reason))
        i = ei + 1
    return trades


def base(**kw):
    p = dict(min_score=7.0, atr_mult=1.5, target_mult=2.0, require_sma200=False,
             use_regime=False, rsi_ceiling=None, max_hold=30)
    p.update(kw)
    return p


VARIANTS = [
    ("baseline", base()),
    ("regime", base(use_regime=True)),
    ("regime+sma200", base(use_regime=True, require_sma200=True)),
    ("regime+stop2.0", base(use_regime=True, atr_mult=2.0)),
    ("regime+stop2.0+tgt2.5", base(use_regime=True, atr_mult=2.0, target_mult=2.5)),
    ("regime+sma200+stop2.0+tgt2.5", base(use_regime=True, require_sma200=True, atr_mult=2.0, target_mult=2.5)),
    ("regime+score8.5", base(use_regime=True, min_score=8.5)),
    ("regime+sma200+stop2.0+rsi70", base(use_regime=True, require_sma200=True, atr_mult=2.0, rsi_ceiling=70)),
]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--years", type=int, default=2)
    a = ap.parse_args(argv)

    tickers = get_universe()
    print(f"Downloading {len(tickers)} + SPY, {a.years}y...")
    bars_by_ticker = load_bars(tickers, a.years)
    spy = load_bars(["SPY"], a.years).get("SPY", [])
    regime_on = regime_map(spy)
    on = sum(1 for v in regime_on.values() if v)
    tot = max(1, len(regime_on))
    print(f"Loaded {len(bars_by_ticker)} tickers. SPY risk-on {on}/{tot} days ({on/tot:.0%}).\n")

    print(f"{'variant':<32}{'trades':>7}{'win%':>6}{'exp/tr':>8}{'PF':>6}{'seqDD':>7}{'hold':>6}")
    print("-" * 72)
    for name, p in VARIANTS:
        trades = []
        for t, bars in bars_by_ticker.items():
            trades += simulate(t, bars, p, regime_on)
        s = summarize(trades)
        if s.get("trades", 0) == 0:
            print(f"{name:<32}{0:>7}")
            continue
        pf = s["profit_factor"]
        pf = pf if pf == "inf" else f"{pf:.2f}"
        print(f"{name:<32}{s['trades']:>7}{s['win_rate']*100:>5.0f}%{s['expectancy_pct']*100:>7.2f}%"
              f"{pf:>6}{s['seq_max_drawdown']*100:>6.0f}%{s['avg_hold_days']:>5.0f}d")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
