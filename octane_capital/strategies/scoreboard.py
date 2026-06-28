"""
Octane Capital Lab - Strategy scoreboard / learning loop
The "memory of its own mistakes." After trades are graded, aggregate per
strategy and emit a trust multiplier that the RiskEngine applies to size.

Key safety property: the multiplier can only ever SHRINK a position (<= 1.0),
never grow it. A strategy that keeps losing literally loses its allowance.
"""

from __future__ import annotations

from dataclasses import dataclass
from statistics import mean


@dataclass
class StrategyStats:
    strategy: str
    n: int
    win_rate: float
    avg_pnl_pct: float
    profit_factor: float


def summarize(grades: list[dict], strategy: str) -> StrategyStats:
    """grades: list of dicts with at least {"pnl_pct": float} for this strategy."""
    pnls = [float(g["pnl_pct"]) for g in grades]
    wins = [p for p in pnls if p > 0]
    losses = [-p for p in pnls if p < 0]
    if losses:
        pf = sum(wins) / sum(losses)
    else:
        pf = float("inf") if wins else 0.0
    return StrategyStats(
        strategy=strategy,
        n=len(pnls),
        win_rate=(len(wins) / len(pnls)) if pnls else 0.0,
        avg_pnl_pct=mean(pnls) if pnls else 0.0,
        profit_factor=pf,
    )


def trust_multiplier(stats: StrategyStats) -> float:
    """Scale a strategy's position size by its proven record. Never > 1.0."""
    if stats.n < 10:
        return 0.5                                   # not enough evidence -> half size
    if stats.profit_factor < 1.0 or stats.avg_pnl_pct <= 0:
        return 0.25                                  # losing -> quarter size + review
    return min(1.0, 0.5 + (stats.profit_factor - 1.0) * 0.5)


def trust_for(grades_by_strategy: dict[str, list[dict]], strategy: str) -> float:
    """Convenience: compute the multiplier for one strategy from graded history."""
    grades = grades_by_strategy.get(strategy, [])
    return trust_multiplier(summarize(grades, strategy))
