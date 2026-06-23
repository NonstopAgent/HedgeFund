"""
Octane Capital Lab - The Auditor Agent (CrewAI)
Deep-dive audit of high-confidence tickers.
"""

from crewai import Agent, Task
from typing import Optional
from datetime import datetime
import json

from octane_capital.config import config
from octane_capital.models import (
    AuditReport,
    MoatAnalysis,
    SECAnalysis,
    InsiderTrading,
    FinancialHealth,
    FinalAssessment,
)
from octane_capital.llm import create_perplexity_llm, perplexity_client
from octane_capital.branding import print_agent_status


def create_auditor_agent() -> Agent:
    """Create The Auditor agent."""
    print_agent_status("THE AUDITOR", "INITIALIZING", "Configuring deep-dive analysis...")

    llm = create_perplexity_llm(model=config.AUDITOR_MODEL, temperature=0.5)

    return Agent(
        role="Investment Auditor",
        goal=(
            "Perform comprehensive due diligence audits on high-confidence tickers, analyzing "
            "technical moats, SEC filings, insider trading patterns, and financial health."
        ),
        backstory="""You are The Auditor, a senior investment analyst at Octane Capital Lab
        specializing in deep-dive due diligence on AI and semiconductor equities.""",
        verbose=True,
        llm=llm,
        allow_delegation=False,
    )


def create_audit_task(ticker: str, company_name: str, initial_confidence: float) -> Task:
    """Create The Auditor's task for a specific ticker."""
    return Task(
        description=f"""
        Perform a comprehensive deep-dive audit of {ticker} ({company_name}).
        Initial confidence score from Scout: {initial_confidence}/10.0

        Analyze technical moats, SEC filings, insider trading, financial health,
        and provide a final conviction score with investment thesis.
        """,
        agent=create_auditor_agent(),
        expected_output=f"""
        JSON object matching AuditReport structure for ticker {ticker}.
        """,
    )


def parse_audit_output(output: str, ticker: str) -> Optional[AuditReport]:
    """Parse Auditor task output into AuditReport model."""
    try:
        parsed = perplexity_client.extract_json(output)

        if not parsed:
            output_clean = output.strip()
            if output_clean.startswith("{"):
                parsed = json.loads(output_clean)
            else:
                parsed = {}

        if not parsed or "ticker" not in parsed:
            parsed["ticker"] = ticker

        if "audit_date" not in parsed:
            parsed["audit_date"] = datetime.now().isoformat()

        if "revised_confidence" in parsed.get("final_assessment", {}):
            parsed["final_assessment"]["conviction_score"] = parsed["final_assessment"].pop(
                "revised_confidence"
            )

        try:
            return AuditReport(**parsed)
        except Exception as e:
            print_agent_status("THE AUDITOR", "WARNING", f"Partial parse: {str(e)}")

            final_assessment_data = parsed.get("final_assessment", {})
            moat_data = parsed.get("technical_moats") or parsed.get("moat_analysis", {})
            sec_data = parsed.get("sec_analysis", {})
            insider_data = parsed.get("insider_trading", {})
            financial_data = parsed.get("financial_health", {})

            return AuditReport(
                ticker=ticker,
                audit_date=datetime.now(),
                moat_analysis=MoatAnalysis(
                    score=float(moat_data.get("score", 7.0)),
                    findings=moat_data.get("findings", []),
                    patents_mentioned=moat_data.get("patents_mentioned", []),
                ),
                risk_factors=parsed.get("risk_factors", []),
                sec_analysis=SECAnalysis(
                    score=float(sec_data.get("score", 7.0)),
                    revenue_trend=sec_data.get("revenue_trend", "Stable"),
                    key_metrics=sec_data.get("key_metrics", {}),
                    risk_factors=sec_data.get("risk_factors", []),
                ),
                insider_trading=InsiderTrading(
                    score=float(insider_data.get("score", 7.0)),
                    recent_activity=insider_data.get("recent_activity", "Neutral"),
                    notable_transactions=insider_data.get("notable_transactions", []),
                ),
                financial_health=FinancialHealth(
                    score=float(financial_data.get("score", 7.0)),
                    debt_equity_ratio=financial_data.get("debt_equity_ratio"),
                    profit_margin=financial_data.get("profit_margin"),
                    summary=financial_data.get("summary", "Financial analysis completed"),
                ),
                final_assessment=FinalAssessment(
                    conviction_score=float(
                        final_assessment_data.get("conviction_score")
                        or final_assessment_data.get("revised_confidence", 7.0)
                    ),
                    risk_level=final_assessment_data.get("risk_level", "Medium"),
                    investment_thesis=final_assessment_data.get("investment_thesis", output[:500]),
                    recommended_position=final_assessment_data.get("recommended_position", "Medium"),
                ),
            )

    except Exception as e:
        print_agent_status("THE AUDITOR", "ERROR", f"Failed to parse audit output: {str(e)}")
        return None
