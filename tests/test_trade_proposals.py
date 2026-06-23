"""Trade proposal parsing tests."""

import pytest

from octane_capital.agents.proposal_cio import parse_trade_proposal_json
from octane_capital.models import TradeProposal, ExitRules, TradeAction


VALID_JSON = """
{
  "ticker": "AMD",
  "action": "BUY",
  "thesis": "AMD gaining data center share with competitive AI accelerators and strong roadmap.",
  "evidence": ["MI300 adoption", "Cloud partnership expansion"],
  "source_urls": ["https://example.com/news"],
  "confidence_score": 8.2,
  "risk_level": "Medium",
  "time_horizon": "90 days",
  "requested_position_pct": 0.03,
  "exit_rules": {"stop_loss_pct": 0.08, "max_hold_days": 90}
}
"""


def test_valid_json_becomes_trade_proposal():
    proposal = parse_trade_proposal_json(VALID_JSON)
    assert isinstance(proposal, TradeProposal)
    assert proposal.ticker == "AMD"
    assert proposal.action == TradeAction.BUY


def test_invalid_json_fails_safely():
    with pytest.raises((ValueError, Exception)):
        parse_trade_proposal_json("not json at all")


def test_missing_thesis_fails_validation():
    with pytest.raises(Exception):
        TradeProposal(
            ticker="AMD",
            action=TradeAction.BUY,
            thesis="too short",
            evidence=["one"],
            confidence_score=8.0,
            risk_level="Low",
            time_horizon="30d",
            requested_position_pct=0.02,
            exit_rules=ExitRules(stop_loss_pct=0.05, max_hold_days=30),
        )


def test_missing_exit_rules_fails_validation():
    with pytest.raises(Exception):
        TradeProposal.model_validate(
            {
                "ticker": "AMD",
                "action": "BUY",
                "thesis": "Valid thesis with enough detail for validation purposes here.",
                "evidence": ["signal"],
                "confidence_score": 8.0,
                "risk_level": "Low",
                "time_horizon": "30d",
                "requested_position_pct": 0.02,
            }
        )
