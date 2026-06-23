"""Octane Capital Lab - research engine.

Orchestrates the research cycle (Scout -> CIO review -> Auditor -> Vault)
using CrewAI. This engine performs research only: it does not place trades.
"""

from .agents.auditor import create_auditor_agent, create_audit_task, parse_audit_output
from .agents.cio import create_cio_agent
from .agents.scout import create_scout_agent, create_scout_task, parse_scout_output
from .config import config
from .octane_branding import (
    print_agent_status,
    print_footer,
    print_header,
    print_section,
    print_ticker_card,
)
from .perplexity_llm import create_perplexity_llm
from .vault.database import Vault

from crewai import Crew, Process


class OctaneCapitalEngine:
    """Main orchestration class for the Octane Capital research engine."""

    def __init__(self):
        self.cio = create_cio_agent()
        self.scout_agent = create_scout_agent()
        self.auditor_agent = create_auditor_agent()
        self.vault = Vault()

    def run_research_cycle(self):
        """Execute the full investment research pipeline using CrewAI."""
        if not config.GHOST_MODE:
            print_header()

        print_section("INITIALIZING RESEARCH ENGINE")
        print_agent_status(
            "SYSTEM", "INFO", "Hierarchical process with institutional memory enabled"
        )

        # Phase 1: Scout identifies alpha signals
        print_section("PHASE 1: ALPHA SIGNAL DETECTION")
        scout_task = create_scout_task()

        scout_crew = Crew(
            agents=[self.scout_agent],
            tasks=[scout_task],
            process=Process.sequential,
            verbose=True,
            memory=False,
        )

        scout_result = scout_crew.kickoff()

        scout_signals = parse_scout_output(str(scout_result))

        if not scout_signals:
            print_section("ENGINE HALTED")
            if not config.GHOST_MODE:
                print("No tickers identified by The Scout. Exiting.")
                print_footer()
            return

        for signal in scout_signals:
            print_ticker_card(signal.ticker, signal.sentiment_score, signal.summary)

        # Phase 2: CIO reviews and determines which tickers need audit
        print_section("PHASE 2: CIO REVIEW & AUDIT DECISION")

        audit_tasks = []
        tickers_to_audit = [
            sig
            for sig in scout_signals
            if sig.sentiment_score >= config.CONFIDENCE_THRESHOLD
        ]

        for signal in tickers_to_audit:
            audit_task = create_audit_task(
                ticker=signal.ticker,
                company_name=signal.company_name,
                initial_confidence=signal.sentiment_score,
            )
            audit_tasks.append(audit_task)

        # Phase 3: Hierarchical crew with CIO, Scout, and Auditor
        print_section("PHASE 3: DEEP-DIVE AUDIT (HIERARCHICAL)")

        crew_agents = [self.cio, self.scout_agent, self.auditor_agent]
        crew_tasks = [scout_task] + audit_tasks

        main_crew = Crew(
            agents=crew_agents,
            tasks=crew_tasks,
            process=Process.hierarchical,
            manager_llm=create_perplexity_llm(model=config.SCOUT_MODEL, temperature=0.6),
            verbose=True,
            memory=True,
            max_iter=3,
        )

        final_result = main_crew.kickoff()

        # Phase 4: Process results and persist
        print_section("PHASE 4: RESULT PROCESSING & VAULT STORAGE")

        audit_results = {}
        if audit_tasks and tickers_to_audit:
            for i, task in enumerate(audit_tasks):
                if i < len(tickers_to_audit):
                    signal = tickers_to_audit[i]
                    task_output = None
                    if hasattr(task, "output") and task.output:
                        task_output = str(task.output)
                    elif hasattr(final_result, "tasks_output") and final_result.tasks_output:
                        for t_output in final_result.tasks_output:
                            if signal.ticker in str(t_output):
                                task_output = str(t_output)
                                break

                    if task_output:
                        audit_report = parse_audit_output(task_output, signal.ticker)
                        if audit_report:
                            audit_results[signal.ticker] = audit_report
                            print_agent_status(
                                "THE AUDITOR",
                                "COMPLETE",
                                f"{signal.ticker}: Conviction {audit_report.final_assessment.conviction_score:.1f}/10",
                            )

        saved_count = 0
        for signal in scout_signals:
            audit_report = audit_results.get(signal.ticker)

            success = self.vault.save_ticker_report(
                scout_signal=signal, audit_report=audit_report
            )

            if success:
                saved_count += 1

        print_section("ENGINE SUMMARY")
        print(f"Tickers Identified: {len(scout_signals)}")
        print(f"Tickers Audited: {len(tickers_to_audit)}")
        print(f"Reports Saved: {saved_count}/{len(scout_signals)}")
        print_agent_status("SYSTEM", "INFO", "Institutional memory updated with findings")

        if not config.GHOST_MODE:
            print_footer()


def main():
    """Entry point for running a research cycle directly."""
    engine = OctaneCapitalEngine()
    engine.run_research_cycle()


if __name__ == "__main__":
    main()
