"""Persistent research storage using Supabase."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from supabase import Client, create_client

from octane_capital.branding import print_agent_status
from octane_capital.config import config
from octane_capital.models import AuditReport, ScoutSignal


class Vault:
    """The Vault - database storage adapter."""

    def __init__(self) -> None:
        self.client: Client | None = None
        self.initialized = False

        if config.SUPABASE_URL and config.SUPABASE_KEY:
            try:
                self.client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
                self.initialized = True
                print_agent_status("THE VAULT", "ACTIVE", "Connected to Supabase")
            except Exception as exc:
                print_agent_status("THE VAULT", "ERROR", f"Connection failed: {exc}")
                self.initialized = False
        else:
            print_agent_status("THE VAULT", "STANDBY", "No Supabase credentials provided")

    def save_ticker_report(
        self,
        ticker_data: dict[str, Any] | None = None,
        audit_data: dict[str, Any] | None = None,
        scout_signal: ScoutSignal | None = None,
        audit_report: AuditReport | None = None,
    ) -> bool:
        """Save ticker research and optional audit report to the database."""
        if not self.initialized or self.client is None:
            return bool(config.GHOST_MODE)

        try:
            if scout_signal:
                ticker = scout_signal.ticker
                company_name = scout_signal.company_name
                scout_confidence = scout_signal.sentiment_score
                alpha_signals = scout_signal.signals
                signal_sources = scout_signal.signal_sources
                scout_summary = scout_signal.summary
            elif ticker_data:
                ticker = ticker_data.get("ticker", "")
                company_name = ticker_data.get("company_name", "")
                scout_confidence = ticker_data.get("confidence_score") or ticker_data.get(
                    "sentiment_score", 0.0
                )
                alpha_signals = ticker_data.get("alpha_signals") or ticker_data.get(
                    "signals", []
                )
                signal_sources = ticker_data.get("signal_sources", [])
                scout_summary = ticker_data.get("summary", "")
            else:
                return False

            if audit_report:
                audit_performed = True
                audit_json = audit_report.model_dump(mode="json")
                revised_confidence = audit_report.final_assessment.conviction_score
                risk_level = audit_report.final_assessment.risk_level
                investment_thesis = audit_report.final_assessment.investment_thesis
            elif audit_data:
                audit_performed = audit_data.get("success", True)
                audit_json = audit_data
                final_assessment = audit_data.get("final_assessment", {})
                revised_confidence = final_assessment.get(
                    "revised_confidence"
                ) or final_assessment.get("conviction_score")
                risk_level = final_assessment.get("risk_level")
                investment_thesis = final_assessment.get("investment_thesis")
            else:
                audit_performed = False
                audit_json = {}
                revised_confidence = None
                risk_level = None
                investment_thesis = None

            record = {
                "ticker": ticker,
                "company_name": company_name,
                "scout_confidence": float(scout_confidence),
                "alpha_signals": alpha_signals,
                "signal_sources": signal_sources,
                "scout_summary": scout_summary,
                "audit_performed": audit_performed,
                "audit_data": audit_json,
                "revised_confidence": (
                    float(revised_confidence) if revised_confidence is not None else None
                ),
                "risk_level": risk_level,
                "investment_thesis": investment_thesis,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
            }

            result = self.client.table("ticker_reports").insert(record).execute()

            if result.data:
                print_agent_status("THE VAULT", "COMPLETE", f"Saved: {ticker}")
                return True

            print_agent_status("THE VAULT", "ERROR", "Insert returned no data")
            return False
        except Exception as exc:
            print_agent_status("THE VAULT", "ERROR", f"Save failed: {exc}")
            return False

    def get_recent_tickers(self, limit: int = 10) -> list[dict[str, Any]]:
        """Retrieve recent ticker reports."""
        if not self.initialized or self.client is None:
            return []

        try:
            result = (
                self.client.table("ticker_reports")
                .select("*")
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
            return result.data if result.data else []
        except Exception as exc:
            print_agent_status("THE VAULT", "ERROR", f"Query failed: {exc}")
            return []

    def is_connected(self) -> bool:
        """Check if the vault is connected."""
        return self.initialized
