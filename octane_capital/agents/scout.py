"""The Scout agent for AI and semiconductor research signals."""

import json

from crewai import Agent, Task

from octane_capital.branding import print_agent_status
from octane_capital.config import config
from octane_capital.models import ScoutSignal
from octane_capital.perplexity_client import perplexity_client
from octane_capital.perplexity_llm import create_perplexity_llm


def create_scout_agent() -> Agent:
    """Create The Scout agent."""
    print_agent_status("THE SCOUT", "INITIALIZING", "Configuring signal detection...")

    llm = create_perplexity_llm(model=config.SCOUT_MODEL, temperature=0.6)

    return Agent(
        role="Alpha Signal Scout",
        goal=(
            f"Identify {config.SCOUT_TARGET_TICKERS} high-potential AI and "
            "semiconductor stock tickers by scanning GitHub, Reddit, and tech "
            "news for early research signals that are not yet fully priced into "
            "the market."
        ),
        backstory="""You are The Scout, a specialized financial intelligence
        analyst at Octane Capital Lab. You detect early-stage research
        opportunities through web intelligence analysis.

        You excel at identifying:
        - GitHub star spikes for AI/semiconductor repositories
        - Developer activity trends indicating product launches
        - Reddit sentiment shifts in stock-specific communities
        - Patent filings and job postings revealing R&D expansion
        - Partnership announcements and regulatory approvals

        You focus on signals from the last 30 days and prioritize research
        candidates that are not yet fully priced in. Your outputs must be
        structured and include ticker symbols, confidence scores, and detailed
        signal analysis.""",
        verbose=True,
        llm=llm,
        allow_delegation=False,
    )


def create_scout_task() -> Task:
    """Create The Scout's task."""
    target_count = config.SCOUT_TARGET_TICKERS

    return Task(
        description=f"""
        Scan GitHub, Reddit, and tech news sources to identify {target_count}
        high-potential AI and semiconductor stock tickers.

        Your search should focus on:
        1. GITHUB SIGNALS:
           - Massive spikes in GitHub stars for AI/semiconductor related repositories
           - New major open-source projects from public companies
           - Developer activity trends indicating product launches

        2. REDDIT SIGNALS:
           - Unusual volume in stock-specific subreddits
           - Technical discussions revealing emerging product adoption
           - Community sentiment shifts

        3. TECH NEWS SIGNALS:
           - Patent filings in AI/semiconductor space
           - Unusual job postings indicating R&D expansion
           - Partnership announcements with major tech companies
           - Regulatory approvals or breakthrough technology news

        CRITERIA:
        - Focus on AI and semiconductor sector stocks
        - Look for recent signals (last 30 days)
        - Prioritize signals that are not yet fully priced in
        - Rank tickers by confidence score (highest first)

        OUTPUT REQUIREMENTS:
        For each ticker, provide:
        - Ticker symbol
        - Company name
        - Sentiment/confidence score (0-10 scale)
        - List of alpha signals detected
        - Signal sources (GitHub, Reddit, Tech News)
        - Summary explaining why this ticker has research potential

        Return exactly {target_count} tickers, formatted as JSON matching the
        ScoutSignal model structure.
        """,
        agent=create_scout_agent(),
        expected_output=f"""
        JSON array of {target_count} ScoutSignal objects, each containing:
        - ticker (string)
        - company_name (string)
        - sentiment_score (float 0-10)
        - signals (array of strings)
        - signal_sources (array of strings)
        - summary (string)

        Format: [{{"ticker": "...", "company_name": "...", "sentiment_score": X.X, "signals": [...], "signal_sources": [...], "summary": "..."}}]
        """,
    )


def parse_scout_output(output: str) -> list[ScoutSignal]:
    """Parse Scout task output into ScoutSignal models."""
    try:
        parsed = perplexity_client.extract_json(output)

        if isinstance(parsed, list):
            tickers_data = parsed
        elif isinstance(parsed, dict) and "tickers" in parsed:
            tickers_data = parsed["tickers"]
        elif isinstance(parsed, dict) and "signals" in parsed:
            tickers_data = parsed["signals"]
        else:
            output_clean = output.strip()
            tickers_data = json.loads(output_clean) if output_clean.startswith("[") else []

        signals: list[ScoutSignal] = []
        for ticker_data in tickers_data:
            try:
                if "confidence_score" in ticker_data:
                    ticker_data["sentiment_score"] = ticker_data.pop("confidence_score")
                if "alpha_signals" in ticker_data:
                    ticker_data["signals"] = ticker_data.pop("alpha_signals")

                signals.append(ScoutSignal(**ticker_data))
            except Exception as exc:
                print_agent_status("THE SCOUT", "ERROR", f"Failed to parse ticker: {exc}")
                continue

        return signals
    except Exception as exc:
        print_agent_status("THE SCOUT", "ERROR", f"Failed to parse output: {exc}")
        return []
