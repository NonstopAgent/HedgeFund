"""
Octane Capital Lab - Execution Guard (drop-in replacement)
Final gate before any live order reaches a broker.

Audit fix #3: duplicate prevention is now DURABLE. The caller passes
`already_executed` (computed from the Vault: proposal.status == EXECUTED or an
existing order row), so a second `execute --live` in a fresh process is blocked.
Also requires a notional on live orders so the dollar cap can't be skipped.
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
    def __init__(self, cfg=None):
        self.config = cfg or config
        self._submitted_proposals: set[str] = set()  # in-process backup only

    def authorize_order(
        self,
        proposal: TradeProposal,
        risk_decision: RiskDecision,
        order: OrderRequest,
        *,
        already_executed: bool = False,
    ) -> Authorization:
        cfg = self.config
        live = not order.dry_run

        # Mode gating.
        if cfg.TRADING_MODE in (
            TradingMode.RESEARCH.value,
            TradingMode.PROPOSAL.value,
        ) and live:
            return Authorization(False, "Live execution disabled in this mode")

        if live and not cfg.ENABLE_LIVE_TRADING:
            return Authorization(False, "ENABLE_LIVE_TRADING=false")

        if live and cfg.REQUIRE_HUMAN_APPROVAL and proposal.status != ProposalStatus.APPROVED:
            return Authorization(False, "Human approval required")

        if not risk_decision.approved:
            return Authorization(False, "Risk engine rejected proposal")

        # Durable duplicate prevention.
        if live and (already_executed or proposal.id in self._submitted_proposals):
            return Authorization(False, "Duplicate order prevention (already executed)")

        # Dollar cap — require an explicit notional on live orders.
        if live:
            if order.notional is None:
                return Authorization(False, "Live order missing notional — cannot verify cap")
            if order.notional > cfg.MAX_SINGLE_TRADE_DOLLARS + 1e-9:
                return Authorization(False, "Order notional exceeds MAX_SINGLE_TRADE_DOLLARS")

        if live:
            self._submitted_proposals.add(proposal.id)

        return Authorization(True, "Authorized")
