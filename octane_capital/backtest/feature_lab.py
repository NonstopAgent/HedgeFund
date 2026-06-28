"""
Octane Capital Lab - Feature lab.
For every gate-passing swing setup over the universe, log entry-time features
plus the realized outcome (using the refined 2.0xATR stop / 2.5R target exits),
then report which features actually predict winners. Drives the score rebuild.

    python -m octane_capital.backtest.feature_lab --years 2
"""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

from octane_capital.data.universe import get_universe
from octane_capital.strategies.scoring import SwingInputs, swing_score
from octane_capital.backtest.walk_forward import (
    _sma, _atr, _rsi, load_bars, MIN_PRICE, MIN_ADV, ATR_PERIOD, SLIPPAGE,
)

ATR_MULT = 2.0
TARGET_R = 2.5
MAX_HOLD = 30


def _ret(closes, i, k):
    p = closes[i - k]
    return (closes[i] - p) / p if p else 0.0


def collect(ticker, bars):
    rows = []
    n = len(bars)
    closes = [b["close"] for b in bars]
    highs = [b["high"] for b in bars]
    lows = [b["low"] for b in bars]
    vols = [b["volume"] for b in bars]
    i = 252
    while i < n - 1:
        c = closes[i]
        sma50 = _sma(closes[:i + 1], 50)
        sma200 = _sma(closes[:i + 1], 200)
        adv = sum(closes[k] * vols[k] for k in range(i - 19, i + 1)) / 20
        if c < MIN_PRICE or adv < MIN_ADV:
            i += 1; continue
        r5 = _ret(closes, i, 5)
        if not (c > sma50 and r5 > 0):  # base gate
            i += 1; continue
        atr = _atr(highs[:i + 1], lows[:i + 1], closes[:i + 1], ATR_PERIOD)
        rsi = _rsi(closes[:i + 1], 14)
        feat = {
            "ext50": c / sma50 - 1,
            "ext200": c / sma200 - 1,
            "slope": sma50 / sma200 - 1,
            "r5": r5,
            "r10": _ret(closes, i, 10),
            "r20": _ret(closes, i, 20),
            "rsi": rsi,
            "atr_pct": atr / c if c else 0.0,
            "near_high": c / max(highs[i - 251:i + 1]),
            "score": swing_score(SwingInputs(close=c, sma50=sma50, sma200=sma200, rsi14=rsi,
                                             atr14=atr, ret_5d=r5, avg_dollar_volume=adv)),
        }
        entry = bars[i + 1]["open"]
        if entry <= 0 or atr <= 0:
            i += 1; continue
        stop = entry - ATR_MULT * atr
        target = entry + TARGET_R * (entry - stop)
        ex = ei = None
        for j in range(i + 1, min(i + 1 + MAX_HOLD, n)):
            if bars[j]["low"] <= stop:
                ex, ei = stop, j; break
            if bars[j]["high"] >= target:
                ex, ei = target, j; break
        if ex is None:
            ei = min(i + MAX_HOLD, n - 1)
            ex = bars[ei]["close"]
        pnl = (ex * (1 - SLIPPAGE) - entry * (1 + SLIPPAGE)) / entry
        feat["pnl"] = pnl
        feat["win"] = 1 if pnl > 0 else 0
        rows.append(feat)
        i = ei + 1
    return rows


def quintiles(rows, key):
    vals = sorted(rows, key=lambda r: r[key])
    n = len(vals)
    q = max(1, n // 5)
    out = []
    for b in range(5):
        seg = vals[b * q:(b + 1) * q] if b < 4 else vals[4 * q:]
        if not seg:
            continue
        wr = sum(r["win"] for r in seg) / len(seg)
        avg = statistics.mean(r["pnl"] for r in seg)
        out.append((wr, avg))
    return out


def corr(rows, key):
    xs = [r[key] for r in rows]
    ys = [r["pnl"] for r in rows]
    mx, my = statistics.mean(xs), statistics.mean(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = sum((x - mx) ** 2 for x in xs) ** 0.5
    dy = sum((y - my) ** 2 for y in ys) ** 0.5
    return num / (dx * dy) if dx * dy else 0.0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--years", type=int, default=2)
    a = ap.parse_args(argv)

    tickers = get_universe()
    print(f"Downloading {len(tickers)} {a.years}y...")
    bars = load_bars(tickers, a.years)
    rows = []
    for t, b in bars.items():
        rows += collect(t, b)
    if not rows:
        print("no rows")
        return 0
    base_wr = sum(r["win"] for r in rows) / len(rows)
    base_avg = statistics.mean(r["pnl"] for r in rows)
    print(f"{len(rows)} setups | base win {base_wr:.0%}, base avg pnl {base_avg:+.2%}\n")

    feats = ["ext50", "ext200", "slope", "r5", "r10", "r20", "rsi", "atr_pct", "near_high", "score"]
    print(f"{'feature':<10}{'corr':>8}   win% by quintile (low->high)      avg pnl by quintile")
    print("-" * 86)
    for f in feats:
        c = corr(rows, f)
        qa = quintiles(rows, f)
        wins = " ".join(f"{w:4.0%}" for w, _ in qa)
        avgs = " ".join(f"{a_:+5.1%}" for _, a_ in qa)
        print(f"{f:<10}{c:>+8.3f}   {wins}     {avgs}")

    Path(".data").mkdir(exist_ok=True)
    Path(".data/feature_rows.json").write_text(json.dumps(rows))
    print(f"\nSaved {len(rows)} feature rows to .data/feature_rows.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
