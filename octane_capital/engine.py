"""Research engine orchestration for Octane Capital Lab."""

from __future__ import annotations

from crewai import Crew, Process

from octane_capital.agents.auditor import (
    create_audit_task,
    create_auditor_agent,
    parse_audit_output,
)
from octane_capital.agents.manager import create_cio_agent
from octane_capital.agents.scout import (
    create_scout_agent,
    create_scout_task,
    parse_scout_output,
)
from octane_capital.branding import (
    print_agent_status,
    print_footer,
    print_header,
    print_section,
    print_ticker_card,
)
from octane_capital.config import config
from octane_capital.perplexity_llm import create_perplexity_llm
from octane_capital.vault.database import Vault


class OctaneCapitalEngine:
    """Main orchestration class for the research engine."""

    def __init__(self) -> None:
        config.validate_live_trading_disabled_by_default()
        self.cio = create_cio_agent()
        self.scout_agent = create_scout_agent()
        self.auditor_agent = create_auditor_agent()
        self.vault = Vault()

    def run_research_cycle(self) -> None:
        """Execute the current research-only pipeline using CrewAI."""
        if not config.GHOST_MODE:
            print_header()

        print_section("INITIALIZING RESEARCH ENGINE")
        print_agent_status("SYSTEM", "INFO", "Research mode enabled; no trading actions")

        print_section("PHASE 1: SIGNAL DETECTION")
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

        print_section("PHASE 2: CIO REVIEW & AUDIT DECISION")
        tickers_to_audit = [
            signal
            for signal in scout_signals
            if signal.sentiment_score >= config.CONFIDENCE_THRESHOLD
        ]

        audit_tasks = [
            create_audit_task(
                ticker=signal.ticker,
                company_name=signal.company_name,
                initial_confidence=signal.sentiment_score,
            )
            for signal in tickers_to_audit
        ]

        print_section("PHASE 3: DEEP-DIVE AUDIT")
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

        print_section("PHASE 4: RESULT PROCESSING & VAULT STORAGE")
        audit_results = {}
        if audit_tasks and tickers_to_audit:
            for index, task in enumerate(audit_tasks):
                if index >= len(tickers_to_audit):
                    continue

                signal = tickers_to_audit[index]
                task_output = None
                if hasattr(task, "output") and task.output:
                    task_output = str(task.output)
                elif hasattr(final_result, "tasks_output") and final_result.tasks_output:
                    for output in final_result.tasks_output:
                        if signal.ticker in str(output):
                            task_output = str(output)
                            break

                if task_output:
                    audit_report = parse_audit_output(task_output, signal.ticker)
                    if audit_report:
                        audit_results[signal.ticker] = audit_report
                        print_agent_status(
                            "THE AUDITOR",
                            "COMPLETE",
                            (
                                f"{signal.ticker}: Conviction "
                                f"{audit_report.final_assessment.conviction_score:.1f}/10"
                            ),
                        )

        saved_count = 0
        for signal in scout_signals:
            audit_report = audit_results.get(signal.ticker)
            success = self.vault.save_ticker_report(
                scout_signal=signal,
                audit_report=audit_report,
            )
            if success:
                saved_count += 1

        print_section("ENGINE SUMMARY")
        print(f"Tickers Identified: {len(scout_signals)}")
        print(f"Tickers Audited: {len(tickers_to_audit)}")
        print(f"Reports Saved: {saved_count}/{len(scout_signals)}")
        print_agent_status("SYSTEM", "INFO", "Research cycle complete")

        if not config.GHOST_MODE:
            print_footer()

    def run(self) -> None:
        """Backward-compatible alias for the research cycle."""
        self.run_research_cycle()


PredatorEngine = OctaneCapitalEngine


def main() -> None:
    """Legacy script entry point."""
    OctaneCapitalEngine().run_research_cycle()


if __name__ == "__main__":
    main()
