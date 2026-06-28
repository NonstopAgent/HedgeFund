"""
Tests for the swing upgrade: scoring, ATR sizing, loss breaker, trust multiplier,
quality screen, and risk-engine wiring. All deterministic — no network.
"""

import pytest

from octane_capital.config import Config
from octane_capital.models import TradeProposal, TradeAction, ExitRules, PortfolioContext
from octane_capital.risk import RiskEngine
from octane_capital.risk import rules
from octane_capital.risk.atr_sizing import size_position, atr_stop_price
from octane_capital.risk.loss_tracker import compute_loss_pcts, record_day_open
from octane_capital.strategies.scoring import SwingInputs, swing_score
from octane_capital.strategies.scoreboard import summarize, trust_multiplier
from octane_capital.risk.quality_filters import check_quality


# ---------- ATR sizing ----------
def test_atr_sizing_caps_and_risk():
    r = size_position(
        account_equity=200, entry_price=100, atr=2.0,
        risk_per_trade_pct=0.02, atr_stop_mult=1.5,
        max_position_pct=0.25, max_single_trade_dollars=50,
    )
    assert r.stop_price == pytest.approx(97.0)          # 100 - 1.5*2
    assert r.notional <= 50.0 + 1e-9                    # hard cap binds
    assert r.quantity > 0
    # risk after cap = qty * per_share_risk, must be <= 2% of equity
    assert r.dollar_risk <= 0.02 * 200 + 1e-6


# ---------- scoring ----------
def test_swing_score_ranks_uptrend_above_weak():
    strong = SwingInputs(close=110, sma50=100, sma200=90, rsi14=60,
                         atr14=3, ret_5d=0.05, avg_dollar_volume=80_000_000)
    weak = SwingInputs(close=95, sma50=100, sma200=105, rsi14=42,
                       atr14=9, ret_5d=-0.02, avg_dollar_volume=1_000_000)
    assert swing_score(strong) > swing_score(weak)
    assert swing_score(strong) >= 7.0


# ---------- loss tracker + breaker ----------
def test_loss_tracker_and_breaker_trips():
    hist = []
    record_day_open(hist, 200)                       # day opened at 200
    daily, weekly = compute_loss_pcts(hist, 185)     # equity now 185 -> -7.5%
    assert daily == pytest.approx(0.075, abs=1e-3)

    cfg = Config()
    engine = RiskEngine(cfg)
    p = _swing_proposal()
    d = engine.evaluate(p, PortfolioContext(account_equity=185, daily_loss_pct=daily))
    assert not d.approved
    assert any("daily loss" in r for r in d.reasons)


# ---------- trust multiplier (learning loop) ----------
def test_trust_multiplier_never_grows_and_shrinks_losers():
    losers = [{"pnl_pct": -0.05} for _ in range(12)]
    winners = [{"pnl_pct": 0.10} for _ in range(12)]
    assert trust_multiplier(summarize(losers, "s")) <= 0.25
    assert trust_multiplier(summarize(winners, "s")) <= 1.0
    assert trust_multiplier(summarize([], "s")) == 0.5   # no evidence -> half


# ---------- quality screen ----------
class _FakeMD:
    def get_price(self, t): return 3.0          # penny
    def avg_dollar_volume(self, t, days=20): return 1_000
    def market_cap(self, t): return 50_000_000
    def days_to_earnings(self, t): return 1

def test_quality_rejects_junk():
    cfg = Config()
    res = check_quality("JUNK", _FakeMD(), cfg)
    assert not res.passed
    assert len(res.reasons) >= 1


# ---------- risk engine wiring ----------
def _swing_proposal(**kw):
    defaults = dict(
        ticker="NVDA", action=TradeAction.BUY,
        thesis="Swing long: price above SMA50 with positive 5d momentum and healthy RSI.",
        evidence=["trend ok", "momentum ok"],
        confidence_score=8.0, risk_level="Low", time_horizon="3-30 trading days",
        requested_position_pct=0.25, requested_notional=50.0,
        exit_rules=ExitRules(stop_loss_pct=0.03, take_profit_pct=0.06, max_hold_days=30),
        strategy="ai_semiconductor_swing", entry_price=100.0, atr=2.0, stop_price=97.0,
    )
    defaults.update(kw)
    return TradeProposal(**defaults)

def test_risk_engine_approves_good_swing_and_caps_size():
    cfg = Config()
    d = RiskEngine(cfg).evaluate(_swing_proposal(), PortfolioContext(account_equity=200))
    assert d.approved
    assert d.adjusted_notional <= min(200 * cfg.MAX_POSITION_PCT, cfg.MAX_SINGLE_TRADE_DOLLARS) + 1e-9

def test_risk_engine_rejects_oversized_notional():
    d = RiskEngine(Config()).evaluate(
        _swing_proposal(requested_notional=60.0), PortfolioContext(account_equity=200)
    )
    assert not d.approved

def test_high_risk_low_confidence_rejected():
    d = RiskEngine(Config()).evaluate(
        _swing_proposal(risk_level="High Risk", confidence_score=8.0),
        PortfolioContext(account_equity=200),
    )
    assert not d.approved  # coerced "High Risk" -> HIGH, needs >=9.0
