"""
Octane Capital Lab - Chief Investment Officer (CIO) Agent
Manages Scout and Auditor in a hierarchical structure.
"""

from crewai import Agent

from octane_capital.config import config
from octane_capital.llm import create_perplexity_llm
from octane_capital.branding import print_agent_status


def create_cio_agent() -> Agent:
    """Create the CIO agent (manager)."""
    print_agent_status("THE CIO", "INITIALIZING", "Setting up hierarchical management...")

    llm = create_perplexity_llm(model=config.SCOUT_MODEL, temperature=0.6)

    return Agent(
        role="Chief Investment Officer",
        goal=(
            "Oversee investment research operations, decide which tickers warrant deep-dive audits, "
            "and synthesize final investment recommendations from Scout and Auditor findings."
        ),
        backstory="""You are the Chief Investment Officer at Octane Capital Lab.
        You oversee The Scout (alpha signal detection) and The Auditor (due diligence).
        You coordinate the research pipeline and maintain institutional memory of findings.
        You do not execute trades — you produce research and recommendations only.""",
        verbose=True,
        allow_delegation=True,
        max_iter=3,
        llm=llm,
    )
