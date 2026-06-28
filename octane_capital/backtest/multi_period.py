"""
Multi-period robustness test of the refined config (v2 score, regime + stacked
uptrend + 2.0xATR stop + 2.5R target) across long horizons, with a per-calendar-
year breakdown to expose regime behavior.

CAVEAT: the universe is today's survivors, so longer windows are increasingly
survivorship-biased and OPTIMISTIC. Read long-horizon numbers as a ceiling.

    python -m octane_capital.backtest.multi_period --period 5y
    python -m octane_capital.backtest.multi_period --period 10y
    python -m octane_capital.backtest.multi_period --period max
"""

from __future__ import annotations

import argparse
import statistics

import yfinance as yf

from octane_capital.data.universe import get_universe
from octane_capital.backtest.refine import simulate, base, regime_map
from octane_capital.backtest.walk_forward import summarize


def load(tickers, period):
    raw = yf.download(tickers, period=period, interval="1d", auto_adjust=True,
                      group_by="ticker", progress=False, threads=True)
    out = {}
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


def seq_mult(trades, frac=0.20):
    eq = 1.0
    for tr in sorted(trades, key=lambda x: x.entry_date):
        eq *= (1 + frac * tr.pnl_pct)
    return eq


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--period", default="5y")
    a = ap.parse_args(argv)

    P = base(use_regime=True, require_sma200=True, atr_mult=2.0, target_mult=2.5)
    uni = get_universe()
    print(f"Loading {len(uni)} tickers + SPY, period={a.period}...")
    bt = load(uni, a.period)
    spy = load(["SPY"], a.period).get("SPY", [])
    regime = regime_map(spy)

    trades = []
    for t, bars in bt.items():
        trades += simulate(t, bars, P, regime)
    if not trades:
        print("no trades")
        return 0

    s = summarize(trades)
    dates = sorted(x.entry_date for x in trades)
    print(f"\nperiod={a.period} | {len(bt)} tickers w/ data | span {dates[0]}..{dates[-1]}")
    print(f"  trades={s['trades']}  win={s['win_rate']:.0%}  exp/tr={s['expectancy_pct']:+.2%}  "
          f"PF={s['profit_factor']}  maxDD(20%seq)={s['seq_max_drawdown']:.0%}")

    by = {}
    for tr in trades:
        by.setdefault(tr.entry_date[:4], []).append(tr)
    print(f"\n  {'year':<6}{'n':>5}{'win%':>6}{'exp/tr':>9}{'yr mult(20%seq)':>17}")
    for yr in sorted(by):
        ts = by[yr]
        wr = sum(1 for x in ts if x.pnl_pct > 0) / len(ts)
        avg = statistics.mean(x.pnl_pct for x in ts)
        m = seq_mult(ts)
        flag = "  <-- losing year" if m < 1.0 else ""
        print(f"  {yr:<6}{len(ts):>5}{wr*100:>5.0f}%{avg*100:>8.2f}%{m:>14.2f}x{flag}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
