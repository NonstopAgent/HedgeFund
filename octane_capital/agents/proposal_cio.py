"""
Octane Capital Lab - Trade Proposal CIO
Creates structured TradeProposal JSON from research inputs.
Never places orders.
"""

import json
from typing import List, Optional

from octane_capital.config import config
from octane_capital.models import (
    ScoutSignal,
    AuditReport,
    TradeProposal,
    TradeAction,
    ExitRules,
    PortfolioContext,
)
from octane_capital.branding import print_agent_status

CIO_SYSTEM_PROMPT = """You are Octane Capital Lab's CIO agent. You do not execute trades.
You create structured trade proposals only.

Rules:
1. Never recommend a trade without a clear thesis.
2. Never recommend a trade without risk factors in evidence.
3. Never recommend a trade without stop-loss or invalidation rules.
4. Prefer HOLD when evidence is weak.
5. Do not invent sources.
6. Options, margin, shorts, crypto, and leverage are disabled unless explicitly enabled.
7. Output valid JSON matching TradeProposal fields only.
8. The Risk Engine has final authority over position size and approval.
"""


def parse_trade_proposal_json(text: str, ticker: str | None = None) -> TradeProposal:
    """Parse CIO JSON output into a TradeProposal; fails safely on invalid input."""
    start = text.find("{")
    end = text.rfind("}") + 1
    if start < 0 or end <= start:
        raise ValueError("No JSON object found in CIO output")

    data = json.loads(text[start:end])
    if ticker and "ticker" not in data:
        data["ticker"] = ticker

    return TradeProposal.model_validate(data)


def _rule_based_proposal(
    signal: ScoutSignal,
    audit: Optional[AuditReport],
) -> TradeProposal:
    """Deterministic fallback when Anthropic is unavailable."""
    confidence = signal.sentiment_score
    if audit:
        confidence = audit.final_assessment.conviction_score

    action = TradeAction.HOLD
    if confidence >= 7.5:
        action = TradeAction.BUY

    risk_level = "Medium"
    thesis = signal.summary
    if audit:
        risk_level = audit.final_assessment.risk_level
        thesis = audit.final_assessment.investment_thesis

    evidence = list(signal.signals) or [signal.summary]
    if audit:
        evidence.extend(audit.risk_factors[:3])

    return TradeProposal(
        ticker=signal.ticker,
        company_name=signal.company_name,
        action=action,
        thesis=thesis,
        evidence=evidence,
        source_urls=[],
        confidence_score=confidence,
        risk_level=risk_level,
        time_horizon="30-90 days",
        requested_position_pct=min(config.MAX_POSITION_PCT, 0.03),
        exit_rules=ExitRules(
            stop_loss_pct=0.08,
            take_profit_pct=0.20,
            max_hold_days=90,
            invalidation_events=["thesis invalidation", "earnings miss"],
        ),
    )


def _call_anthropic(prompt: str) -> str:
    if not config.ANTHROPIC_API_KEY:
        raise ValueError("ANTHROPIC_API_KEY not configured")

    import anthropic

    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        system=CIO_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


def create_trade_proposal(
    signal: ScoutSignal,
    audit: Optional[AuditReport] = None,
    portfolio: Optional[PortfolioContext] = None,
) -> TradeProposal:
    """Generate a TradeProposal from Scout signal and optional audit."""
    print_agent_status("PROPOSAL CIO", "INITIALIZING", f"Evaluating {signal.ticker}")

    if not config.ANTHROPIC_API_KEY:
        print_agent_status("PROPOSAL CIO", "INFO", "No Anthropic key — using rule-based fallback")
        return _rule_based_proposal(signal, audit)

    audit_summary = ""
    if audit:
        audit_summary = json.dumps(audit.model_dump(mode="json"), default=str)[:3000]

    portfolio_summary = ""
    if portfolio:
        portfolio_summary = portfolio.model_dump_json()

    prompt = f"""
Create a TradeProposal JSON for ticker {signal.ticker}.

Scout signal:
{signal.model_dump_json()}

Audit report (optional):
{audit_summary or "none"}

Portfolio context:
{portfolio_summary or "none"}

Return only JSON with fields: ticker, company_name, action, thesis, evidence (list),
source_urls (list), confidence_score, risk_level, time_horizon, requested_position_pct,
exit_rules (stop_loss_pct, take_profit_pct, max_hold_days, invalidation_events).
Use action HOLD if evidence is weak.
"""

    try:
        raw = _call_anthropic(prompt)
        return parse_trade_proposal_json(raw, ticker=signal.ticker)
    except Exception as e:
        print_agent_status("PROPOSAL CIO", "WARNING", f"LLM parse failed: {e}")
        return _rule_based_proposal(signal, audit)


def create_trade_proposals(
    signals: List[ScoutSignal],
    audits: dict[str, AuditReport],
    portfolio: Optional[PortfolioContext] = None,
) -> List[TradeProposal]:
    """Generate proposals for all scout signals."""
    proposals = []
    for signal in signals:
        audit = audits.get(signal.ticker)
        proposals.append(create_trade_proposal(signal, audit, portfolio))
    return proposals
