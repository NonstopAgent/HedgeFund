"""
Octane Capital Lab - Robinhood MCP Broker (stub)
Wraps Robinhood Trading MCP behind BrokerAdapter.

Claude Code MCP setup:
    claude mcp add robinhood-trading --transport http https://agent.robinhood.com/mcp/trading

Direct MCP calls from Python may not be available at runtime; this adapter
raises unless live trading is explicitly enabled and ExecutionGuard authorizes.
"""

from typing import List

from octane_capital.config import config
from octane_capital.models import (
    AccountSnapshot,
    PositionSnapshot,
    OrderRequest,
    OrderPreview,
    TradeResult,
    TradingMode,
)
from octane_capital.broker.execution_guard import ExecutionGuard, Authorization


class RobinhoodMCPBroker:
    """Stub broker adapter for Robinhood Agentic Trading MCP."""

    def __init__(self, guard: ExecutionGuard | None = None):
        self.guard = guard or ExecutionGuard()
        self.mcp_server = config.ROBINHOOD_MCP_SERVER

    def get_account(self) -> AccountSnapshot:
        raise NotImplementedError(
            "Robinhood MCP get_account requires authenticated MCP session. "
            f"Configure MCP server: {self.mcp_server}"
        )

    def get_positions(self) -> List[PositionSnapshot]:
        raise NotImplementedError(
            "Robinhood MCP get_positions requires authenticated MCP session."
        )

    def preview_order(self, order: OrderRequest) -> OrderPreview:
        return OrderPreview(
            ticker=order.ticker,
            action=order.action,
            estimated_quantity=order.quantity or 0.0,
            estimated_notional=order.notional or 0.0,
            estimated_price=0.0,
            warnings=["Robinhood MCP preview is a stub — no live price available"],
        )

    def place_order(
        self,
        order: OrderRequest,
        proposal=None,
        risk_decision=None,
    ) -> TradeResult:
        if proposal and risk_decision:
            auth = self.guard.authorize_order(proposal, risk_decision, order)
            if not auth.authorized:
                return TradeResult(
                    proposal_id=order.proposal_id,
                    broker="robinhood_mcp",
                    mode=TradingMode(config.TRADING_MODE),
                    submitted=False,
                    error=auth.reason,
                )

        if not config.ENABLE_LIVE_TRADING:
            return TradeResult(
                proposal_id=order.proposal_id,
                broker="robinhood_mcp",
                mode=TradingMode(config.TRADING_MODE),
                submitted=False,
                error="ENABLE_LIVE_TRADING=false — Robinhood execution blocked",
            )

        return TradeResult(
            proposal_id=order.proposal_id,
            broker="robinhood_mcp",
            mode=TradingMode(config.TRADING_MODE),
            submitted=False,
            error="Robinhood MCP place_order is a stub — connect MCP session manually",
        )
