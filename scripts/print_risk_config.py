#!/usr/bin/env python3
"""Print current risk and trading safety configuration."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from octane_capital.config import config

FIELDS = [
    "TRADING_MODE",
    "ENABLE_LIVE_TRADING",
    "REQUIRE_HUMAN_APPROVAL",
    "STARTING_PAPER_CASH",
    "MAX_POSITION_PCT",
    "MAX_SINGLE_TRADE_DOLLARS",
    "MAX_DAILY_LOSS_PCT",
    "MAX_WEEKLY_LOSS_PCT",
    "MAX_OPEN_POSITIONS",
    "ALLOW_OPTIONS",
    "ALLOW_MARGIN",
    "ALLOW_SHORTS",
    "ALLOW_CRYPTO",
]

if __name__ == "__main__":
    print("Octane Capital Lab — Risk Configuration\n")
    for field in FIELDS:
        print(f"  {field}: {getattr(config, field)}")
