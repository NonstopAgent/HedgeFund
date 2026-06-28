"""
Octane Capital Lab - Trading universe
A broad, static list of liquid US large/mid-cap equities for scanning and
backtesting. Static (not scraped) for reproducible backtests. Survivorship note:
this is today's list, so historical backtests over it carry mild survivorship
bias — fine for a first-pass edge check, not a published track record.
"""

from __future__ import annotations

LARGE_CAP_UNIVERSE = [
    # Mega-cap tech / semis
    "AAPL", "MSFT", "NVDA", "AMD", "AVGO", "TSM", "QCOM", "INTC", "MU", "AMAT",
    "LRCX", "KLAC", "ADI", "TXN", "ARM", "MRVL", "ASML", "SMCI", "ORCL", "CRM",
    "ADBE", "NOW", "INTU", "CSCO", "IBM", "ACN",
    # Internet / comm / media
    "GOOGL", "GOOG", "META", "AMZN", "NFLX", "DIS", "CMCSA", "TMUS", "T", "VZ",
    "SNAP", "PINS", "UBER", "ABNB", "SHOP", "SPOT", "RBLX", "DASH",
    # Software / cloud
    "PLTR", "SNOW", "NET", "DDOG", "CRWD", "ZS", "PANW", "FTNT", "MDB", "TEAM",
    "WDAY", "OKTA", "TTD",
    # Consumer
    "TSLA", "HD", "LOW", "NKE", "SBUX", "MCD", "COST", "WMT", "TGT", "PG", "KO",
    "PEP", "PM", "MO", "CL", "MDLZ", "KHC", "GIS", "EL", "LULU", "CMG", "ROST",
    "TJX", "DG", "DLTR",
    # Financials
    "JPM", "BAC", "WFC", "C", "GS", "MS", "BLK", "SCHW", "AXP", "V", "MA", "PYPL",
    "COF", "USB", "PNC", "BK", "SPGI", "CME", "ICE", "CB", "MMC", "PGR", "TRV",
    # Health care
    "UNH", "JNJ", "LLY", "PFE", "MRK", "ABBV", "TMO", "ABT", "DHR", "BMY", "AMGN",
    "GILD", "CVS", "CI", "HUM", "ISRG", "MDT", "SYK", "BSX", "VRTX", "REGN", "ZTS",
    "MRNA", "BIIB",
    # Industrials
    "CAT", "DE", "BA", "GE", "HON", "UNP", "UPS", "FDX", "LMT", "RTX", "NOC", "GD",
    "MMM", "EMR", "ETN", "ITW",
    # Energy
    "XOM", "CVX", "COP", "SLB", "EOG", "MPC", "PSX", "VLO", "OXY", "KMI", "WMB",
    # Materials / utilities / REIT
    "LIN", "APD", "SHW", "FCX", "NEM", "NUE", "NEE", "DUK", "SO", "D", "AEP",
    "PLD", "AMT", "EQIX", "CCI", "SPG", "O", "PSA",
    # Autos
    "F", "GM", "RIVN", "LCID",
]

# De-duped, order-preserving.
_seen = set()
LARGE_CAP_UNIVERSE = [t for t in LARGE_CAP_UNIVERSE if not (t in _seen or _seen.add(t))]

# A faster subset for live daily scans (mega/large + popular momentum names).
LIVE_WATCHLIST = [
    "NVDA", "AMD", "AVGO", "TSM", "QCOM", "MU", "MRVL", "ARM", "SMCI", "ASML",
    "AAPL", "MSFT", "GOOGL", "META", "AMZN", "NFLX", "TSLA", "ORCL", "CRM", "ADBE",
    "PLTR", "NOW", "PANW", "CRWD", "NET", "DDOG", "SNOW", "UBER", "SHOP", "AVGO",
    "LLY", "UNH", "JPM", "V", "MA", "COST", "WMT", "HD", "CAT", "GE",
]
_seen2 = set()
LIVE_WATCHLIST = [t for t in LIVE_WATCHLIST if not (t in _seen2 or _seen2.add(t))]


def get_universe() -> list[str]:
    return list(LARGE_CAP_UNIVERSE)
