"""
Octane Capital Lab - Deterministic Risk Engine (drop-in replacement)
Claude cannot override these rules.

Upgrades vs the audited version:
  * RiskLevel is coerced from free text (fixes the "High Risk" bypass).
  * ATR risk-based sizing when the proposal carries entry_price + atr.
  * Optional trust multiplier from graded history (can only SHRINK size).
  * Loss breakers now read populated daily/weekly loss pcts (see paper_broker).
"""

from __future__ import annotations

from typing import Optional

from octane_capital.config import config
from octane_capital.models import (
    TradeProposal,
    RiskDecision,
    PortfolioContext,
    TradeAction,
    AssetClass,
    TradingMode,
    RiskLevel,
)
from octane_capital.risk import position_sizing
from octane_capital.risk import rules
from octane_capital.risk.atr_sizing import size_position
from octane_capital.strategies.scoreboard import trust_for


class RiskEngine:
    def __init__(self, cfg=None):
        self.config = cfg or config

    def evaluate(
        self,
        proposal: TradeProposal,
        portfolio: PortfolioContext,
        *,
        live_execution: bool = False,
        grades_by_strategy: Optional[dict] = None,
    ) -> RiskDecision:
        cfg = self.config
        reasons: list[str] = []

        if live_execution and not cfg.ENABLE_LIVE_TRADING:
            reasons.append("ENABLE_LIVE_TRADING=false")
        if cfg.TRADING_MODE == TradingMode.RESEARCH.value and live_execution:
            reasons.append("TRADING_MODE=research blocks order execution")
        if proposal.action == TradeAction.BUY and proposal.confidence_score < rules.MIN_CONFIDENCE_BUY:
            reasons.append(f"confidence {proposal.confidence_score} below min {rules.MIN_CONFIDENCE_BUY}")
        if not proposal.ticker or not proposal.ticker.strip():
            reasons.append("ticker is missing or invalid")
        if proposal.asset_class != AssetClass.EQUITY:
            reasons.append(f"asset_class {proposal.asset_class} not allowed (equities only)")
        if proposal.action in (TradeAction.SELL, TradeAction.EXIT) and not cfg.ALLOW_SHORTS:
            pass  # closing a long is always allowed
        if proposal.exit_rules.stop_loss_pct is None:
            reasons.append("stop_loss_pct is missing")
        if proposal.requested_position_pct > cfg.MAX_POSITION_PCT + 1e-9:
            reasons.append(
                f"requested_position_pct {proposal.requested_position_pct} exceeds "
                f"MAX_POSITION_PCT {cfg.MAX_POSITION_PCT}"
            )
        if (
            proposal.requested_notional is not None
            and proposal.requested_notional > cfg.MAX_SINGLE_TRADE_DOLLARS + 1e-9
        ):
            reasons.append(
                f"requested_notional {proposal.requested_notional} exceeds "
                f"MAX_SINGLE_TRADE_DOLLARS {cfg.MAX_SINGLE_TRADE_DOLLARS}"
            )
        if portfolio.daily_loss_pct >= cfg.MAX_DAILY_LOSS_PCT:
            reasons.append("daily loss limit breached — no new entries")
        if portfolio.weekly_loss_pct >= cfg.MAX_WEEKLY_LOSS_PCT:
            reasons.append("weekly loss limit breached — no new entries")
        if portfolio.total_drawdown_pct >= cfg.MAX_TOTAL_DRAWDOWN_PCT:
            reasons.append(
                f"max-drawdown kill-switch: down {portfolio.total_drawdown_pct:.0%} from peak "
                f"(limit {cfg.MAX_TOTAL_DRAWDOWN_PCT:.0%}) — all new entries halted"
            )
        if portfolio.open_positions >= cfg.MAX_OPEN_POSITIONS:
            reasons.append("max open positions reached")
        if live_execution and not proposal.source_urls and proposal.strategy is None:
            # signal-driven swing proposals are self-sourced via indicators;
            # narrative proposals must carry sources for live.
            reasons.append("source_urls required for live narrative proposals")
        if len(proposal.thesis.strip()) < rules.MIN_THESIS_LENGTH:
            reasons.append("thesis shorter than minimum threshold")
        if RiskLevel.coerce(proposal.risk_level) == RiskLevel.HIGH and (
            proposal.confidence_score < rules.MIN_CONFIDENCE_HIGH_RISK
        ):
            reasons.append("high risk requires confidence >= 9.0")

        if reasons:
            return RiskDecision(approved=False, decision=rules.REJECTED, reasons=reasons)

        # ---- sizing ----
        if proposal.entry_price and proposal.atr and proposal.entry_price > 0:
            sized = size_position(
                account_equity=portfolio.account_equity,
                entry_price=proposal.entry_price,
                atr=proposal.atr,
                risk_per_trade_pct=cfg.RISK_PER_TRADE_PCT,
                atr_stop_mult=cfg.ATR_STOP_MULT,
                max_position_pct=cfg.MAX_POSITION_PCT,
                max_single_trade_dollars=cfg.MAX_SINGLE_TRADE_DOLLARS,
            )
            adjusted_notional = sized.notional
        else:
            max_notional = position_sizing.calculate_max_notional(
                portfolio.account_equity, cfg.MAX_POSITION_PCT, cfg.MAX_SINGLE_TRADE_DOLLARS
            )
            conf_mult = position_sizing.confidence_size_multiplier(proposal.confidence_score)
            if conf_mult == 0.0:
                return RiskDecision(approved=False, decision=rules.REJECTED,
                                    reasons=["confidence below trade threshold"])
            risk_mult = position_sizing.risk_level_multiplier(proposal.risk_level)
            adjusted_notional = max_notional * conf_mult * risk_mult

        # ---- learning loop: only ever shrink size ----
        if grades_by_strategy and proposal.strategy:
            tm = trust_for(grades_by_strategy, proposal.strategy)
            adjusted_notional *= max(0.0, min(1.0, tm))

        # Final clamp — never exceed hard caps regardless of path above.
        cap = min(portfolio.account_equity * cfg.MAX_POSITION_PCT, cfg.MAX_SINGLE_TRADE_DOLLARS)
        adjusted_notional = min(adjusted_notional, cap)

        if adjusted_notional <= 0:
            return RiskDecision(approved=False, decision=rules.REJECTED,
                                reasons=["position sized to zero after caps"])

        adjusted_position_pct = (
            adjusted_notional / portfolio.account_equity if portfolio.account_equity > 0 else 0.0
        )
        max_allowed_loss = adjusted_notional * proposal.exit_rules.stop_loss_pct

        if live_execution or cfg.TRADING_MODE in (
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
            adjusted_position_pct=round(adjusted_position_pct, 4),
            adjusted_notional=round(adjusted_notional, 2),
            max_allowed_loss=round(max_allowed_loss, 2),
        )

    def evaluate_batch(self, proposals, portfolio, *, live_execution=False, grades_by_strategy=None):
        return {
            p.id: self.evaluate(p, portfolio, live_execution=live_execution,
                                grades_by_strategy=grades_by_strategy)
            for p in proposals
        }
