"""
Octane Capital Lab - Backtest Engine
Simple daily-close simulation with transaction costs and slippage.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from octane_capital.config import config
from octane_capital.models import BacktestResult, TradeAction
from octane_capital.risk import RiskEngine
from octane_capital.backtest.metrics import compute_metrics


@dataclass
class SimulatedTrade:
    ticker: str
    entry_price: float
    exit_price: float
    quantity: float
    hold_days: int
    pnl_pct: float


class BacktestEngine:
    """Daily-close backtest with conservative cost assumptions."""

    def __init__(
        self,
        transaction_cost_pct: float = 0.001,
        slippage_pct: float = 0.001,
    ):
        self.transaction_cost_pct = transaction_cost_pct
        self.slippage_pct = slippage_pct
        self.risk_engine = RiskEngine()

    def run(
        self,
        signals: List[dict],
        historical_data: Dict[str, List[dict]],
        starting_cash: float,
        min_confidence: float = 7.5,
    ) -> BacktestResult:
        """
        Run backtest over historical daily bars.

        historical_data: {ticker: [{"date": "...", "close": float}, ...]}
        signals: [{"ticker": str, "confidence": float, "entry_idx": int, "hold_days": int}, ...]
        """
        cash = starting_cash
        equity_curve = [cash]
        trade_pnls: list[float] = []
        hold_days_list: list[float] = []
        simulated: list[SimulatedTrade] = []

        for signal in signals:
            ticker = signal["ticker"].upper()
            bars = historical_data.get(ticker, [])
            entry_idx = signal.get("entry_idx", 0)
            hold = signal.get("hold_days", 20)
            confidence = signal.get("confidence", 0.0)

            if confidence < min_confidence or entry_idx >= len(bars):
                continue

            exit_idx = min(entry_idx + hold, len(bars) - 1)
            entry_price = bars[entry_idx]["close"] * (1 + self.slippage_pct)
            exit_price = bars[exit_idx]["close"] * (1 - self.slippage_pct)

            max_notional = min(
                cash * config.MAX_POSITION_PCT,
                config.MAX_SINGLE_TRADE_DOLLARS,
            )
            if max_notional <= 0:
                continue

            cost = max_notional * self.transaction_cost_pct
            quantity = (max_notional - cost) / entry_price
            pnl = (exit_price - entry_price) * quantity - cost * 2
            pnl_pct = pnl / max_notional if max_notional else 0.0

            cash += pnl
            equity_curve.append(cash)
            trade_pnls.append(pnl_pct)
            hold_days_list.append(float(exit_idx - entry_idx))
            simulated.append(
                SimulatedTrade(
                    ticker=ticker,
                    entry_price=entry_price,
                    exit_price=exit_price,
                    quantity=quantity,
                    hold_days=exit_idx - entry_idx,
                    pnl_pct=pnl_pct,
                )
            )

        return compute_metrics(equity_curve, trade_pnls, hold_days_list)
