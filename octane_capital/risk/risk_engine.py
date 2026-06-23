"""
Octane Capital Lab - Deterministic Risk Engine
Claude cannot override these rules.
"""

from octane_capital.config import config
from octane_capital.models import (
    TradeProposal,
    RiskDecision,
    PortfolioContext,
    TradeAction,
    AssetClass,
    TradingMode,
    ProposalStatus,
)
from octane_capital.risk import position_sizing
from octane_capital.risk import rules


class RiskEngine:
    """Evaluate trade proposals against hard risk limits."""

    def __init__(self, cfg=None):
        self.config = cfg or config

    def evaluate(
        self,
        proposal: TradeProposal,
        portfolio: PortfolioContext,
        *,
        live_execution: bool = False,
    ) -> RiskDecision:
        reasons: list[str] = []

        if live_execution and not self.config.ENABLE_LIVE_TRADING:
            reasons.append("ENABLE_LIVE_TRADING=false")

        if self.config.TRADING_MODE == TradingMode.RESEARCH.value and live_execution:
            reasons.append("TRADING_MODE=research blocks order execution")

        if proposal.action == TradeAction.BUY and proposal.confidence_score < rules.MIN_CONFIDENCE_BUY:
            reasons.append(f"confidence {proposal.confidence_score} below minimum {rules.MIN_CONFIDENCE_BUY}")

        if not proposal.ticker or not proposal.ticker.strip():
            reasons.append("ticker is missing or invalid")

        if proposal.asset_class != AssetClass.EQUITY:
            reasons.append(f"asset_class {proposal.asset_class} not allowed")

        if proposal.asset_class == AssetClass.OPTION and not self.config.ALLOW_OPTIONS:
            reasons.append("options disabled")

        if proposal.asset_class == AssetClass.CRYPTO and not self.config.ALLOW_CRYPTO:
            reasons.append("crypto disabled")

        if proposal.action in (TradeAction.SELL, TradeAction.EXIT) and not self.config.ALLOW_SHORTS:
            pass  # selling existing long is allowed

        if proposal.exit_rules.stop_loss_pct is None:
            reasons.append("stop_loss_pct is missing")

        if proposal.requested_position_pct > self.config.MAX_POSITION_PCT:
            reasons.append(
                f"requested_position_pct {proposal.requested_position_pct} exceeds "
                f"MAX_POSITION_PCT {self.config.MAX_POSITION_PCT}"
            )

        if (
            proposal.requested_notional is not None
            and proposal.requested_notional > self.config.MAX_SINGLE_TRADE_DOLLARS
        ):
            reasons.append(
                f"requested_notional {proposal.requested_notional} exceeds "
                f"MAX_SINGLE_TRADE_DOLLARS {self.config.MAX_SINGLE_TRADE_DOLLARS}"
            )

        if portfolio.daily_loss_pct >= self.config.MAX_DAILY_LOSS_PCT:
            reasons.append("daily loss limit breached")

        if portfolio.weekly_loss_pct >= self.config.MAX_WEEKLY_LOSS_PCT:
            reasons.append("weekly loss limit breached")

        if portfolio.open_positions >= self.config.MAX_OPEN_POSITIONS:
            reasons.append("max open positions reached")

        if live_execution and not proposal.source_urls:
            reasons.append("source_urls required for live proposals")

        if len(proposal.thesis.strip()) < rules.MIN_THESIS_LENGTH:
            reasons.append("thesis shorter than minimum threshold")

        risk_level = proposal.risk_level.strip().lower()
        if risk_level == "high" and proposal.confidence_score < rules.MIN_CONFIDENCE_HIGH_RISK:
            reasons.append("high risk requires confidence >= 9.0")

        if reasons:
            return RiskDecision(
                approved=False,
                decision=rules.REJECTED,
                reasons=reasons,
            )

        max_notional = position_sizing.calculate_max_notional(
            portfolio.account_equity,
            self.config.MAX_POSITION_PCT,
            self.config.MAX_SINGLE_TRADE_DOLLARS,
        )
        conf_mult = position_sizing.confidence_size_multiplier(proposal.confidence_score)
        risk_mult = position_sizing.risk_level_multiplier(proposal.risk_level)

        if conf_mult == 0.0:
            return RiskDecision(
                approved=False,
                decision=rules.REJECTED,
                reasons=["confidence below trade threshold"],
            )

        adjusted_notional = max_notional * conf_mult * risk_mult
        adjusted_position_pct = min(
            proposal.requested_position_pct,
            adjusted_notional / portfolio.account_equity if portfolio.account_equity > 0 else 0,
        )
        max_allowed_loss = adjusted_notional * proposal.exit_rules.stop_loss_pct

        if live_execution or self.config.TRADING_MODE in (
            TradingMode.LIVE_MANUAL.value,
            TradingMode.LIVE_LIMITED.value,
            TradingMode.PROPOSAL.value,
        ):
            decision = rules.APPROVED_FOR_MANUAL_REVIEW
        else:
            decision = rules.APPROVED_FOR_PAPER

        return RiskDecision(
            approved=True,
            decision=decision,
            reasons=["passed all risk checks"],
            adjusted_position_pct=adjusted_position_pct,
            adjusted_notional=adjusted_notional,
            max_allowed_loss=max_allowed_loss,
        )

    def evaluate_batch(
        self,
        proposals: list[TradeProposal],
        portfolio: PortfolioContext,
        *,
        live_execution: bool = False,
    ) -> dict[str, RiskDecision]:
        return {p.id: self.evaluate(p, portfolio, live_execution=live_execution) for p in proposals}
