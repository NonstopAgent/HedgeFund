"""
Octane Capital Lab - Swing strategy
Research-grounded swing setups: trade established uptrends with momentum, size
by ATR risk, place ATR stops, hold days-to-weeks. Long-only equities.

Pipeline per ticker:
  quality screen -> indicators -> swing score -> ATR stop & risk sizing
  -> TradeProposal (the deterministic RiskEngine still has final say).

Rules distilled from standard swing practice:
  * Only longs in uptrends: close > SMA50 (and SMA50 > SMA200 preferred).
  * Momentum present: positive recent return, RSI in a healthy band (not >75).
  * Not overextended far above SMA50.
  * Liquid, non-penny, non-microcap (quality_filters).
  * Stop = ATR_STOP_MULT * ATR below entry; target = 2R; hold <= SWING_MAX_HOLD_DAYS.
"""

from __future__ import annotations

from typing import List, Optional

from octane_capital.config import config
from octane_capital.data.market_data import MarketData, MarketDataError
from octane_capital.risk.quality_filters import check_quality
from octane_capital.risk.atr_sizing import size_position
from octane_capital.strategies.scoring import SwingInputs, swing_score, score_breakdown
from octane_capital.models import TradeProposal, ExitRules, TradeAction


def _risk_level(atr_pct: float) -> str:
    if atr_pct < 0.03:
        return "Low"
    if atr_pct <= 0.06:
        return "Medium"
    return "High"


def evaluate_ticker(
    ticker: str,
    md: MarketData,
    cfg=config,
    account_equity: Optional[float] = None,
) -> Optional[TradeProposal]:
    """Return a BUY TradeProposal if `ticker` is a valid swing long, else None."""
    equity = account_equity if account_equity is not None else cfg.STARTING_PAPER_CASH

    # 1) Quality gate (penny/illiquid/microcap/earnings).
    q = check_quality(ticker, md, cfg)
    if not q.passed:
        return None

    # 2) Indicators.
    try:
        close = md.get_price(ticker)
        sma50 = md.sma(ticker, 50)
        sma200 = md.sma(ticker, 200)
        rsi14 = md.rsi(ticker, cfg.RSI_PERIOD)
        atr14 = md.atr(ticker, cfg.ATR_PERIOD)
        ret_5d = md.pct_change(ticker, 5)
        adv = md.avg_dollar_volume(ticker, 20)
    except MarketDataError:
        return None

    # 3) Setup gate: must be an uptrend with some momentum.
    if not (close > sma50 and ret_5d > 0):
        return None

    inp = SwingInputs(
        close=close, sma50=sma50, sma200=sma200, rsi14=rsi14,
        atr14=atr14, ret_5d=ret_5d, avg_dollar_volume=adv,
    )
    score = swing_score(inp)
    if score < cfg.SWING_MIN_SCORE:
        return None

    # 4) ATR stop + risk-based size (hard-capped).
    sizing = size_position(
        account_equity=equity,
        entry_price=close,
        atr=atr14,
        risk_per_trade_pct=cfg.RISK_PER_TRADE_PCT,
        atr_stop_mult=cfg.ATR_STOP_MULT,
        max_position_pct=cfg.MAX_POSITION_PCT,
        max_single_trade_dollars=cfg.MAX_SINGLE_TRADE_DOLLARS,
    )
    if sizing.quantity <= 0 or sizing.notional <= 0:
        return None

    stop_loss_pct = (close - sizing.stop_price) / close
    atr_pct = atr14 / close if close else 0.0
    bd = score_breakdown(inp)

    thesis = (
        f"{ticker} swing long: price {close:.2f} above SMA50 {sma50:.2f} "
        f"(SMA200 {sma200:.2f}), 5d momentum {ret_5d:+.1%}, RSI {rsi14:.0f}. "
        f"ATR stop {sizing.stop_price:.2f} (-{stop_loss_pct:.1%}), risk "
        f"${sizing.dollar_risk:.2f} of ${equity:.0f}."
    )
    evidence = [
        f"trend score {bd['trend']:.1f}/10 (close>SMA50={close > sma50}, SMA50>SMA200={sma50 > sma200})",
        f"momentum score {bd['momentum']:.1f}/10 (5d {ret_5d:+.1%}, RSI {rsi14:.0f})",
        f"liquidity ${adv:,.0f} avg daily $ volume",
        f"ATR{cfg.ATR_PERIOD} {atr14:.2f} ({atr_pct:.1%} of price)",
    ]

    return TradeProposal(
        ticker=ticker,
        action=TradeAction.BUY,
        thesis=thesis,
        evidence=evidence,
        source_urls=[],
        confidence_score=score,
        risk_level=_risk_level(atr_pct),
        time_horizon=f"{cfg.SWING_MIN_HOLD_DAYS}-{cfg.SWING_MAX_HOLD_DAYS} trading days",
        requested_position_pct=min(sizing.notional / equity if equity else 0.0,
                                   cfg.MAX_POSITION_PCT),
        requested_notional=sizing.notional,
        exit_rules=ExitRules(
            stop_loss_pct=round(stop_loss_pct, 4),
            take_profit_pct=round(min(2 * stop_loss_pct, 2.0), 4),  # 2R target
            max_hold_days=cfg.SWING_MAX_HOLD_DAYS,
            invalidation_events=["close below ATR stop", "close back under SMA50",
                                 "earnings surprise"],
        ),
        strategy="ai_semiconductor_swing",
        entry_price=close,
        atr=atr14,
        stop_price=sizing.stop_price,
    )


def generate_swing_proposals(
    tickers: List[str],
    md: MarketData,
    cfg=config,
    account_equity: Optional[float] = None,
) -> List[TradeProposal]:
    proposals: List[TradeProposal] = []
    for t in tickers:
        try:
            p = evaluate_ticker(t, md, cfg, account_equity)
        except Exception:
            p = None
        if p is not None:
            proposals.append(p)
    # Best setups first.
    proposals.sort(key=lambda p: p.confidence_score, reverse=True)
    return proposals
