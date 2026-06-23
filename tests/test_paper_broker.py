"""Paper broker tests."""

import tempfile
from pathlib import Path

from octane_capital.broker.paper_broker import PaperBroker
from octane_capital.models import OrderRequest, TradeAction


def _broker(tmp_path: Path, cash: float = 10000) -> PaperBroker:
    state = tmp_path / "paper.json"
    broker = PaperBroker(state_path=state, prices={"NVDA": 100.0})
    broker._state["cash"] = cash
    broker._save_state()
    return broker


def test_buy_reduces_cash(tmp_path):
    broker = _broker(tmp_path)
    order = OrderRequest(
        proposal_id="p1",
        ticker="NVDA",
        action=TradeAction.BUY,
        notional=500,
        dry_run=False,
    )
    result = broker.place_order(order)
    assert result.submitted
    assert broker.get_account().cash < 10000


def test_sell_increases_cash(tmp_path):
    broker = _broker(tmp_path)
    buy = OrderRequest(
        proposal_id="p1", ticker="NVDA", action=TradeAction.BUY, notional=500, dry_run=False
    )
    broker.place_order(buy)
    cash_after_buy = broker.get_account().cash

    sell = OrderRequest(
        proposal_id="p2",
        ticker="NVDA",
        action=TradeAction.SELL,
        quantity=broker.get_positions()[0].quantity,
        dry_run=False,
    )
    result = broker.place_order(sell)
    assert result.submitted
    assert broker.get_account().cash > cash_after_buy


def test_cannot_buy_more_than_cash(tmp_path):
    broker = _broker(tmp_path, cash=100)
    order = OrderRequest(
        proposal_id="p1",
        ticker="NVDA",
        action=TradeAction.BUY,
        notional=5000,
        dry_run=False,
    )
    result = broker.place_order(order)
    assert not result.submitted
    assert "cash" in (result.error or "").lower()


def test_positions_update(tmp_path):
    broker = _broker(tmp_path)
    order = OrderRequest(
        proposal_id="p1", ticker="NVDA", action=TradeAction.BUY, notional=1000, dry_run=False
    )
    broker.place_order(order)
    positions = broker.get_positions()
    assert len(positions) == 1
    assert positions[0].ticker == "NVDA"
    assert positions[0].quantity > 0
