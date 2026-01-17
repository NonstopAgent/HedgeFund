"""
Octane Global Trust - Predator Investment Engine
Main orchestration script using CrewAI with hierarchical process and institutional memory
"""

from crewai import Crew, Process
from agents.manager import create_cio_agent
from agents.scout import create_scout_agent, create_scout_task, parse_scout_output
from agents.auditor import create_auditor_agent, create_audit_task, parse_audit_output
from vault.database import Vault
from config import config
from octane_branding import print_header, print_section, print_footer, print_agent_status, print_ticker_card
from perplexity_llm import create_perplexity_llm
import time


class PredatorEngine:
    """Main orchestration class for the Predator investment engine"""
    
    def __init__(self):
        self.cio = create_cio_agent()
        self.scout_agent = create_scout_agent()
        self.auditor_agent = create_auditor_agent()
        self.vault = Vault()
    
    def run(self):
        """Execute the full investment research pipeline using CrewAI"""
        if not config.GHOST_MODE:
            print_header()
        
        print_section("INITIALIZING PREDATOR ENGINE")
        print_agent_status("SYSTEM", "INFO", "Hierarchical process with institutional memory enabled")
        
        # Phase 1: Scout identifies alpha signals
        print_section("PHASE 1: ALPHA SIGNAL DETECTION")
        scout_task = create_scout_task()
        
        # Create initial crew for Scout task
        scout_crew = Crew(
            agents=[self.scout_agent],
            tasks=[scout_task],
            process=Process.sequential,
            verbose=True,
            memory=False  # Scout doesn't need memory, CIO will manage
        )
        
        scout_result = scout_crew.kickoff()
        
        # Parse Scout output into ScoutSignal models
        scout_signals = parse_scout_output(str(scout_result))
        
        if not scout_signals:
            print_section("ENGINE HALTED")
            if not config.GHOST_MODE:
                print("No tickers identified by The Scout. Exiting.")
                print_footer()
            return
        
        # Display Scout findings
        for signal in scout_signals:
            print_ticker_card(
                signal.ticker,
                signal.sentiment_score,
                signal.summary
            )
        
        # Phase 2: CIO reviews and determines which tickers need audit
        print_section("PHASE 2: CIO REVIEW & AUDIT DECISION")
        
        # Prepare ticker summary for CIO
        ticker_summary = "\n".join([
            f"- {sig.ticker} ({sig.company_name}): Confidence {sig.sentiment_score:.1f}/10 - {sig.summary[:100]}"
            for sig in scout_signals
        ])
        
        # Create audit tasks for tickers meeting threshold
        audit_tasks = []
        tickers_to_audit = [
            sig for sig in scout_signals 
            if sig.sentiment_score >= config.CONFIDENCE_THRESHOLD
        ]
        
        for signal in tickers_to_audit:
            audit_task = create_audit_task(
                ticker=signal.ticker,
                company_name=signal.company_name,
                initial_confidence=signal.sentiment_score
            )
            audit_tasks.append(audit_task)
        
        # Phase 3: Hierarchical Crew with CIO, Scout, and Auditor
        print_section("PHASE 3: DEEP-DIVE AUDIT (HIERARCHICAL)")
        
        # Build the main crew with hierarchical process
        crew_agents = [self.cio, self.scout_agent, self.auditor_agent]
        crew_tasks = [scout_task] + audit_tasks
        
        # Create hierarchical crew with memory
        main_crew = Crew(
            agents=crew_agents,
            tasks=crew_tasks,
            process=Process.hierarchical,
            manager_llm=create_perplexity_llm(model=config.SCOUT_MODEL, temperature=0.6),
            verbose=True,
            memory=True,  # Institutional memory enabled
            max_iter=3
        )
        
        # Execute the crew
        final_result = main_crew.kickoff()
        
        # Parse results and prepare for vault storage
        print_section("PHASE 4: RESULT PROCESSING & VAULT STORAGE")
        
        # Extract audit reports from task outputs
        audit_results = {}
        if audit_tasks and tickers_to_audit:
            for i, task in enumerate(audit_tasks):
                if i < len(tickers_to_audit):
                    signal = tickers_to_audit[i]
                    # Try to get task output (CrewAI may store this differently)
                    task_output = None
                    if hasattr(task, 'output') and task.output:
                        task_output = str(task.output)
                    elif hasattr(final_result, 'tasks_output') and final_result.tasks_output:
                        # Try to find this task's output in crew results
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
                                f"{signal.ticker}: Conviction {audit_report.final_assessment.conviction_score:.1f}/10"
                            )
        
        # Save all reports to vault
        saved_count = 0
        for signal in scout_signals:
            # Save using Pydantic models
            audit_report = audit_results.get(signal.ticker)
            
            success = self.vault.save_ticker_report(
                scout_signal=signal,
                audit_report=audit_report
            )
            
            if success:
                saved_count += 1
        
        # Final summary
        print_section("ENGINE SUMMARY")
        print(f"Tickers Identified: {len(scout_signals)}")
        print(f"Tickers Audited: {len(tickers_to_audit)}")
        print(f"Reports Saved: {saved_count}/{len(scout_signals)}")
        print_agent_status("SYSTEM", "INFO", "Institutional memory updated with findings")
        
        if not config.GHOST_MODE:
            print_footer()


def main():
    """Entry point"""
    engine = PredatorEngine()
    engine.run()


if __name__ == "__main__":
    main()
