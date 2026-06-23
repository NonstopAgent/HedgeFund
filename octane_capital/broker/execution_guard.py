"""
Octane Capital Lab - Execution Guard
Final gate before any live order reaches a broker.
"""

from dataclasses import dataclass

from octane_capital.config import config
from octane_capital.models import (
    TradeProposal,
    RiskDecision,
    OrderRequest,
    ProposalStatus,
    TradingMode,
)


@dataclass
class Authorization:
    authorized: bool
    reason: str


class ExecutionGuard:
    """Authorize or block orders based on mode, config, and risk decisions."""

    def __init__(self, cfg=None):
        self.config = cfg or config
        self._submitted_proposals: set[str] = set()

    def authorize_order(
        self,
        proposal: TradeProposal,
        risk_decision: RiskDecision,
        order: OrderRequest,
    ) -> Authorization:
        if self.config.TRADING_MODE in (
            TradingMode.RESEARCH.value,
            TradingMode.PAPER.value,
            TradingMode.PROPOSAL.value,
        ):
            if not order.dry_run and self.config.TRADING_MODE != TradingMode.PAPER.value:
                return Authorization(False, "Live execution disabled in this mode")

        if not order.dry_run and not self.config.ENABLE_LIVE_TRADING:
            return Authorization(False, "ENABLE_LIVE_TRADING=false")

        if (
            not order.dry_run
            and self.config.REQUIRE_HUMAN_APPROVAL
            and proposal.status != ProposalStatus.APPROVED
        ):
            return Authorization(False, "Human approval required")

        if not risk_decision.approved:
            return Authorization(False, "Risk engine rejected proposal")

        if proposal.id in self._submitted_proposals and not order.dry_run:
            return Authorization(False, "Duplicate order prevention")

        if order.notional and order.notional > self.config.MAX_SINGLE_TRADE_DOLLARS:
            return Authorization(False, "Order notional exceeds limit")

        if not order.dry_run:
            self._submitted_proposals.add(proposal.id)

        return Authorization(True, "Authorized")
