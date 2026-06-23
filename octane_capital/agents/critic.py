"""
Octane Capital Lab - Critic Agent
Reviews trade proposals for weak evidence, missing sources, and hype.
"""

from octane_capital.config import config
from octane_capital.models import TradeProposal, CriticReview, TradeAction
from octane_capital.branding import print_agent_status


def review_proposal(proposal: TradeProposal) -> CriticReview:
    """Deterministic critic — flags common proposal quality issues."""
    print_agent_status("THE CRITIC", "INITIALIZING", f"Reviewing {proposal.ticker}")

    concerns: list[str] = []
    changes: list[str] = []
    confidence_adj = 0.0

    if proposal.action == TradeAction.BUY and not proposal.source_urls:
        concerns.append("no source URLs cited")
        changes.append("add primary source URLs before live consideration")
        confidence_adj -= 0.5

    if len(proposal.evidence) < 2:
        concerns.append("fewer than 2 independent evidence items")
        changes.append("add more independent evidence")
        confidence_adj -= 0.5

    thesis_words = proposal.thesis.lower().split()
    hype_words = {"moon", "guaranteed", "sure", "can't lose", "rocket", "easy money"}
    if any(w in proposal.thesis.lower() for w in hype_words):
        concerns.append("hype-driven language detected")
        changes.append("rewrite thesis with evidence-based language")
        confidence_adj -= 1.0

    if proposal.action == TradeAction.BUY and proposal.confidence_score < 7.5:
        concerns.append("confidence below buy threshold")
        changes.append("consider HOLD until confidence improves")

    if proposal.requested_position_pct > config.MAX_POSITION_PCT:
        concerns.append("requested position exceeds max allowed")
        changes.append(f"reduce position to <= {config.MAX_POSITION_PCT}")

    if proposal.action == TradeAction.BUY and proposal.risk_level.lower() == "high":
        if proposal.confidence_score < 9.0:
            concerns.append("high risk without sufficient confidence")
            changes.append("raise confidence to 9+ or downgrade risk level")

    if proposal.action != TradeAction.HOLD and len(proposal.thesis) < 50:
        concerns.append("thesis may be too brief for the proposed action")
        changes.append("expand thesis with causal link to trade action")

    passed = len(concerns) == 0
    print_agent_status(
        "THE CRITIC",
        "COMPLETE" if passed else "WARNING",
        f"{proposal.ticker}: {'passed' if passed else f'{len(concerns)} concerns'}",
    )

    return CriticReview(
        passed=passed,
        concerns=concerns,
        recommended_changes=changes,
        confidence_adjustment=confidence_adj,
    )


def review_proposals(proposals: list[TradeProposal]) -> dict[str, CriticReview]:
    return {p.id: review_proposal(p) for p in proposals}
