"""
Octane Capital Lab - Walk-forward backtest / data engine.

Runs the swing strategy over a broad universe and ~N years of daily bars to
generate a large sample of GRADED trades for strategy refinement and learning.

No lookahead: a signal at day t uses only bars[:t+1]; the entry fills at
bars[t+1].open. Exits use later bars' high/low vs an ATR stop / 2R target /
max-hold. This is a SIGNAL-QUALITY backtest (every signal taken, fixed-fraction
sizing) — a first-pass edge check, not a capital-constrained portfolio sim.

Run:
    python -m octane_capital.backtest.walk_forward --years 2
"""

from __future__ import annotations

import argparse
import json
import statistics
from dataclasses import dataclass, asdict
from pathlib import Path

import yfinance as yf

from octane_capital.strategies.scoring import SwingInputs, swing_score
from octane_capital.data.universe import get_universe

SLIPPAGE = 0.001
MIN_PRICE = 5.0
MIN_ADV = 20_000_000.0
ATR_PERIOD = 14
ATR_MULT = 1.5
MAX_HOLD = 30
ALLOC_FRACTION = 0.20  # for the sequential equity-curve approximation


@dataclass
class Trade:
    ticker: str
    entry_date: str
    exit_date: str
    entry: float
    exit: float
    pnl_pct: float
    hold_days: int
    score: float
    reason: str


def _sma(xs, n):
    return sum(xs[-n:]) / n


def _atr(highs, lows, closes, n):
    trs = []
    for i in range(1, len(highs)):
        trs.append(max(highs[i] - lows[i], abs(highs[i] - closes[i - 1]), abs(lows[i] - closes[i - 1])))
    return sum(trs[-n:]) / n


def _rsi(closes, n=14):
    gains, losses = [], []
    for i in range(1, len(closes)):
        ch = closes[i] - closes[i - 1]
        gains.append(max(ch, 0.0))
        losses.append(max(-ch, 0.0))
    ag = sum(gains[-n:]) / n
    al = sum(losses[-n:]) / n
    if al == 0:
        return 100.0
    return 100.0 - 100.0 / (1.0 + ag / al)


def simulate_ticker(ticker: str, bars: list[dict], min_score: float) -> list[Trade]:
    """bars ascending: dict(date,open,high,low,close,volume). No overlapping positions."""
    trades: list[Trade] = []
    n = len(bars)
    closes = [b["close"] for b in bars]
    highs = [b["high"] for b in bars]
    lows = [b["low"] for b in bars]
    vols = [b["volume"] for b in bars]

    i = 200  # need 200 bars for SMA200
    while i < n - 1:
        c = closes[i]
        sma50 = _sma(closes[: i + 1], 50)
        sma200 = _sma(closes[: i + 1], 200)
        adv = sum(closes[k] * vols[k] for k in range(i - 19, i + 1)) / 20
        if c < MIN_PRICE or adv < MIN_ADV:
            i += 1
            continue
        prior = closes[i - 5]
        r5 = (c - prior) / prior if prior else 0.0
        if not (c > sma50 and r5 > 0):
            i += 1
            continue
        atr = _atr(highs[: i + 1], lows[: i + 1], closes[: i + 1], ATR_PERIOD)
        rsi = _rsi(closes[: i + 1], 14)
        score = swing_score(SwingInputs(
            close=c, sma50=sma50, sma200=sma200, rsi14=rsi,
            atr14=atr, ret_5d=r5, avg_dollar_volume=adv,
        ))
        if score < min_score:
            i += 1
            continue

        entry = bars[i + 1]["open"]
        if entry <= 0 or atr <= 0:
            i += 1
            continue
        stop = entry - ATR_MULT * atr
        target = entry + 2 * (entry - stop)

        exit_price = None
        reason = None
        exit_idx = None
        for j in range(i + 1, min(i + 1 + MAX_HOLD, n)):
            if bars[j]["low"] <= stop:
                exit_price, reason, exit_idx = stop, "stop", j
                break
            if bars[j]["high"] >= target:
                exit_price, reason, exit_idx = target, "target", j
                break
        if exit_price is None:
            exit_idx = min(i + MAX_HOLD, n - 1)
            exit_price, reason = bars[exit_idx]["close"], "maxhold"

        pnl = (exit_price * (1 - SLIPPAGE) - entry * (1 + SLIPPAGE)) / entry
        trades.append(Trade(
            ticker=ticker, entry_date=bars[i + 1]["date"], exit_date=bars[exit_idx]["date"],
            entry=round(entry, 2), exit=round(exit_price, 2), pnl_pct=round(pnl, 4),
            hold_days=exit_idx - (i + 1), score=score, reason=reason,
        ))
        i = exit_idx + 1  # no overlapping positions on the same ticker
    return trades


def _max_drawdown(curve: list[float]) -> float:
    peak = curve[0] if curve else 1.0
    mdd = 0.0
    for v in curve:
        peak = max(peak, v)
        mdd = max(mdd, (peak - v) / peak if peak > 0 else 0.0)
    return mdd


def summarize(trades: list[Trade]) -> dict:
    if not trades:
        return {"trades": 0}
    pnls = [t.pnl_pct for t in trades]
    wins = [p for p in pnls if p > 0]
    losses = [-p for p in pnls if p < 0]
    pf = (sum(wins) / sum(losses)) if losses else float("inf")
    # sequential equity curve (order by entry date), allocate fixed fraction per trade
    ordered = sorted(trades, key=lambda t: t.entry_date)
    eq = 1.0
    curve = [eq]
    for t in ordered:
        eq *= (1 + ALLOC_FRACTION * t.pnl_pct)
        curve.append(eq)
    # score buckets
    buckets = {"6.5-7.0": [], "7.0-7.5": [], "7.5-8.0": [], "8.0-9.0": [], "9.0-10": []}
    for t in trades:
        s = t.score
        key = ("6.5-7.0" if s < 7.0 else "7.0-7.5" if s < 7.5 else
               "7.5-8.0" if s < 8.0 else "8.0-9.0" if s < 9.0 else "9.0-10")
        buckets[key].append(t.pnl_pct)
    bucket_stats = {
        k: {"n": len(v),
            "win_rate": round(sum(1 for p in v if p > 0) / len(v), 3) if v else 0,
            "avg_pnl": round(statistics.mean(v), 4) if v else 0}
        for k, v in buckets.items()
    }
    reasons = {}
    for t in trades:
        reasons[t.reason] = reasons.get(t.reason, 0) + 1
    return {
        "trades": len(trades),
        "win_rate": round(len(wins) / len(pnls), 3),
        "avg_win_pct": round(statistics.mean(wins), 4) if wins else 0,
        "avg_loss_pct": round(-statistics.mean(losses), 4) if losses else 0,
        "expectancy_pct": round(statistics.mean(pnls), 4),
        "profit_factor": round(pf, 2) if pf != float("inf") else "inf",
        "avg_hold_days": round(statistics.mean([t.hold_days for t in trades]), 1),
        "exit_reasons": reasons,
        "seq_equity_mult": round(curve[-1], 3),
        "seq_max_drawdown": round(_max_drawdown(curve), 3),
        "by_score": bucket_stats,
    }


def load_bars(tickers: list[str], years: int) -> dict[str, list[dict]]:
    raw = yf.download(tickers, period=f"{years}y", interval="1d", auto_adjust=True,
                      group_by="ticker", progress=False, threads=True)
    out: dict[str, list[dict]] = {}
    for t in tickers:
        try:
            sub = raw[t].dropna()
        except Exception:
            continue
        bars = [{"date": str(idx.date()), "open": float(r["Open"]), "high": float(r["High"]),
                 "low": float(r["Low"]), "close": float(r["Close"]), "volume": float(r["Volume"])}
                for idx, r in sub.iterrows()]
        if len(bars) >= 210:
            out[t] = bars
    return out


def run(years: int = 2, thresholds=(6.5, 7.0, 7.5), tickers=None) -> dict:
    tickers = tickers or get_universe()
    print(f"Downloading {len(tickers)} tickers, {years}y daily bars...")
    bars_by_ticker = load_bars(tickers, years)
    print(f"Loaded {len(bars_by_ticker)} tickers with enough history.\n")

    results = {}
    saved = None
    for thr in thresholds:
        all_trades = []
        for t, bars in bars_by_ticker.items():
            all_trades += simulate_ticker(t, bars, thr)
        stats = summarize(all_trades)
        results[thr] = stats
        if thr == 7.0:
            saved = all_trades
        print(f"=== min_score >= {thr} ===")
        if stats.get("trades", 0) == 0:
            print("  no trades\n")
            continue
        # trades per month
        dates = sorted(t.entry_date for t in all_trades)
        months = max(1, (int(dates[-1][:4]) * 12 + int(dates[-1][5:7])) -
                     (int(dates[0][:4]) * 12 + int(dates[0][5:7])) + 1)
        print(f"  trades={stats['trades']}  (~{stats['trades']/months:.1f}/mo across universe)")
        print(f"  win_rate={stats['win_rate']:.0%}  expectancy/trade={stats['expectancy_pct']:+.2%}  PF={stats['profit_factor']}")
        print(f"  avg_win={stats['avg_win_pct']:+.2%}  avg_loss={stats['avg_loss_pct']:+.2%}  avg_hold={stats['avg_hold_days']}d")
        print(f"  exits={stats['exit_reasons']}")
        print(f"  seq(20%/trade): x{stats['seq_equity_mult']}  maxDD={stats['seq_max_drawdown']:.0%}")
        print(f"  by score: " + "  ".join(
            f"{k}:n={v['n']},win={v['win_rate']:.0%},avg={v['avg_pnl']:+.1%}"
            for k, v in stats["by_score"].items() if v["n"] > 0))
        print()

    if saved is not None:
        out = Path(".data/backtest_trades.json")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps([asdict(t) for t in saved], indent=2))
        print(f"Saved {len(saved)} trades (min_score>=7.0) to {out}")
    return results


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Octane walk-forward backtest / data engine")
    p.add_argument("--years", type=int, default=2)
    p.add_argument("--tickers", default="", help="comma-separated; default = full universe")
    args = p.parse_args(argv)
    tickers = [t.strip().upper() for t in args.tickers.split(",") if t.strip()] or None
    run(years=args.years, tickers=tickers)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
