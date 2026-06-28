"""
Octane Capital Lab - Quality / "don't trade junk" filters
Deterministic gate that keeps the agent out of penny stocks, illiquid names,
micro-caps, and earnings-week landmines. Addresses "make sure it's not trading
bad stocks."

A ticker must pass ALL enabled checks to be tradable.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class QualityResult:
    passed: bool
    reasons: list[str]   # failure reasons when not passed; notes when passed


def check_quality(ticker: str, md, cfg) -> QualityResult:
    """
    md  : MarketData instance
    cfg : Config (uses MIN_PRICE, MIN_AVG_DOLLAR_VOLUME, MIN_MARKET_CAP,
          EARNINGS_BLACKOUT_DAYS)
    """
    reasons: list[str] = []

    # Price floor — no penny stocks.
    try:
        price = md.get_price(ticker)
        if price < cfg.MIN_PRICE:
            reasons.append(f"price ${price:.2f} < MIN_PRICE ${cfg.MIN_PRICE:.2f}")
    except Exception as e:
        return QualityResult(False, [f"no price available: {e}"])

    # Liquidity — must be easy to get in/out of on a small account.
    try:
        adv = md.avg_dollar_volume(ticker, days=20)
        if adv < cfg.MIN_AVG_DOLLAR_VOLUME:
            reasons.append(
                f"avg $ volume ${adv:,.0f} < MIN ${cfg.MIN_AVG_DOLLAR_VOLUME:,.0f}"
            )
    except Exception:
        reasons.append("could not verify liquidity")

    # Slow per-name checks (market cap + earnings) — skipped when QUALITY_FAST,
    # because they each cost a separate yfinance network call. The curated
    # universe is already large-cap, so this is safe for broad scans.
    if not getattr(cfg, "QUALITY_FAST", False):
        # Market cap — avoid micro-caps (best-effort; skip if unknown).
        mc = md.market_cap(ticker)
        if mc is not None and mc < cfg.MIN_MARKET_CAP:
            reasons.append(f"market cap ${mc:,.0f} < MIN ${cfg.MIN_MARKET_CAP:,.0f}")

        # Earnings blackout — don't open a swing into an earnings print.
        dte = md.days_to_earnings(ticker)
        if dte is not None and 0 <= dte <= cfg.EARNINGS_BLACKOUT_DAYS:
            reasons.append(f"earnings in {dte}d (<= blackout {cfg.EARNINGS_BLACKOUT_DAYS}d)")

    if reasons:
        return QualityResult(False, reasons)
    return QualityResult(True, ["passed quality screen"])
