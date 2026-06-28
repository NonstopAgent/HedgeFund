"""Order construction from approved proposals (drop-in replacement).

Audit fix #1: a real price is now REQUIRED. No $100 default — a missing price
raises instead of silently faking the trade. Carries the ATR stop through.
"""

from octane_capital.models import TradeProposal, OrderRequest, RiskDecision


def order_from_proposal(
    proposal: TradeProposal,
    risk_decision: RiskDecision,
    *,
    dry_run: bool = True,
    price: float,
) -> OrderRequest:
    if price is None or price <= 0:
        raise ValueError(
            "order_from_proposal requires a real price > 0 (no fake default). "
            "Fetch it from MarketData (paper) or the Robinhood MCP quote (live)."
        )

    notional = risk_decision.adjusted_notional
    if notional is None:
        notional = proposal.requested_notional
    if not notional or notional <= 0:
        raise ValueError("no sized notional available for order")

    quantity = notional / price
    return OrderRequest(
        proposal_id=proposal.id,
        ticker=proposal.ticker,
        action=proposal.action,
        quantity=quantity,
        notional=notional,
        dry_run=dry_run,
        stop_price=proposal.stop_price,
    )
