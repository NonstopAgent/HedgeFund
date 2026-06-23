"""Legacy CIO manager agent for the research crew."""

from crewai import Agent

from octane_capital.branding import print_agent_status
from octane_capital.config import config
from octane_capital.perplexity_llm import create_perplexity_llm


def create_cio_agent() -> Agent:
    """Create the CIO manager agent."""
    print_agent_status("THE CIO", "INITIALIZING", "Setting up research management...")

    llm = create_perplexity_llm(model=config.SCOUT_MODEL, temperature=0.6)

    return Agent(
        role="Chief Research Officer",
        goal=(
            "Oversee investment research operations, decide which tickers "
            "warrant deep-dive audits, and synthesize Scout and Auditor "
            "findings into research conclusions. Do not execute trades."
        ),
        backstory="""You are the Chief Research Officer at Octane Capital Lab,
        a private research and simulation system for AI and semiconductor
        equities. You oversee The Scout, who identifies research signals, and
        The Auditor, who performs deep-dive analysis.

        Your role is to:
        1. Review Scout recommendations against the confidence threshold
        2. Coordinate the research pipeline between Scout and Auditor
        3. Synthesize findings into research theses
        4. Maintain institutional memory of useful research patterns
        5. Avoid trade execution and keep outputs research-only""",
        verbose=True,
        allow_delegation=True,
        max_iter=3,
        llm=llm,
    )
