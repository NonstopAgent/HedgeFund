"""AI Semiconductor Momentum Strategy."""

import os
from typing import List, Optional

from octane_capital.config import config
from octane_capital.models import ScoutSignal, AuditReport, TradeProposal
from octane_capital.agents.proposal_cio import create_trade_proposal


UNIVERSE = {"NVDA", "AMD", "TSM", "AVGO", "ARM", "PLTR", "MU", "ASML", "INTC", "QCOM"}


class AISemiconductorMomentumStrategy:
    name = "ai_semiconductor_momentum"

    def generate_candidates(self, context: dict) -> List[ScoutSignal]:
        signals = context.get("scout_signals", [])
        return [
            s
            for s in signals
            if s.ticker.upper() in UNIVERSE
            and s.sentiment_score >= 7.5
            and len(s.signals) >= 2
        ]

    def create_proposal(
        self, candidate: ScoutSignal, audit: Optional[AuditReport] = None
    ) -> TradeProposal:
        if candidate.sentiment_score > 8.0 and not audit:
            raise ValueError("Audit required above 8.0 confidence")
        return create_trade_proposal(candidate, audit)
