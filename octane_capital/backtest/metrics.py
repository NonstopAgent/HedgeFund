"""Backtest performance metrics."""

from typing import List

from octane_capital.models import BacktestResult


def compute_metrics(
    equity_curve: List[float],
    trade_pnls: List[float],
    hold_days: List[float],
    risk_free_rate: float = 0.0,
) -> BacktestResult:
    if not equity_curve:
        return BacktestResult(
            total_return_pct=0.0,
            max_drawdown_pct=0.0,
            win_rate=0.0,
            average_win_pct=0.0,
            average_loss_pct=0.0,
            profit_factor=0.0,
            sharpe_ratio=0.0,
            num_trades=0,
            average_hold_days=0.0,
        )

    start = equity_curve[0]
    end = equity_curve[-1]
    total_return_pct = ((end - start) / start * 100) if start else 0.0

    peak = equity_curve[0]
    max_dd = 0.0
    for value in equity_curve:
        peak = max(peak, value)
        dd = (peak - value) / peak if peak else 0.0
        max_dd = max(max_dd, dd)

    wins = [p for p in trade_pnls if p > 0]
    losses = [p for p in trade_pnls if p < 0]
    win_rate = len(wins) / len(trade_pnls) if trade_pnls else 0.0
    avg_win = sum(wins) / len(wins) if wins else 0.0
    avg_loss = sum(losses) / len(losses) if losses else 0.0
    gross_profit = sum(wins)
    gross_loss = abs(sum(losses))
    profit_factor = gross_profit / gross_loss if gross_loss else (gross_profit or 0.0)

    if len(equity_curve) > 1:
        returns = [
            (equity_curve[i] - equity_curve[i - 1]) / equity_curve[i - 1]
            for i in range(1, len(equity_curve))
            if equity_curve[i - 1]
        ]
        if returns:
            mean_ret = sum(returns) / len(returns)
            variance = sum((r - mean_ret) ** 2 for r in returns) / len(returns)
            std = variance ** 0.5
            sharpe = ((mean_ret - risk_free_rate / 252) / std * (252 ** 0.5)) if std else 0.0
        else:
            sharpe = 0.0
    else:
        sharpe = 0.0

    return BacktestResult(
        total_return_pct=total_return_pct,
        max_drawdown_pct=max_dd * 100,
        win_rate=win_rate * 100,
        average_win_pct=avg_win * 100,
        average_loss_pct=avg_loss * 100,
        profit_factor=profit_factor,
        sharpe_ratio=sharpe,
        num_trades=len(trade_pnls),
        average_hold_days=sum(hold_days) / len(hold_days) if hold_days else 0.0,
    )
