"""The Auditor agent for high-confidence ticker due diligence."""

import json
from datetime import datetime

from crewai import Agent, Task

from octane_capital.branding import print_agent_status
from octane_capital.config import config
from octane_capital.models import (
    AuditReport,
    FinalAssessment,
    FinancialHealth,
    InsiderTrading,
    MoatAnalysis,
    SECAnalysis,
)
from octane_capital.perplexity_client import perplexity_client
from octane_capital.perplexity_llm import create_perplexity_llm


def create_auditor_agent() -> Agent:
    """Create The Auditor agent."""
    print_agent_status("THE AUDITOR", "INITIALIZING", "Configuring due diligence...")

    llm = create_perplexity_llm(model=config.AUDITOR_MODEL, temperature=0.5)

    return Agent(
        role="Investment Research Auditor",
        goal=(
            "Perform comprehensive due diligence audits on high-confidence "
            "tickers, analyzing technical moats, SEC filings, insider trading "
            "patterns, and financial health to produce detailed research "
            "assessments."
        ),
        backstory="""You are The Auditor, a senior research analyst at Octane
        Capital Lab specializing in deep-dive due diligence.

        Your expertise includes:
        - Analyzing proprietary technology and patent portfolios
        - Reviewing SEC filings (10-K, 10-Q) for financial trends and risk factors
        - Tracking insider trading patterns and executive compensation
        - Assessing financial health metrics and balance sheet quality

        Your audits are meticulous and objective. You evaluate both
        opportunities and risks.""",
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

        AUDIT REQUIREMENTS:

        1. TECHNICAL MOATS ANALYSIS:
           - Evaluate proprietary technology and patents
           - Assess R&D spending trends and pipeline
           - Analyze competitive advantages in AI/semiconductor space
           - Identify barriers to entry for competitors

        2. SEC FILINGS ANALYSIS:
           - Review recent 10-K, 10-Q filings
           - Analyze revenue trends and growth metrics
           - Evaluate cash flow and balance sheet health
           - Extract management discussion highlights
           - Identify and assess risk factors

        3. INSIDER TRADING PATTERNS:
           - Review recent insider buying/selling activity
           - Analyze executive compensation trends
           - Track stock option exercises
           - Review Form 4 filings

        4. FINANCIAL HEALTH ASSESSMENT:
           - Calculate debt-to-equity ratios
           - Evaluate profit margins and operating leverage
           - Assess revenue concentration risks
           - Determine growth trajectory sustainability

        5. FINAL ASSESSMENT:
           - Provide revised conviction score (0-10)
           - Categorize risk level (Low/Medium/High)
           - Write detailed investment thesis
           - Recommend position size (Large/Medium/Small/None)

        OUTPUT: Provide a comprehensive audit report in JSON format matching
        the AuditReport model structure.
        """,
        agent=create_auditor_agent(),
        expected_output=f"""
        JSON object matching AuditReport structure with:
        - ticker: "{ticker}"
        - audit_date: ISO timestamp
        - moat_analysis: {{score, findings[], patents_mentioned[]}}
        - risk_factors: string[]
        - sec_analysis: {{score, revenue_trend, key_metrics{{}}, risk_factors[]}}
        - insider_trading: {{score, recent_activity, notable_transactions[]}}
        - financial_health: {{score, debt_equity_ratio, profit_margin, summary}}
        - final_assessment: {{conviction_score, risk_level, investment_thesis, recommended_position}}
        """,
    )


def parse_audit_output(output: str, ticker: str) -> AuditReport | None:
    """Parse Auditor task output into an AuditReport model."""
    try:
        parsed = perplexity_client.extract_json(output)

        if not parsed:
            output_clean = output.strip()
            parsed = json.loads(output_clean) if output_clean.startswith("{") else {}

        if not parsed or "ticker" not in parsed:
            parsed["ticker"] = ticker

        if "audit_date" not in parsed:
            parsed["audit_date"] = datetime.now().isoformat()

        if "revised_confidence" in parsed.get("final_assessment", {}):
            parsed["final_assessment"]["conviction_score"] = parsed[
                "final_assessment"
            ].pop("revised_confidence")

        try:
            return AuditReport(**parsed)
        except Exception as exc:
            print_agent_status("THE AUDITOR", "WARNING", f"Partial parse: {exc}")

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
                    summary=financial_data.get(
                        "summary", "Financial analysis completed"
                    ),
                ),
                final_assessment=FinalAssessment(
                    conviction_score=float(
                        final_assessment_data.get("conviction_score")
                        or final_assessment_data.get("revised_confidence", 7.0)
                    ),
                    risk_level=final_assessment_data.get("risk_level", "Medium"),
                    investment_thesis=final_assessment_data.get(
                        "investment_thesis", output[:500]
                    ),
                    recommended_position=final_assessment_data.get(
                        "recommended_position", "Medium"
                    ),
                ),
            )
    except Exception as exc:
        print_agent_status("THE AUDITOR", "ERROR", f"Failed to parse audit output: {exc}")
        return None
