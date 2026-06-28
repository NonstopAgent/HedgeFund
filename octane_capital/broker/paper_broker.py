"""
Octane Capital Lab - Paper Broker (drop-in replacement)
Simulates cash/positions/fills with REAL prices and a working loss tracker.

Audit fixes:
  #1  no more $100 default — price comes from injected MarketData or set_price();
      a missing price raises instead of faking a fill.
  #2  records an equity snapshot each portfolio_context() call and derives the
      daily/weekly loss pcts the RiskEngine checks, so the breakers actually fire.
"""

import json
import uuid
from pathlib import Path
from typing import Dict, List, Optional

from octane_capital.config import config
from octane_capital.models import (
    AccountSnapshot,
    PositionSnapshot,
    OrderRequest,
    OrderPreview,
    TradeResult,
    TradeAction,
    TradingMode,
    PortfolioContext,
)
from octane_capital.risk.loss_tracker import compute_loss_pcts, record_day_open

DEFAULT_SLIPPAGE_PCT = 0.001


class PaperBroker:
    def __init__(
        self,
        state_path: Optional[Path] = None,
        prices: Optional[Dict[str, float]] = None,
        market_data=None,
    ):
        self.state_path = state_path or Path(".data/paper_broker.json")
        self.prices = {k.upper(): v for k, v in (prices or {}).items()}
        self.market_data = market_data
        self._state = self._load_state()

    def _load_state(self) -> dict:
        if self.state_path.exists():
            return json.loads(self.state_path.read_text())
        return {"cash": config.STARTING_PAPER_CASH, "positions": {}, "orders": [],
                "equity_history": []}

    def _save_state(self) -> None:
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.state_path.write_text(json.dumps(self._state, indent=2, default=str))

    def set_price(self, ticker: str, price: float) -> None:
        self.prices[ticker.upper()] = price

    def _get_price(self, ticker: str) -> float:
        t = ticker.upper()
        if t in self.prices:
            return self.prices[t]
        if self.market_data is not None:
            price = self.market_data.get_price(t)
            self.prices[t] = price
            return price
        raise ValueError(
            f"no price for {t}: inject MarketData or call set_price() — never fake a price"
        )

    def get_account(self) -> AccountSnapshot:
        positions_value = sum(
            pos["quantity"] * self._get_price(ticker)
            for ticker, pos in self._state["positions"].items()
        )
        cash = float(self._state["cash"])
        return AccountSnapshot(cash=cash, equity=cash + positions_value, buying_power=cash)

    def get_positions(self) -> List[PositionSnapshot]:
        out = []
        for ticker, pos in self._state["positions"].items():
            price = self._get_price(ticker)
            out.append(PositionSnapshot(
                ticker=ticker, quantity=pos["quantity"],
                average_cost=pos["average_cost"], market_value=pos["quantity"] * price,
            ))
        return out

    def preview_order(self, order: OrderRequest) -> OrderPreview:
        price = self._get_price(order.ticker)
        notional = order.notional or (order.quantity or 0) * price
        quantity = (notional / price) if (order.notional and not order.quantity) else (order.quantity or 0.0)
        warnings = []
        if order.action == TradeAction.BUY and notional > self._state["cash"]:
            warnings.append("insufficient cash")
        return OrderPreview(
            ticker=order.ticker, action=order.action, estimated_quantity=quantity,
            estimated_notional=notional, estimated_price=price, warnings=warnings,
        )

    def place_order(self, order: OrderRequest) -> TradeResult:
        if order.dry_run:
            return TradeResult(
                proposal_id=order.proposal_id, broker="paper", mode=TradingMode.PAPER,
                submitted=False, ticker=order.ticker, action=order.action,
                notional=order.notional, error="dry_run=true",
            )

        preview = self.preview_order(order)
        if preview.warnings:
            return TradeResult(
                proposal_id=order.proposal_id, broker="paper", mode=TradingMode.PAPER,
                submitted=False, ticker=order.ticker, action=order.action,
                notional=order.notional, error="; ".join(preview.warnings),
            )

        price = preview.estimated_price * (1 + DEFAULT_SLIPPAGE_PCT)
        ticker = order.ticker.upper()
        positions = self._state["positions"]

        if order.action == TradeAction.BUY:
            cost = preview.estimated_notional * (1 + DEFAULT_SLIPPAGE_PCT)
            if cost > self._state["cash"]:
                return TradeResult(
                    proposal_id=order.proposal_id, broker="paper", mode=TradingMode.PAPER,
                    submitted=False, ticker=ticker, action=order.action,
                    notional=order.notional, error="insufficient cash",
                )
            self._state["cash"] -= cost
            existing = positions.get(ticker, {"quantity": 0.0, "average_cost": 0.0})
            total_qty = existing["quantity"] + preview.estimated_quantity
            avg_cost = (
                (existing["quantity"] * existing["average_cost"]
                 + preview.estimated_quantity * price) / total_qty
                if total_qty > 0 else price
            )
            positions[ticker] = {"quantity": total_qty, "average_cost": avg_cost}

        elif order.action in (TradeAction.SELL, TradeAction.EXIT, TradeAction.TRIM):
            existing = positions.get(ticker)
            if not existing or existing["quantity"] <= 0:
                return TradeResult(
                    proposal_id=order.proposal_id, broker="paper", mode=TradingMode.PAPER,
                    submitted=False, ticker=ticker, action=order.action,
                    notional=order.notional, error="no position to sell",
                )
            sell_qty = min(preview.estimated_quantity or existing["quantity"], existing["quantity"])
            self._state["cash"] += sell_qty * price
            remaining = existing["quantity"] - sell_qty
            if remaining <= 1e-9:
                del positions[ticker]
            else:
                positions[ticker] = {"quantity": remaining, "average_cost": existing["average_cost"]}

        result = TradeResult(
            proposal_id=order.proposal_id, broker="paper", mode=TradingMode.PAPER,
            submitted=True, ticker=ticker, action=order.action, notional=order.notional,
            broker_order_id=str(uuid.uuid4()), filled_quantity=preview.estimated_quantity,
            average_fill_price=price,
        )
        self._state["orders"].append(result.model_dump(mode="json"))
        self._save_state()
        return result

    def portfolio_context(self) -> PortfolioContext:
        account = self.get_account()
        hist = self._state.setdefault("equity_history", [])
        record_day_open(hist, account.equity)
        self._save_state()
        daily, weekly = compute_loss_pcts(hist, account.equity)
        return PortfolioContext(
            account_equity=account.equity,
            daily_loss_pct=daily,
            weekly_loss_pct=weekly,
            open_positions=len(self.get_positions()),
        )
