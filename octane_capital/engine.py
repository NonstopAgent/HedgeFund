"""
Octane Capital Lab - Research Engine
Orchestrates Scout → CIO → Auditor → Proposals → Risk → Vault pipeline.
"""

from crewai import Crew, Process

from octane_capital.agents.cio import create_cio_agent
from octane_capital.agents.scout import create_scout_agent, create_scout_task, parse_scout_output
from octane_capital.agents.auditor import create_auditor_agent, create_audit_task, parse_audit_output
from octane_capital.agents.proposal_cio import create_trade_proposals
from octane_capital.agents.critic import review_proposals
from octane_capital.vault import Vault
from octane_capital.vault.repository import VaultRepository
from octane_capital.risk import RiskEngine
from octane_capital.risk import rules
from octane_capital.broker import PaperBroker
from octane_capital.broker.order_factory import order_from_proposal
from octane_capital.config import config
from octane_capital.models import (
    ResearchCycleResult,
    ProposalStatus,
    TradeAction,
    PortfolioContext,
)
from octane_capital.branding import (
    print_header,
    print_section,
    print_footer,
    print_agent_status,
    print_ticker_card,
)
from octane_capital.llm import create_perplexity_llm


class OctaneCapitalEngine:
    """Main orchestration for research, proposals, and paper trading."""

    def __init__(self):
        config.require_perplexity_key()
        self.cio = create_cio_agent()
        self.scout_agent = create_scout_agent()
        self.auditor_agent = create_auditor_agent()
        self.vault = Vault()
        self.repository = VaultRepository(self.vault)
        self.risk_engine = RiskEngine()
        self.paper_broker = PaperBroker()

    def run_research_cycle(self) -> ResearchCycleResult:
        """Execute Scout → Auditor research and generate proposals."""
        if not config.GHOST_MODE:
            print_header()

        print_section("INITIALIZING RESEARCH ENGINE")
        print_agent_status("SYSTEM", "INFO", f"Trading mode: {config.TRADING_MODE}")

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

        result = ResearchCycleResult(scout_signals=scout_signals)

        if not scout_signals:
            print_section("ENGINE HALTED")
            if not config.GHOST_MODE:
                print("No tickers identified by The Scout. Exiting.")
                print_footer()
            return result

        for signal in scout_signals:
            print_ticker_card(signal.ticker, signal.sentiment_score, signal.summary)

        print_section("PHASE 2: CIO REVIEW & AUDIT DECISION")
        audit_tasks = []
        tickers_to_audit = [
            sig for sig in scout_signals if sig.sentiment_score >= config.CONFIDENCE_THRESHOLD
        ]
        for signal in tickers_to_audit:
            audit_tasks.append(
                create_audit_task(
                    ticker=signal.ticker,
                    company_name=signal.company_name,
                    initial_confidence=signal.sentiment_score,
                )
            )

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
                                f"{signal.ticker}: Conviction "
                                f"{audit_report.final_assessment.conviction_score:.1f}/10",
                            )

        result.audit_reports = audit_results

        for signal in scout_signals:
            audit_report = audit_results.get(signal.ticker)
            self.vault.save_ticker_report(scout_signal=signal, audit_report=audit_report)

        print_section("PHASE 5: TRADE PROPOSAL GENERATION")
        portfolio = self.paper_broker.portfolio_context()
        proposals = create_trade_proposals(scout_signals, audit_results, portfolio)
        result.proposals = proposals

        print_section("PHASE 6: CRITIC REVIEW")
        result.critic_reviews = review_proposals(proposals)

        print_section("PHASE 7: RISK ENGINE EVALUATION")
        risk_decisions = self.risk_engine.evaluate_batch(proposals, portfolio)
        result.risk_decisions = risk_decisions

        for proposal in proposals:
            self.repository.save_proposal(proposal)
            decision = risk_decisions[proposal.id]

            critic = result.critic_reviews.get(proposal.id)
            if critic and not critic.passed:
                proposal.status = ProposalStatus.NEEDS_REVIEW
            elif not decision.approved:
                proposal.status = ProposalStatus.RISK_REJECTED
            elif decision.decision == rules.APPROVED_FOR_PAPER:
                proposal.status = ProposalStatus.NEEDS_REVIEW
                result.approved_for_paper.append(proposal)
            elif decision.decision == rules.APPROVED_FOR_MANUAL_REVIEW:
                proposal.status = ProposalStatus.NEEDS_REVIEW
                result.proposals_needing_approval.append(proposal)

            self.repository.save_risk_decision(proposal.id, decision)
            self.repository.save_proposal(proposal)

        print_section("ENGINE SUMMARY")
        print(f"Tickers Identified: {len(scout_signals)}")
        print(f"Tickers Audited: {len(tickers_to_audit)}")
        print(f"Proposals Generated: {len(proposals)}")
        print(f"Approved for Paper: {len(result.approved_for_paper)}")
        print(f"Needing Approval: {len(result.proposals_needing_approval)}")
        print_agent_status("SYSTEM", "INFO", "Research cycle complete")

        if not config.GHOST_MODE:
            print_footer()

        return result

    def run_paper_cycle(self) -> ResearchCycleResult:
        """Run research then simulate approved paper trades."""
        result = self.run_research_cycle()

        print_section("PAPER TRADING EXECUTION")
        for proposal in result.approved_for_paper:
            if proposal.action not in (TradeAction.BUY, TradeAction.SELL, TradeAction.EXIT):
                continue

            decision = result.risk_decisions[proposal.id]
            price = self.paper_broker._get_price(proposal.ticker)
            self.paper_broker.set_price(proposal.ticker, price)
            order = order_from_proposal(proposal, decision, dry_run=False, price=price)
            trade_result = self.paper_broker.place_order(order)
            self.repository.save_order_result(trade_result)

            if trade_result.submitted:
                proposal.status = ProposalStatus.EXECUTED
                self.repository.save_proposal(proposal)
                print_agent_status(
                    "PAPER BROKER",
                    "COMPLETE",
                    f"{proposal.ticker}: filled @ {trade_result.average_fill_price:.2f}",
                )
            else:
                print_agent_status("PAPER BROKER", "ERROR", trade_result.error or "order failed")

        return result

    def run_live_manual_cycle(self) -> ResearchCycleResult:
        """Run research and return proposals needing human approval."""
        return self.run_research_cycle()


PredatorEngine = OctaneCapitalEngine
