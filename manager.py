"""
Octane Global Trust - Chief Investment Officer (CIO) Agent
Manages the Scout and Auditor in hierarchical structure
"""

from crewai import Agent
from perplexity_llm import create_perplexity_llm
from config import config
from octane_branding import print_agent_status


def create_cio_agent() -> Agent:
    """Create the CIO agent (manager)"""
    print_agent_status("THE CIO", "INITIALIZING", "Setting up hierarchical management...")
    
    # CIO uses sonar-reasoning-pro for management decisions
    llm = create_perplexity_llm(model=config.SCOUT_MODEL, temperature=0.6)
    
    cio = Agent(
        role="Chief Investment Officer",
        goal="Oversee investment research operations, make strategic decisions on which tickers warrant deep-dive audits, and synthesize final investment recommendations based on Scout and Auditor findings.",
        backstory="""You are the Chief Investment Officer at Octane Global Trust, a sophisticated hedge fund specializing in AI and semiconductor investments. 
        You have 20+ years of experience in quantitative finance and have built your reputation on identifying early-stage opportunities through systematic alpha generation.
        You oversee a team of specialists: The Scout (who identifies alpha signals) and The Auditor (who performs deep-dive analysis).
        Your role is to:
        1. Review Scout's ticker recommendations and determine which meet the confidence threshold for audit
        2. Coordinate the research pipeline between Scout and Auditor
        3. Synthesize findings into actionable investment theses
        4. Maintain institutional memory of successful patterns and strategies
        5. Make final go/no-go decisions on investment opportunities""",
        verbose=True,
        allow_delegation=True,
        max_iter=3,
        llm=llm
    )
    
    return cio
