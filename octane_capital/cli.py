"""
Octane Capital Lab - CLI
Safe entry points for research, paper trading, proposals, and execution.
"""

import argparse
import json
import sys

from octane_capital.config import config
from octane_capital.models import ProposalStatus, TradeGrade, TradingMode
from octane_capital.vault.repository import VaultRepository
from octane_capital.risk import RiskEngine
from octane_capital.broker import PaperBroker, ExecutionGuard, RobinhoodMCPBroker
from octane_capital.broker.order_factory import order_from_proposal
from octane_capital.backtest import BacktestEngine


def cmd_research(_args: argparse.Namespace) -> int:
    try:
        from octane_capital.engine import OctaneCapitalEngine

        OctaneCapitalEngine().run_research_cycle()
        return 0
    except ValueError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Research cycle failed: {e}", file=sys.stderr)
        return 1


def cmd_paper(_args: argparse.Namespace) -> int:
    try:
        from octane_capital.engine import OctaneCapitalEngine

        OctaneCapitalEngine().run_paper_cycle()
        return 0
    except ValueError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Paper cycle failed: {e}", file=sys.stderr)
        return 1


def cmd_proposals(args: argparse.Namespace) -> int:
    repo = VaultRepository()
    status = ProposalStatus(args.status) if args.status else None
    proposals = repo.list_proposals(status=status)
    for p in proposals:
        print(f"{p.id[:8]}  {p.ticker:6}  {p.action.value:4}  {p.status.value:14}  conf={p.confidence_score:.1f}")
    print(f"\n{len(proposals)} proposal(s)")
    return 0


def cmd_risk_check(args: argparse.Namespace) -> int:
    repo = VaultRepository()
    proposal = repo.get_proposal(args.proposal_id)
    if not proposal:
        print(f"Proposal not found: {args.proposal_id}", file=sys.stderr)
        return 1

    broker = PaperBroker()
    portfolio = broker.portfolio_context()
    decision = RiskEngine().evaluate(proposal, portfolio, live_execution=args.live)
    repo.save_risk_decision(proposal.id, decision)

    print(json.dumps(decision.model_dump(mode="json"), indent=2, default=str))
    return 0


def cmd_approve(args: argparse.Namespace) -> int:
    repo = VaultRepository()
    if not repo.update_proposal_status(args.proposal_id, ProposalStatus.APPROVED):
        print(f"Proposal not found: {args.proposal_id}", file=sys.stderr)
        return 1
    print(f"Approved proposal {args.proposal_id}")
    return 0


def cmd_cancel(args: argparse.Namespace) -> int:
    repo = VaultRepository()
    if not repo.update_proposal_status(args.proposal_id, ProposalStatus.CANCELLED):
        print(f"Proposal not found: {args.proposal_id}", file=sys.stderr)
        return 1
    print(f"Cancelled proposal {args.proposal_id}")
    return 0


def cmd_execute(args: argparse.Namespace) -> int:
    repo = VaultRepository()
    proposal = repo.get_proposal(args.proposal_id)
    if not proposal:
        print(f"Proposal not found: {args.proposal_id}", file=sys.stderr)
        return 1

    decision = repo.get_risk_decision(args.proposal_id)
    if not decision:
        print("No risk decision found — run risk-check first", file=sys.stderr)
        return 1

    dry_run = not args.live
    if args.live and not config.ENABLE_LIVE_TRADING:
        print("ENABLE_LIVE_TRADING=false — live execution blocked", file=sys.stderr)
        return 1

    if args.live and proposal.status != ProposalStatus.APPROVED:
        print("Proposal must be approved before live execution", file=sys.stderr)
        return 1

    from octane_capital.data.market_data import MarketData
    try:
        price = MarketData().get_price(proposal.ticker)  # live: prefer Robinhood MCP quote
    except Exception as e:
        print(f"Could not fetch price for {proposal.ticker}: {e}", file=sys.stderr)
        return 1

    guard = ExecutionGuard()
    order = order_from_proposal(proposal, decision, dry_run=dry_run, price=price)
    already = proposal.status == ProposalStatus.EXECUTED
    auth = guard.authorize_order(proposal, decision, order, already_executed=already)
    if not auth.authorized and not dry_run:
        print(f"Execution blocked: {auth.reason}", file=sys.stderr)
        return 1

    if config.TRADING_MODE == TradingMode.PAPER.value or dry_run:
        broker = PaperBroker()
        broker.set_price(proposal.ticker, price)
        preview = broker.preview_order(order)
        print(json.dumps(preview.model_dump(mode="json"), indent=2))
        if not dry_run:
            result = broker.place_order(order)
            repo.save_order_result(result)
            if result.submitted:
                repo.update_proposal_status(proposal.id, ProposalStatus.EXECUTED)
            print(json.dumps(result.model_dump(mode="json"), indent=2, default=str))
    else:
        broker = RobinhoodMCPBroker(guard)
        preview = broker.preview_order(order)
        print(json.dumps(preview.model_dump(mode="json"), indent=2))
        if not dry_run:
            result = broker.place_order(order, proposal=proposal, risk_decision=decision)
            repo.save_order_result(result)
            if result.submitted:
                repo.update_proposal_status(proposal.id, ProposalStatus.EXECUTED)
            print(json.dumps(result.model_dump(mode="json"), indent=2, default=str))

    return 0


def cmd_grade(args: argparse.Namespace) -> int:
    repo = VaultRepository()
    proposal = repo.get_proposal(args.proposal_id)
    if not proposal:
        print(f"Proposal not found: {args.proposal_id}", file=sys.stderr)
        return 1

    entry = args.entry_price
    exit_price = args.exit_price
    pnl_pct = (exit_price - entry) / entry if entry else 0.0

    grade = TradeGrade(
        proposal_id=proposal.id,
        ticker=proposal.ticker,
        strategy=proposal.strategy,
        entry_price=entry,
        current_or_exit_price=exit_price,
        pnl_pct=pnl_pct,
        thesis_correct=pnl_pct > 0,
        timing_score=args.timing_score,
        risk_management_score=args.risk_score,
        lesson=args.lesson or "Post-trade review recorded",
        should_repeat_strategy=pnl_pct > 0,
    )
    repo.save_grade(grade)
    print(json.dumps(grade.model_dump(mode="json"), indent=2, default=str))
    return 0


def cmd_swing(_args: argparse.Namespace) -> int:
    from octane_capital.data.market_data import MarketData
    from octane_capital.strategies.swing import generate_swing_proposals

    md = MarketData()
    broker = PaperBroker(market_data=md)
    equity = broker.get_account().equity
    proposals = generate_swing_proposals(config.WATCHLIST, md, config, equity)
    portfolio = broker.portfolio_context()
    repo = VaultRepository()
    grades = repo.grades_by_strategy()
    decisions = RiskEngine().evaluate_batch(proposals, portfolio, grades_by_strategy=grades)
    for p in proposals:
        d = decisions[p.id]
        repo.save_proposal(p)
        repo.save_risk_decision(p.id, d)
        flag = "APPROVED" if d.approved else "rejected"
        size = d.adjusted_notional or 0.0
        print(f"{p.id[:8]}  {p.ticker:6} score={p.confidence_score:4.1f}  {flag:9} "
              f"size=${size:6.2f} stop={p.stop_price}")
    print(f"\n{len(proposals)} proposal(s) from {len(config.WATCHLIST)} tickers "
          f"(approve one, then: execute --proposal-id <id>)")
    return 0


def cmd_scoreboard(_args: argparse.Namespace) -> int:
    from octane_capital.strategies.scoreboard import summarize, trust_multiplier

    repo = VaultRepository()
    data = repo.grades_by_strategy()
    if not data:
        print("No graded trades yet — grade some trades first.")
        return 0
    for strat, grades in data.items():
        s = summarize(grades, strat)
        print(f"{strat}: n={s.n} win={s.win_rate:.0%} avgPnL={s.avg_pnl_pct:+.1%} "
              f"PF={s.profit_factor:.2f} trust={trust_multiplier(s):.2f}")
    return 0


def cmd_backtest(args: argparse.Namespace) -> int:
    engine = BacktestEngine()
    # Demo historical data for CLI smoke test
    historical = {
        "NVDA": [{"date": f"2024-01-{d:02d}", "close": 100 + d} for d in range(1, 31)],
    }
    signals = [{"ticker": "NVDA", "confidence": 8.5, "entry_idx": 0, "hold_days": 10}]
    result = engine.run(signals, historical, starting_cash=args.cash)
    print(json.dumps(result.model_dump(mode="json"), indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="octane_capital",
        description="Octane Capital Lab — research, paper trading, and risk-limited execution.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("research", help="Run Scout/Auditor research cycle (no trading)").set_defaults(
        func=cmd_research
    )
    sub.add_parser("paper", help="Run research + paper trade simulation").set_defaults(func=cmd_paper)

    p = sub.add_parser("proposals", help="List trade proposals")
    p.add_argument("--status", choices=[s.value for s in ProposalStatus], default=None)
    p.set_defaults(func=cmd_proposals)

    p = sub.add_parser("risk-check", help="Evaluate proposal against risk engine")
    p.add_argument("--proposal-id", required=True)
    p.add_argument("--live", action="store_true", help="Evaluate for live execution")
    p.set_defaults(func=cmd_risk_check)

    p = sub.add_parser("approve", help="Approve a proposal for execution")
    p.add_argument("--proposal-id", required=True)
    p.set_defaults(func=cmd_approve)

    p = sub.add_parser("cancel", help="Cancel a proposal")
    p.add_argument("--proposal-id", required=True)
    p.set_defaults(func=cmd_cancel)

    p = sub.add_parser("execute", help="Execute or preview a proposal order")
    p.add_argument("--proposal-id", required=True)
    p.add_argument("--live", action="store_true", help="Live execution (requires approval)")
    p.set_defaults(func=cmd_execute)

    p = sub.add_parser("grade", help="Grade a completed trade")
    p.add_argument("--proposal-id", required=True)
    p.add_argument("--entry-price", type=float, required=True)
    p.add_argument("--exit-price", type=float, required=True)
    p.add_argument("--timing-score", type=float, default=7.0)
    p.add_argument("--risk-score", type=float, default=7.0)
    p.add_argument("--lesson", default="")
    p.set_defaults(func=cmd_grade)

    p = sub.add_parser("backtest", help="Run a demo backtest")
    p.add_argument("--cash", type=float, default=10000)
    p.set_defaults(func=cmd_backtest)

    sub.add_parser("swing", help="Indicator-driven swing scan -> scored proposals").set_defaults(
        func=cmd_swing
    )
    sub.add_parser("scoreboard", help="Per-strategy graded performance").set_defaults(
        func=cmd_scoreboard
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
