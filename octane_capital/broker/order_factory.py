"""Order construction from approved proposals."""

from octane_capital.models import TradeProposal, OrderRequest, TradeAction, RiskDecision


def order_from_proposal(
    proposal: TradeProposal,
    risk_decision: RiskDecision,
    *,
    dry_run: bool = True,
    price: float = 100.0,
) -> OrderRequest:
    notional = risk_decision.adjusted_notional
    if notional is None:
        notional = proposal.requested_notional

    quantity = None
    if notional:
        quantity = notional / price

    return OrderRequest(
        proposal_id=proposal.id,
        ticker=proposal.ticker,
        action=proposal.action,
        quantity=quantity,
        notional=notional,
        dry_run=dry_run,
    )
