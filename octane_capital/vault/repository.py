"""
Octane Capital Lab - Vault Repository
Persists proposals, risk decisions, orders, and grades.
Falls back to local JSON when Supabase is unavailable.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from octane_capital.config import config
from octane_capital.models import (
    TradeProposal,
    RiskDecision,
    TradeResult,
    TradeGrade,
    ProposalStatus,
)
from octane_capital.vault.database import Vault


class VaultRepository:
    """Unified storage for trade workflow artifacts."""

    def __init__(self, vault: Optional[Vault] = None, local_dir: Optional[Path] = None):
        self.vault = vault or Vault()
        self.local_dir = local_dir or Path(".data/vault")
        self.local_dir.mkdir(parents=True, exist_ok=True)

    def _local_path(self, name: str) -> Path:
        return self.local_dir / f"{name}.json"

    def _read_local(self, name: str) -> list[dict]:
        path = self._local_path(name)
        if not path.exists():
            return []
        return json.loads(path.read_text())

    def _write_local(self, name: str, records: list[dict]) -> None:
        self._local_path(name).write_text(json.dumps(records, indent=2, default=str))

    def save_proposal(self, proposal: TradeProposal) -> bool:
        records = self._read_local("proposals")
        records = [r for r in records if r.get("id") != proposal.id]
        records.append(proposal.model_dump(mode="json"))
        self._write_local("proposals", records)

        if self.vault.initialized:
            try:
                self.vault.client.table("trade_proposals").upsert(
                    {
                        "id": proposal.id,
                        "ticker": proposal.ticker,
                        "company_name": proposal.company_name,
                        "asset_class": proposal.asset_class.value,
                        "action": proposal.action.value,
                        "thesis": proposal.thesis,
                        "evidence": proposal.evidence,
                        "source_urls": proposal.source_urls,
                        "confidence_score": proposal.confidence_score,
                        "risk_level": proposal.risk_level,
                        "time_horizon": proposal.time_horizon,
                        "requested_position_pct": proposal.requested_position_pct,
                        "requested_notional": proposal.requested_notional,
                        "exit_rules": proposal.exit_rules.model_dump(),
                        "status": proposal.status.value,
                        "requires_human_approval": proposal.requires_human_approval,
                        "source_report_id": proposal.source_report_id,
                    }
                ).execute()
            except Exception:
                pass
        return True

    def get_proposal(self, proposal_id: str) -> Optional[TradeProposal]:
        for record in self._read_local("proposals"):
            if record.get("id") == proposal_id:
                return TradeProposal.model_validate(record)
        return None

    def list_proposals(self, status: Optional[ProposalStatus] = None) -> List[TradeProposal]:
        proposals = [TradeProposal.model_validate(r) for r in self._read_local("proposals")]
        if status:
            proposals = [p for p in proposals if p.status == status]
        return sorted(proposals, key=lambda p: p.created_at, reverse=True)

    def update_proposal_status(self, proposal_id: str, status: ProposalStatus) -> bool:
        proposal = self.get_proposal(proposal_id)
        if not proposal:
            return False
        proposal.status = status
        return self.save_proposal(proposal)

    def save_risk_decision(self, proposal_id: str, decision: RiskDecision) -> bool:
        records = self._read_local("risk_decisions")
        records.append({"proposal_id": proposal_id, **decision.model_dump(mode="json")})
        self._write_local("risk_decisions", records)

        if self.vault.initialized:
            try:
                self.vault.client.table("risk_decisions").insert(
                    {
                        "proposal_id": proposal_id,
                        "approved": decision.approved,
                        "decision": decision.decision,
                        "reasons": decision.reasons,
                        "adjusted_position_pct": decision.adjusted_position_pct,
                        "adjusted_notional": decision.adjusted_notional,
                        "max_allowed_loss": decision.max_allowed_loss,
                    }
                ).execute()
            except Exception:
                pass
        return True

    def get_risk_decision(self, proposal_id: str) -> Optional[RiskDecision]:
        records = self._read_local("risk_decisions")
        for record in reversed(records):
            if record.get("proposal_id") == proposal_id:
                record = {k: v for k, v in record.items() if k != "proposal_id"}
                return RiskDecision.model_validate(record)
        return None

    def save_order_result(self, result: TradeResult) -> bool:
        records = self._read_local("orders")
        records.append(result.model_dump(mode="json"))
        self._write_local("orders", records)

        if self.vault.initialized:
            try:
                self.vault.client.table("orders").insert(
                    {
                        "proposal_id": result.proposal_id,
                        "broker": result.broker,
                        "mode": result.mode.value,
                        "submitted": result.submitted,
                        "ticker": result.ticker,
                        "action": result.action.value if result.action else None,
                        "notional": result.notional,
                        "broker_order_id": result.broker_order_id,
                        "filled_quantity": result.filled_quantity,
                        "average_fill_price": result.average_fill_price,
                        "error": result.error,
                    }
                ).execute()
            except Exception:
                pass
        return True

    def save_grade(self, grade: TradeGrade) -> bool:
        records = self._read_local("trade_grades")
        records.append(grade.model_dump(mode="json"))
        self._write_local("trade_grades", records)
        return True

    def list_grades(self) -> list[dict]:
        return self._read_local("trade_grades")

    def grades_by_strategy(self) -> dict[str, list[dict]]:
        out: dict[str, list[dict]] = {}
        for g in self.list_grades():
            strat = g.get("strategy") or "unknown"
            out.setdefault(strat, []).append(g)
        return out
