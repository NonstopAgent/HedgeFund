"""Watchlist Strategy — manual ticker universe from env."""

import os
from typing import List, Optional

from octane_capital.models import ScoutSignal, AuditReport, TradeProposal
from octane_capital.agents.proposal_cio import create_trade_proposal


class WatchlistStrategy:
    name = "watchlist"

    def __init__(self, watchlist: Optional[List[str]] = None):
        raw = os.getenv("WATCHLIST", "NVDA,AMD,TSM,AVGO,MSFT,GOOGL,META,AMZN,PLTR,ARM")
        self.watchlist = {t.strip().upper() for t in (watchlist or raw.split(",")) if t.strip()}

    def generate_candidates(self, context: dict) -> List[ScoutSignal]:
        signals = context.get("scout_signals", [])
        return [s for s in signals if s.ticker.upper() in self.watchlist]

    def create_proposal(
        self, candidate: ScoutSignal, audit: Optional[AuditReport] = None
    ) -> TradeProposal:
        return create_trade_proposal(candidate, audit)
