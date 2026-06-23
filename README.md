# Octane Capital Lab

A safe, Claude-ready research and risk-limited trading system built on CrewAI and Perplexity Sonar API.

**Important:** This is a private research and paper-trading lab — not a registered investment adviser or public hedge fund. Live trading is disabled by default.

## Architecture

```text
Scout → Auditor → Proposal CIO → Critic → Risk Engine → Paper Broker / Robinhood (guarded)
```

- **The Scout** (`sonar-reasoning-pro`) — alpha signals in AI/semiconductor equities
- **The Auditor** (`sonar-deep-research`) — due diligence on high-confidence tickers
- **The CIO** (CrewAI) — hierarchical research manager
- **Proposal CIO** (Claude / rule-based fallback) — structured `TradeProposal` JSON
- **The Critic** — flags weak evidence, hype, and missing risk controls
- **Risk Engine** — deterministic limits (Claude cannot override)
- **Paper Broker** — simulated fills before any live execution
- **Execution Guard** — final gate before Robinhood MCP orders
- **The Vault** — Supabase + local JSON for proposals, orders, and grades

See `CURSOR_ROBINHOOD_CLAUDE_PLAN.md` for the full roadmap.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
# Add PERPLEXITY_API_KEY (required for research)
# Add ANTHROPIC_API_KEY (optional — enables Claude proposal CIO)
# Add SUPABASE_URL / SUPABASE_KEY (optional)
```

**Never commit `.env` or hardcode API keys.** Rotate any key that was ever exposed in git history.

Apply database migrations from `octane_capital/vault/migrations.sql` when using Supabase.

## CLI Commands

```bash
python3 -m octane_capital.cli research          # Scout/Auditor cycle, no orders
python3 -m octane_capital.cli paper              # Research + paper broker simulation
python3 -m octane_capital.cli proposals          # List proposals
python3 -m octane_capital.cli risk-check --proposal-id <id>
python3 -m octane_capital.cli approve --proposal-id <id>
python3 -m octane_capital.cli cancel --proposal-id <id>
python3 -m octane_capital.cli execute --proposal-id <id>        # dry-run preview (default)
python3 -m octane_capital.cli execute --proposal-id <id> --live # blocked unless enabled
python3 -m octane_capital.cli grade --proposal-id <id> --entry-price 100 --exit-price 110
python3 -m octane_capital.cli backtest
python3 scripts/print_risk_config.py
```

## Trading Safety Defaults

```env
TRADING_MODE=research
ENABLE_LIVE_TRADING=false
REQUIRE_HUMAN_APPROVAL=true
```

Live execution requires **all** of: `ENABLE_LIVE_TRADING=true`, `TRADING_MODE=live_manual`, human approval, and risk-engine approval.

## Project Structure

```text
octane_capital/
├── agents/       scout, auditor, cio, proposal_cio, critic
├── broker/       paper_broker, robinhood_mcp (stub), execution_guard
├── risk/         risk_engine, position_sizing, rules
├── vault/        database, repository, migrations.sql
├── backtest/     engine, metrics
├── strategies/   ai_semiconductor_momentum, watchlist
├── engine.py     orchestration
└── cli.py        CLI entry point
tests/
scripts/
```

## Tests

```bash
python3 -m pytest tests/ -q
```

## Robinhood MCP (Phase 5 stub)

```bash
claude mcp add robinhood-trading --transport http https://agent.robinhood.com/mcp/trading
```

The Python adapter is a guarded stub — connect MCP manually in Claude Code before live use.

---

**Octane Capital Lab** | Research-first, risk-limited by design
