"""
Octane Capital Lab - ATR risk-based position sizing
Deterministic. This is how "a little risky but never zeroed" is enforced.

Sizing logic (per trade):
  1. Stop is placed ATR_STOP_MULT * ATR below entry  -> defines per-share risk.
  2. Dollar risk allowed = account_equity * RISK_PER_TRADE_PCT.
  3. Quantity = dollar_risk / per_share_risk.
  4. Notional is then HARD-CAPPED by both MAX_POSITION_PCT and
     MAX_SINGLE_TRADE_DOLLARS. The cap can only ever SHRINK the position.

The result: each losing trade costs ~RISK_PER_TRADE_PCT of the account at the
stop (often less after caps bind), so a string of losses bleeds slowly instead
of zeroing the account.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SizingResult:
    quantity: float
    notional: float
    entry_price: float
    stop_price: float
    per_share_risk: float
    dollar_risk: float          # actual $ at risk after caps
    reasons: list[str]


def atr_stop_price(entry_price: float, atr: float, mult: float) -> float:
    """Stop placed mult*ATR below entry, floored at 0."""
    return max(0.0, entry_price - atr * mult)


def size_position(
    *,
    account_equity: float,
    entry_price: float,
    atr: float,
    risk_per_trade_pct: float,
    atr_stop_mult: float,
    max_position_pct: float,
    max_single_trade_dollars: float,
) -> SizingResult:
    reasons: list[str] = []
    stop = atr_stop_price(entry_price, atr, atr_stop_mult)
    per_share_risk = entry_price - stop

    if per_share_risk <= 0 or entry_price <= 0:
        return SizingResult(0.0, 0.0, entry_price, stop, 0.0, 0.0,
                            ["invalid entry/ATR — cannot size"])

    dollar_risk = account_equity * risk_per_trade_pct
    raw_qty = dollar_risk / per_share_risk
    raw_notional = raw_qty * entry_price

    # Hard caps — choose the most restrictive.
    cap_notional = min(account_equity * max_position_pct, max_single_trade_dollars)
    notional = min(raw_notional, cap_notional)
    if notional < raw_notional:
        reasons.append(
            f"position capped to ${notional:.2f} "
            f"(min of {max_position_pct:.0%} equity and ${max_single_trade_dollars:.0f})"
        )

    quantity = notional / entry_price  # fractional shares OK on Robinhood
    actual_risk = quantity * per_share_risk
    return SizingResult(
        quantity=round(quantity, 6),
        notional=round(notional, 2),
        entry_price=entry_price,
        stop_price=round(stop, 4),
        per_share_risk=round(per_share_risk, 4),
        dollar_risk=round(actual_risk, 2),
        reasons=reasons or ["sized by ATR risk model"],
    )
