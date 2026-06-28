"""
Octane Capital Lab - The Scout Agent (CrewAI)
Scans web for alpha signals in AI and semiconductor stocks.
"""

from crewai import Agent, Task
from typing import List
import json

from octane_capital.config import config
from octane_capital.models import ScoutSignal
from octane_capital.llm import create_perplexity_llm, perplexity_client
from octane_capital.branding import print_agent_status


def create_scout_agent() -> Agent:
    """Create The Scout agent."""
    print_agent_status("THE SCOUT", "INITIALIZING", "Configuring alpha signal detection...")

    llm = create_perplexity_llm(model=config.SCOUT_MODEL, temperature=0.6)

    return Agent(
        role="Alpha Signal Scout",
        goal=(
            f"Identify {config.SCOUT_TARGET_TICKERS} high-potential AI and semiconductor stock "
            "tickers by scanning GitHub, Reddit, and tech news for early alpha signals."
        ),
        backstory="""You are The Scout, a specialized financial intelligence analyst at Octane Capital Lab.
        Your expertise lies in detecting early-stage investment opportunities through web intelligence analysis.
        You excel at identifying GitHub star spikes, developer activity trends, Reddit sentiment shifts,
        patent filings, job postings revealing R&D expansion, and partnership announcements.
        You focus on signals from the last 30 days and prioritize opportunities not yet fully priced in.""",
        verbose=True,
        llm=llm,
        allow_delegation=False,
    )


def create_scout_task() -> Task:
    """Create The Scout's task."""
    target_count = config.SCOUT_TARGET_TICKERS

    return Task(
        description=f"""
        Scan GitHub, Reddit, and tech news sources to identify {target_count} high-potential AI and semiconductor stock tickers.

        Focus on GitHub signals, Reddit sentiment, and tech news (patents, hiring, partnerships).
        Return exactly {target_count} tickers ranked by confidence score.
        """,
        agent=create_scout_agent(),
        expected_output=f"""
        JSON array of {target_count} ScoutSignal objects with ticker, company_name, sentiment_score,
        signals, signal_sources, and summary fields.
        """,
    )


def parse_scout_output(output: str) -> List[ScoutSignal]:
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
            if output_clean.startswith("["):
                tickers_data = json.loads(output_clean)
            else:
                tickers_data = []

        signals = []
        for ticker_data in tickers_data:
            try:
                if "confidence_score" in ticker_data:
                    ticker_data["sentiment_score"] = ticker_data.pop("confidence_score")
                if "alpha_signals" in ticker_data:
                    ticker_data["signals"] = ticker_data.pop("alpha_signals")

                signals.append(ScoutSignal(**ticker_data))
            except Exception as e:
                print_agent_status("THE SCOUT", "ERROR", f"Failed to parse ticker: {str(e)}")

        return signals

    except Exception as e:
        print_agent_status("THE SCOUT", "ERROR", f"Failed to parse output: {str(e)}")
        return []
