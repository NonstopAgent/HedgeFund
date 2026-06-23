"""Octane Capital Lab - Chief Investment Officer (CIO) agent.

Manages the Scout and Auditor in a hierarchical structure. In this research
phase the CIO only reviews and coordinates research; it never executes trades.
"""

from crewai import Agent

from ..config import config
from ..octane_branding import print_agent_status
from ..perplexity_llm import create_perplexity_llm


def create_cio_agent() -> Agent:
    """Create the CIO agent (manager)."""
    print_agent_status("THE CIO", "INITIALIZING", "Setting up hierarchical management...")

    # CIO uses sonar-reasoning-pro for management decisions
    llm = create_perplexity_llm(model=config.SCOUT_MODEL, temperature=0.6)

    cio = Agent(
        role="Chief Investment Officer",
        goal="Oversee investment research operations, make strategic decisions on which tickers warrant deep-dive audits, and synthesize final investment recommendations based on Scout and Auditor findings.",
        backstory="""You are the Chief Investment Officer at Octane Capital Lab, an AI-focused research operation specializing in AI and semiconductor opportunities.
        You have deep experience in quantitative research and identifying early-stage opportunities through systematic alpha generation.
        You oversee a team of specialists: The Scout (who identifies alpha signals) and The Auditor (who performs deep-dive analysis).
        Your role is to:
        1. Review Scout's ticker recommendations and determine which meet the confidence threshold for audit
        2. Coordinate the research pipeline between Scout and Auditor
        3. Synthesize findings into actionable investment theses
        4. Maintain institutional memory of successful patterns and strategies
        5. Make final go/no-go decisions on which opportunities deserve further research""",
        verbose=True,
        allow_delegation=True,
        max_iter=3,
        llm=llm,
    )

    return cio
