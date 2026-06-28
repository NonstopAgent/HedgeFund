"""Risk engine tests."""

from datetime import datetime

import pytest

from octane_capital.config import Config
from octane_capital.models import (
    TradeProposal,
    TradeAction,
    AssetClass,
    ExitRules,
    PortfolioContext,
)
from octane_capital.risk import RiskEngine
from octane_capital.risk import rules


def _proposal(**kwargs) -> TradeProposal:
    defaults = dict(
        ticker="NVDA",
        action=TradeAction.BUY,
        thesis="Strong AI semiconductor demand with expanding data center capex cycle.",
        evidence=["GitHub CUDA activity spike", "Revenue beat in latest quarter"],
        source_urls=["https://example.com/filing"],
        confidence_score=8.5,
        risk_level="Medium",
        time_horizon="60 days",
        requested_position_pct=0.03,
        exit_rules=ExitRules(stop_loss_pct=0.08, max_hold_days=90),
    )
    defaults.update(kwargs)
    return TradeProposal(**defaults)


def _portfolio(**kwargs) -> PortfolioContext:
    defaults = dict(account_equity=10000, daily_loss_pct=0.0, weekly_loss_pct=0.0, open_positions=0)
    defaults.update(kwargs)
    return PortfolioContext(**defaults)


def test_reject_low_confidence():
    engine = RiskEngine()
    p = _proposal(confidence_score=7.0)
    d = engine.evaluate(p, _portfolio())
    assert not d.approved
    assert d.decision == rules.REJECTED


def test_reject_oversized_position():
    cfg = Config()
    cfg.MAX_POSITION_PCT = 0.05
    engine = RiskEngine(cfg)
    p = _proposal(requested_position_pct=0.20)
    d = engine.evaluate(p, _portfolio())
    assert not d.approved


def test_reject_high_risk_low_confidence():
    engine = RiskEngine()
    p = _proposal(risk_level="High", confidence_score=8.5)
    d = engine.evaluate(p, _portfolio())
    assert not d.approved


def test_reject_daily_loss_breach():
    cfg = Config()
    cfg.MAX_DAILY_LOSS_PCT = 0.02
    engine = RiskEngine(cfg)
    p = _proposal()
    d = engine.evaluate(p, _portfolio(daily_loss_pct=0.03))
    assert not d.approved


def test_reject_too_many_positions():
    cfg = Config()
    cfg.MAX_OPEN_POSITIONS = 5
    engine = RiskEngine(cfg)
    p = _proposal()
    d = engine.evaluate(p, _portfolio(open_positions=5))
    assert not d.approved


def test_reject_live_without_sources():
    engine = RiskEngine()
    p = _proposal(source_urls=[])
    d = engine.evaluate(p, _portfolio(), live_execution=True)
    assert not d.approved


def test_approve_equity_paper_trade():
    engine = RiskEngine()
    p = _proposal()
    d = engine.evaluate(p, _portfolio())
    assert d.approved
    assert d.decision == rules.APPROVED_FOR_PAPER
    assert d.adjusted_notional is not None
    assert d.adjusted_notional > 0


def test_reject_options_when_disabled():
    cfg = Config()
    cfg.ALLOW_OPTIONS = False
    engine = RiskEngine(cfg)
    p = _proposal(asset_class=AssetClass.OPTION)
    d = engine.evaluate(p, _portfolio())
    assert not d.approved
