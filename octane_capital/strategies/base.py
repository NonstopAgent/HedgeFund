"""Strategy abstractions."""

from typing import List, Optional, Protocol

from octane_capital.models import ScoutSignal, AuditReport, TradeProposal


class Strategy(Protocol):
    name: str

    def generate_candidates(self, context: dict) -> List[ScoutSignal]: ...
    def create_proposal(
        self, candidate: ScoutSignal, audit: Optional[AuditReport]
    ) -> TradeProposal: ...
