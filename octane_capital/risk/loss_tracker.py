"""
Octane Capital Lab - Loss tracking
Fixes the daily/weekly loss circuit-breakers (which previously read values
nothing computed).

Design: record the OPENING equity for each day once (never overwritten), then
compare live equity against the day's / week's open to get the drawdown the
RiskEngine checks. Works for the paper broker's state and a live account
snapshot alike.
"""

from __future__ import annotations

from datetime import date, timedelta


def record_day_open(equity_history: list[dict], equity: float) -> list[dict]:
    """Record today's OPENING equity exactly once; do not overwrite intraday."""
    today = str(date.today())
    if not any(s["date"] == today for s in equity_history):
        equity_history.append({"date": today, "equity": float(equity)})
    return equity_history


def compute_loss_pcts(equity_history: list[dict], current_equity: float) -> tuple[float, float]:
    """Return (daily_loss_pct, weekly_loss_pct) as POSITIVE fractions.

    daily  = drawdown from today's opening equity to current_equity.
    weekly = drawdown from the first opening equity in the last 7 days to current.
    Returns 0.0 when there isn't enough history (fail-safe: no false breaker).
    """
    if not equity_history:
        return 0.0, 0.0

    today = date.today()
    week_ago = today - timedelta(days=7)

    day_open = float(current_equity)
    for s in equity_history:
        if s["date"] == str(today):
            day_open = float(s["equity"])
            break

    week_open = float(current_equity)
    for s in equity_history:
        if s["date"] >= str(week_ago):
            week_open = float(s["equity"])
            break

    daily = max(0.0, (day_open - current_equity) / day_open) if day_open > 0 else 0.0
    weekly = max(0.0, (week_open - current_equity) / week_open) if week_open > 0 else 0.0
    return round(daily, 4), round(weekly, 4)
