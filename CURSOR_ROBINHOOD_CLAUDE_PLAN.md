# Cursor Build Plan — Octane Capital Lab

> Goal: turn the existing `NonstopAgent/HedgeFund` research prototype into a safe, Claude-powered, Robinhood-ready AI trading lab.
>
> Important framing: this is **not** a public hedge fund, registered investment adviser, or system for managing outside capital. Build it first as a private research, paper-trading, and tightly risk-limited execution system for a Robinhood Agentic Trading account.

---

## 0. Current repo diagnosis

The project already has the right early idea: a multi-agent research engine that scans for AI/semiconductor alpha signals, audits high-conviction tickers, and stores reports.

Current pieces:

- `README.md` describes **Octane Global Trust - Predator Investment Engine**.
- `scout.py` creates the Scout agent for AI/semiconductor signal discovery.
- `auditor.py` creates the Auditor agent for due diligence.
- `models.py` has `ScoutSignal`, `AuditReport`, and related Pydantic models.
- `database.py` stores ticker reports in Supabase.
- `predator_engine.py` tries to orchestrate Scout → CIO review → Auditor → Vault.

Current blockers:

1. **Security issue:** the repo contains a hardcoded Perplexity API key in README/config. Remove it immediately and rotate the key.
2. **Structure mismatch:** `predator_engine.py` imports `agents.manager`, `agents.scout`, `agents.auditor`, and `vault.database`, but the files appear to be root-level.
3. **No Robinhood layer yet:** there is no broker adapter, order model, trade proposal model, position sizing, execution guard, or paper trading.
4. **No backtesting yet:** the system can generate research, but it cannot prove whether strategies work.
5. **No risk engine yet:** this must exist before any live trade execution.
6. **No approval workflow yet:** the system needs explicit review gates before live orders.
7. **No audit trail for trades:** research reports are stored, but trade decisions, rejected trades, and executed trades need durable logs.

---

## 1. Product direction

Rename the project internally from **Predator Investment Engine** to:

```text
Octane Capital Lab
```

Brand meaning:

- **Octane** = AI command system.
- **Capital Lab** = research, simulation, and risk-limited execution.
- Avoid claiming this is a legal hedge fund until legal/regulatory structure exists.

Core thesis:

```text
Claude researches and reasons.
Octane scores and risk-checks.
Robinhood executes only after approval and hard limits.
The system learns from every trade outcome.
```

Do not build this as:

```text
Claude, pick stocks and make me rich.
```

Build this as:

```text
Evidence → Thesis → Risk check → Paper trade → Human approval → Limited live execution → Post-trade grading
```

---

## 2. Target architecture

Final high-level architecture:

```text
                 ┌─────────────────────┐
                 │   Market Data Layer  │
                 │ prices/news/filings  │
                 └──────────┬──────────┘
                            │
                            ▼
┌─────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│   Scout     │───▶│   Claude CIO Agent   │───▶│   Trade Proposal     │
│ signals     │    │ thesis + reasoning   │    │ structured JSON      │
└─────────────┘    └─────────────────────┘    └──────────┬──────────┘
                                                          │
                                                          ▼
                                               ┌─────────────────────┐
                                               │    Risk Engine       │
                                               │ limits + blockers    │
                                               └──────────┬──────────┘
                                                          │
                        ┌─────────────────────────────────┴────────────────────────────────┐
                        ▼                                                                  ▼
          ┌─────────────────────────┐                                      ┌─────────────────────────┐
          │ Rejected / Needs Review │                                      │ Approved Proposal        │
          │ stored in Vault         │                                      │ paper/live candidate     │
          └─────────────────────────┘                                      └──────────┬──────────────┘
                                                                                      │
                                                                                      ▼
                                                                            ┌─────────────────┐
                                                                            │ Paper Broker     │
                                                                            │ then Robinhood   │
                                                                            └────────┬────────┘
                                                                                     │
                                                                                     ▼
                                                                            ┌─────────────────┐
                                                                            │ Trade Journal    │
                                                                            │ grading/memory   │
                                                                            └─────────────────┘
```

---

## 3. Build modes

Implement strict modes. The app must never accidentally jump to live trading.

```python
TRADING_MODE = "research" | "paper" | "proposal" | "live_manual" | "live_limited"
```

Mode behavior:

| Mode | Behavior |
|---|---|
| `research` | Run Scout/Auditor/CIO only. No orders. |
| `paper` | Simulate trades with fake capital. No Robinhood orders. |
| `proposal` | Create live trade proposals but do not execute. |
| `live_manual` | Requires explicit human confirmation before each order. |
| `live_limited` | Allows limited autonomous execution only inside hard risk caps. Disable by default. |

Default must be:

```env
TRADING_MODE=research
ENABLE_LIVE_TRADING=false
```

Live execution must require both:

```env
TRADING_MODE=live_manual
ENABLE_LIVE_TRADING=true
```

Never allow live execution from default config.

---

## 4. New repo structure

Refactor into this structure:

```text
HedgeFund/
├── octane_capital/
│   ├── __init__.py
│   ├── config.py
│   ├── models.py
│   │
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── scout.py
│   │   ├── auditor.py
│   │   ├── cio.py
│   │   └── critic.py
│   │
│   ├── broker/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── paper_broker.py
│   │   ├── robinhood_mcp.py
│   │   └── execution_guard.py
│   │
│   ├── data/
│   │   ├── __init__.py
│   │   ├── market_data.py
│   │   ├── filings.py
│   │   ├── news.py
│   │   └── prices.py
│   │
│   ├── risk/
│   │   ├── __init__.py
│   │   ├── risk_engine.py
│   │   ├── position_sizing.py
│   │   └── rules.py
│   │
│   ├── strategies/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── ai_semiconductor_momentum.py
│   │   └── watchlist_strategy.py
│   │
│   ├── backtest/
│   │   ├── __init__.py
│   │   ├── engine.py
│   │   ├── metrics.py
│   │   └── walk_forward.py
│   │
│   ├── vault/
│   │   ├── __init__.py
│   │   ├── database.py
│   │   ├── migrations.sql
│   │   └── repository.py
│   │
│   ├── engine.py
│   └── cli.py
│
├── tests/
│   ├── test_risk_engine.py
│   ├── test_trade_proposals.py
│   ├── test_paper_broker.py
│   └── test_config_safety.py
│
├── scripts/
│   ├── run_research.py
│   ├── run_paper_cycle.py
│   └── print_risk_config.py
│
├── .env.example
├── requirements.txt
├── README.md
└── CURSOR_ROBINHOOD_CLAUDE_PLAN.md
```

Cursor should migrate code gradually instead of rewriting everything at once.

---

## 5. Immediate security tasks

### 5.1 Remove exposed key

Remove all hardcoded API keys from:

- `README.md`
- `config.py`
- any examples
- comments
- tests

Use placeholders only:

```env
PERPLEXITY_API_KEY=your_perplexity_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here
SUPABASE_URL=your_supabase_url_here
SUPABASE_KEY=your_supabase_key_here
```

### 5.2 Config must fail closed

`config.py` should never contain real fallback keys.

Bad:

```python
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY", "real-key-here")
```

Good:

```python
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
```

If a required key is missing, the feature should disable itself or raise a clear error depending on mode.

### 5.3 Add `.gitignore`

Ensure:

```text
.env
.env.*
!.env.example
__pycache__/
.pytest_cache/
.venv/
venv/
*.db
*.sqlite
.DS_Store
```

### 5.4 Add `.env.example`

```env
# AI providers
ANTHROPIC_API_KEY=
PERPLEXITY_API_KEY=
PERPLEXITY_BASE_URL=https://api.perplexity.ai

# Supabase
SUPABASE_URL=
SUPABASE_KEY=

# Trading safety
TRADING_MODE=research
ENABLE_LIVE_TRADING=false
REQUIRE_HUMAN_APPROVAL=true

# Risk limits
STARTING_PAPER_CASH=10000
MAX_POSITION_PCT=0.05
MAX_SINGLE_TRADE_DOLLARS=250
MAX_DAILY_LOSS_PCT=0.02
MAX_WEEKLY_LOSS_PCT=0.05
MAX_OPEN_POSITIONS=5
ALLOW_OPTIONS=false
ALLOW_MARGIN=false
ALLOW_SHORTS=false
ALLOW_CRYPTO=false

# Robinhood MCP
ROBINHOOD_MCP_SERVER=https://agent.robinhood.com/mcp/trading
```

---

## 6. Core data models

Expand `models.py` with separate research, proposal, risk, order, and result models.

### 6.1 Enums

```python
from enum import Enum

class TradeAction(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    TRIM = "TRIM"
    EXIT = "EXIT"

class AssetClass(str, Enum):
    EQUITY = "EQUITY"
    OPTION = "OPTION"
    CRYPTO = "CRYPTO"

class TradingMode(str, Enum):
    RESEARCH = "research"
    PAPER = "paper"
    PROPOSAL = "proposal"
    LIVE_MANUAL = "live_manual"
    LIVE_LIMITED = "live_limited"

class ProposalStatus(str, Enum):
    DRAFT = "draft"
    RISK_REJECTED = "risk_rejected"
    NEEDS_REVIEW = "needs_review"
    APPROVED = "approved"
    EXECUTED = "executed"
    CANCELLED = "cancelled"
```

### 6.2 Trade proposal model

```python
class ExitRules(BaseModel):
    stop_loss_pct: float = Field(..., ge=0.0, le=0.5)
    take_profit_pct: Optional[float] = Field(None, ge=0.0, le=2.0)
    max_hold_days: int = Field(..., ge=1, le=365)
    invalidation_events: List[str] = Field(default_factory=list)

class TradeProposal(BaseModel):
    id: str
    created_at: datetime
    ticker: str
    company_name: Optional[str] = None
    asset_class: AssetClass = AssetClass.EQUITY
    action: TradeAction
    thesis: str
    evidence: List[str]
    source_urls: List[str] = Field(default_factory=list)
    confidence_score: float = Field(..., ge=0.0, le=10.0)
    risk_level: str
    time_horizon: str
    requested_position_pct: float = Field(..., ge=0.0, le=1.0)
    requested_notional: Optional[float] = None
    exit_rules: ExitRules
    status: ProposalStatus = ProposalStatus.DRAFT
    requires_human_approval: bool = True
    source_report_id: Optional[str] = None
```

### 6.3 Risk decision model

```python
class RiskDecision(BaseModel):
    approved: bool
    decision: str  # APPROVED, REJECTED, NEEDS_REVIEW
    reasons: List[str]
    adjusted_position_pct: Optional[float] = None
    adjusted_notional: Optional[float] = None
    max_allowed_loss: Optional[float] = None
    checked_at: datetime
```

### 6.4 Order request model

```python
class OrderRequest(BaseModel):
    proposal_id: str
    ticker: str
    action: TradeAction
    quantity: Optional[float] = None
    notional: Optional[float] = None
    order_type: str = "market"
    time_in_force: str = "day"
    dry_run: bool = True
```

### 6.5 Trade result model

```python
class TradeResult(BaseModel):
    proposal_id: str
    broker: str
    mode: TradingMode
    submitted: bool
    broker_order_id: Optional[str] = None
    filled_quantity: Optional[float] = None
    average_fill_price: Optional[float] = None
    error: Optional[str] = None
    executed_at: datetime
```

### 6.6 Post-trade grade model

```python
class TradeGrade(BaseModel):
    proposal_id: str
    ticker: str
    entry_price: float
    current_or_exit_price: float
    pnl_pct: float
    thesis_correct: Optional[bool] = None
    timing_score: float = Field(..., ge=0.0, le=10.0)
    risk_management_score: float = Field(..., ge=0.0, le=10.0)
    lesson: str
    should_repeat_strategy: bool
    graded_at: datetime
```

---

## 7. Claude CIO agent

Add `octane_capital/agents/cio.py`.

Purpose:

- Read Scout signals and Auditor reports.
- Decide whether a ticker deserves a trade proposal.
- Produce strict JSON matching `TradeProposal`.
- Never directly place orders.
- Always include risk factors and exit rules.

System rules for Claude CIO:

```text
You are Octane Capital Lab's CIO agent. You do not execute trades. You create structured trade proposals only.

Rules:
1. Never recommend a trade without a clear thesis.
2. Never recommend a trade without risk factors.
3. Never recommend a trade without stop-loss or invalidation rules.
4. Prefer HOLD when evidence is weak.
5. Do not invent sources.
6. Use lower confidence when sources are vague, old, promotional, or not primary.
7. Options, margin, shorts, crypto, and leverage are disabled unless explicitly enabled in config.
8. Your output must be valid JSON matching TradeProposal.
9. The Risk Engine has final authority over position size and approval.
10. This system is for research and planning, not guaranteed profit.
```

CIO input:

```python
ScoutSignal + Optional[AuditReport] + current portfolio + current market context + risk config
```

CIO output:

```python
TradeProposal
```

Also add `octane_capital/agents/critic.py`.

The Critic should review each proposal and look for:

- hallucinated claims
- missing sources
- bad risk/reward
- thesis not connected to trade action
- position too large
- event risk
- hype-driven reasoning

The Critic should return:

```python
class CriticReview(BaseModel):
    passed: bool
    concerns: List[str]
    recommended_changes: List[str]
    confidence_adjustment: float
```

---

## 8. Risk engine

Add `octane_capital/risk/risk_engine.py`.

The Risk Engine must be deterministic. Do not let Claude override it.

### 8.1 Hard rejection rules

Reject proposal if:

```text
- ENABLE_LIVE_TRADING=false and request is live execution
- TRADING_MODE=research and any order is attempted
- action is BUY but confidence_score < 7.5
- ticker is missing or invalid
- asset_class != EQUITY
- ALLOW_OPTIONS=false and proposal is option
- ALLOW_MARGIN=false and proposal needs margin
- ALLOW_SHORTS=false and action implies shorting
- stop_loss_pct is missing
- requested_position_pct > MAX_POSITION_PCT
- requested_notional > MAX_SINGLE_TRADE_DOLLARS
- current daily loss exceeds MAX_DAILY_LOSS_PCT
- current weekly loss exceeds MAX_WEEKLY_LOSS_PCT
- open positions >= MAX_OPEN_POSITIONS
- source_urls empty for live proposals
- thesis shorter than minimum threshold
- risk_level is High and confidence < 9.0
```

### 8.2 Position sizing

Default position sizing:

```python
def calculate_max_notional(account_equity, max_position_pct, max_single_trade_dollars):
    return min(account_equity * max_position_pct, max_single_trade_dollars)
```

Risk-adjusted sizing:

```text
confidence 9.0-10.0 → up to 100% of max allowed
confidence 8.0-8.9 → up to 65% of max allowed
confidence 7.5-7.9 → up to 35% of max allowed
below 7.5 → reject
```

Risk level adjustment:

```text
Low risk → 100% of calculated size
Medium risk → 70%
High risk → 35% or reject depending confidence
```

### 8.3 Approval states

Risk engine result:

```text
APPROVED_FOR_PAPER
APPROVED_FOR_MANUAL_REVIEW
REJECTED
NEEDS_MORE_DATA
```

Never return `APPROVED_FOR_LIVE_AUTO` until the project has a proven paper-trading history.

---

## 9. Broker layer

Add `octane_capital/broker/base.py`.

```python
class BrokerAdapter(Protocol):
    def get_account(self) -> AccountSnapshot: ...
    def get_positions(self) -> List[PositionSnapshot]: ...
    def preview_order(self, order: OrderRequest) -> OrderPreview: ...
    def place_order(self, order: OrderRequest) -> TradeResult: ...
```

### 9.1 Paper broker first

Add `octane_capital/broker/paper_broker.py`.

Requirements:

- Simulate cash.
- Simulate positions.
- Use latest available price or mock price.
- Record fake fills.
- Apply simple slippage assumption.
- Support BUY, SELL, HOLD, EXIT.
- Persist state to Supabase or local JSON.

Paper broker should be the default adapter.

### 9.2 Robinhood MCP adapter

Add `octane_capital/broker/robinhood_mcp.py`.

Purpose:

- Wrap Robinhood Trading MCP calls behind the same broker interface.
- Do not expose MCP calls directly to agents.
- Never let Claude call broker methods without `ExecutionGuard`.

Claude Code MCP setup command for the developer environment:

```bash
claude mcp add robinhood-trading --transport http https://agent.robinhood.com/mcp/trading
```

Then inside Claude Code:

```text
/mcp
```

Select `robinhood-trading` and authenticate.

Implementation note:

Cursor may not be able to directly call the local Claude MCP session from Python. If direct MCP calls are not available from the app runtime, build the adapter as an interface/stub first and keep execution manual. The system can still generate broker-ready proposals.

### 9.3 Execution guard

Add `octane_capital/broker/execution_guard.py`.

This file is the final gate before orders.

ExecutionGuard must check:

```text
- trading mode
- enable live flag
- human approval flag
- risk decision approved
- proposal status approved
- order notional under limits
- asset allowed
- duplicate order prevention
- market hours check if implemented
```

Pseudocode:

```python
def authorize_order(proposal, risk_decision, order, config):
    if config.TRADING_MODE in ["research", "paper", "proposal"]:
        return Authorization(False, "Live execution disabled in this mode")

    if not config.ENABLE_LIVE_TRADING:
        return Authorization(False, "ENABLE_LIVE_TRADING=false")

    if config.REQUIRE_HUMAN_APPROVAL and proposal.status != ProposalStatus.APPROVED:
        return Authorization(False, "Human approval required")

    if not risk_decision.approved:
        return Authorization(False, "Risk engine rejected proposal")

    return Authorization(True, "Authorized")
```

---

## 10. Database schema

Expand Supabase beyond `ticker_reports`.

### 10.1 `ticker_reports`

Keep current table but add:

```sql
ALTER TABLE ticker_reports
ADD COLUMN IF NOT EXISTS source_run_id UUID,
ADD COLUMN IF NOT EXISTS model_provider TEXT,
ADD COLUMN IF NOT EXISTS model_name TEXT,
ADD COLUMN IF NOT EXISTS raw_output JSONB,
ADD COLUMN IF NOT EXISTS data_quality_score NUMERIC;
```

### 10.2 `trade_proposals`

```sql
CREATE TABLE IF NOT EXISTS trade_proposals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticker TEXT NOT NULL,
    company_name TEXT,
    asset_class TEXT NOT NULL DEFAULT 'EQUITY',
    action TEXT NOT NULL,
    thesis TEXT NOT NULL,
    evidence JSONB NOT NULL DEFAULT '[]'::jsonb,
    source_urls JSONB NOT NULL DEFAULT '[]'::jsonb,
    confidence_score NUMERIC NOT NULL,
    risk_level TEXT NOT NULL,
    time_horizon TEXT,
    requested_position_pct NUMERIC,
    requested_notional NUMERIC,
    exit_rules JSONB NOT NULL DEFAULT '{}'::jsonb,
    status TEXT NOT NULL DEFAULT 'draft',
    requires_human_approval BOOLEAN NOT NULL DEFAULT true,
    source_report_id BIGINT,
    raw_cio_output JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_trade_proposals_created_at ON trade_proposals(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_trade_proposals_ticker ON trade_proposals(ticker);
CREATE INDEX IF NOT EXISTS idx_trade_proposals_status ON trade_proposals(status);
```

### 10.3 `risk_decisions`

```sql
CREATE TABLE IF NOT EXISTS risk_decisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    proposal_id UUID REFERENCES trade_proposals(id),
    approved BOOLEAN NOT NULL,
    decision TEXT NOT NULL,
    reasons JSONB NOT NULL DEFAULT '[]'::jsonb,
    adjusted_position_pct NUMERIC,
    adjusted_notional NUMERIC,
    max_allowed_loss NUMERIC,
    config_snapshot JSONB NOT NULL DEFAULT '{}'::jsonb,
    checked_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_risk_decisions_proposal_id ON risk_decisions(proposal_id);
```

### 10.4 `orders`

```sql
CREATE TABLE IF NOT EXISTS orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    proposal_id UUID REFERENCES trade_proposals(id),
    broker TEXT NOT NULL,
    mode TEXT NOT NULL,
    ticker TEXT NOT NULL,
    action TEXT NOT NULL,
    quantity NUMERIC,
    notional NUMERIC,
    order_type TEXT,
    time_in_force TEXT,
    submitted BOOLEAN NOT NULL DEFAULT false,
    broker_order_id TEXT,
    filled_quantity NUMERIC,
    average_fill_price NUMERIC,
    error TEXT,
    executed_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_orders_proposal_id ON orders(proposal_id);
CREATE INDEX IF NOT EXISTS idx_orders_ticker ON orders(ticker);
```

### 10.5 `trade_grades`

```sql
CREATE TABLE IF NOT EXISTS trade_grades (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    proposal_id UUID REFERENCES trade_proposals(id),
    ticker TEXT NOT NULL,
    entry_price NUMERIC,
    current_or_exit_price NUMERIC,
    pnl_pct NUMERIC,
    thesis_correct BOOLEAN,
    timing_score NUMERIC,
    risk_management_score NUMERIC,
    lesson TEXT,
    should_repeat_strategy BOOLEAN,
    graded_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 11. Engine flow

Replace `PredatorEngine.run()` with a more explicit pipeline.

```python
class OctaneCapitalEngine:
    def run_research_cycle(self):
        scout_signals = self.scout.find_signals()
        audit_reports = self.auditor.audit_high_confidence(scout_signals)
        proposals = self.cio.create_trade_proposals(scout_signals, audit_reports)
        critic_reviews = self.critic.review(proposals)
        risk_decisions = self.risk_engine.evaluate(proposals)
        self.vault.save_cycle(...)
        return ResearchCycleResult(...)

    def run_paper_cycle(self):
        result = self.run_research_cycle()
        for proposal in result.approved_for_paper:
            order = self.order_factory.from_proposal(proposal)
            self.paper_broker.place_order(order)

    def run_live_manual_cycle(self):
        result = self.run_research_cycle()
        return result.proposals_needing_approval
```

Do not implement live autonomous trading yet.

---

## 12. Strategy layer

Add a strategy abstraction.

```python
class Strategy(Protocol):
    name: str
    def generate_candidates(self, context: MarketContext) -> List[ScoutSignal]: ...
    def create_proposal(self, candidate: ScoutSignal, audit: Optional[AuditReport]) -> TradeProposal: ...
```

First strategy:

```text
AI Semiconductor Momentum Strategy
```

Rules:

- Universe: large and mid-cap AI/semiconductor equities only.
- Evidence required: at least 2 independent sources.
- Minimum Scout score: 7.5.
- Audit required above 8.0.
- Avoid trade if earnings are within a configurable blackout window.
- No options.
- No leverage.

Second strategy:

```text
Watchlist Strategy
```

Manual watchlist of tickers you care about.

`.env`:

```env
WATCHLIST=NVDA,AMD,TSM,AVGO,MSFT,GOOGL,META,AMZN,PLTR,ARM
```

---

## 13. Backtesting requirements

Add a basic backtest engine before live trading.

Minimum metrics:

```text
- total return
- max drawdown
- win rate
- average win
- average loss
- profit factor
- Sharpe-like ratio if possible
- number of trades
- average hold duration
```

Backtest assumptions must be conservative:

```text
- include transaction costs
- include slippage
- no lookahead bias
- no using future news to justify past trades
- separate train/test periods if strategy parameters are tuned
```

Basic backtest class:

```python
class BacktestEngine:
    def run(self, strategy, historical_data, starting_cash):
        # simulate proposals, risk decisions, fills, exits
        return BacktestResult(...)
```

Do not let Cursor overcomplicate this. First version can be simple daily-close simulation.

---

## 14. CLI commands

Add a CLI so the system can be run safely.

```bash
python -m octane_capital.cli research
python -m octane_capital.cli paper
python -m octane_capital.cli proposals
python -m octane_capital.cli risk-check --proposal-id <id>
python -m octane_capital.cli approve --proposal-id <id>
python -m octane_capital.cli execute --proposal-id <id> --dry-run
python -m octane_capital.cli execute --proposal-id <id> --live
python -m octane_capital.cli grade --proposal-id <id>
```

Rules:

- `execute --live` must fail unless `ENABLE_LIVE_TRADING=true`.
- `execute --live` must fail unless proposal was approved.
- `execute --live` must fail if risk decision is stale.
- Default should always be dry-run.

---

## 15. Tests Cursor must write

### 15.1 Config safety tests

Test:

```text
- default trading mode is research
- live trading is disabled by default
- missing keys do not silently use fake/real fallback keys
- .env is ignored
```

### 15.2 Risk engine tests

Test rejection when:

```text
- confidence below threshold
- position too large
- stop loss missing
- high risk + low confidence
- options disabled
- live trading disabled
- daily loss limit hit
- too many open positions
```

Test approval when:

```text
- equity trade
- confidence high enough
- sourced thesis
- stop loss present
- position inside limits
- paper mode
```

### 15.3 Paper broker tests

Test:

```text
- buying reduces cash
- selling increases cash
- cannot buy more than cash
- positions update correctly
- order result is stored
```

### 15.4 Proposal parsing tests

Test:

```text
- valid CIO JSON becomes TradeProposal
- invalid JSON fails safely
- missing thesis fails validation
- missing exit rules fails validation
```

---

## 16. Cursor prompt to use

Paste this into Cursor as the first instruction:

```text
You are working in the NonstopAgent/HedgeFund repo. Your job is to turn the current CrewAI/Perplexity investment research prototype into Octane Capital Lab: a safe Claude-powered research, paper-trading, and Robinhood-ready trading system.

Important safety rules:
- Do NOT implement uncontrolled live trading.
- Do NOT let any LLM place trades directly.
- Do NOT hardcode API keys.
- Remove any exposed API keys from README/config and replace with env placeholders.
- Default mode must be research-only.
- Live trading must require ENABLE_LIVE_TRADING=true, TRADING_MODE=live_manual, human approval, and risk-engine approval.
- Build paper trading before live Robinhood execution.
- Broker execution must go through ExecutionGuard.

Current repo issues:
- predator_engine.py imports agents.manager/agents.scout/agents.auditor/vault.database, but files appear root-level.
- README/config contain a hardcoded Perplexity key that must be removed.
- There is no broker layer, risk engine, trade proposal model, or paper broker yet.

Implement in phases:

Phase 1:
1. Create clean package structure under octane_capital/.
2. Move/refactor existing scout.py, auditor.py, database.py, models.py into the package.
3. Fix imports.
4. Add .env.example and .gitignore.
5. Remove all hardcoded secrets.
6. Make python -m octane_capital.cli research run without import errors.

Phase 2:
1. Add TradeProposal, ExitRules, RiskDecision, OrderRequest, TradeResult, TradeGrade models.
2. Add deterministic RiskEngine.
3. Add tests for risk rejection/approval.

Phase 3:
1. Add Claude CIO agent that creates structured TradeProposal JSON.
2. Add Critic agent that reviews proposals for hallucinations, weak evidence, and missing risk controls.
3. CIO and Critic must never execute trades.

Phase 4:
1. Add PaperBroker.
2. Add CLI command for paper trading.
3. Store paper trades and proposals.

Phase 5:
1. Add RobinhoodMCPBroker adapter interface only.
2. Add ExecutionGuard.
3. Keep live execution disabled by default.
4. Add dry-run order preview flow.

Phase 6:
1. Add backtesting module.
2. Add basic daily-close simulation.
3. Add metrics: return, max drawdown, win rate, profit factor, average hold duration.

Do not do every phase in one giant change. Start with Phase 1 and make sure tests/imports pass before moving on.
```

---

## 17. Smaller Cursor task prompts

Use these one at a time.

### Task 1 — Security cleanup

```text
Clean up secrets in this repo. Remove any hardcoded API keys from README.md, config.py, examples, and comments. Add .env.example with placeholders only. Add or update .gitignore so .env files are never committed. Config must read keys from environment only and never use a real fallback key. Do not change trading logic yet.
```

### Task 2 — Package refactor

```text
Refactor the project into an octane_capital Python package. Move existing scout.py, auditor.py, database.py, models.py, config.py, and predator_engine.py into the package structure. Fix broken imports. Add octane_capital/cli.py with a research command. Preserve current behavior as much as possible. Do not add Robinhood yet.
```

### Task 3 — Trade models

```text
Add Pydantic models for TradeProposal, ExitRules, RiskDecision, OrderRequest, TradeResult, TradeGrade, TradingMode, TradeAction, AssetClass, and ProposalStatus. Keep existing ScoutSignal and AuditReport models. Add validation so proposals require thesis, evidence, confidence score, risk level, requested position size, and exit rules.
```

### Task 4 — Risk engine

```text
Create a deterministic RiskEngine that evaluates TradeProposal objects against config limits. It should reject low confidence, missing stop loss, oversized positions, disabled asset classes, missing sources for live proposals, max daily loss breach, max weekly loss breach, and too many open positions. Add unit tests for approvals and rejections.
```

### Task 5 — Paper broker

```text
Create BrokerAdapter protocol and PaperBroker implementation. PaperBroker should simulate cash, positions, buys, sells, exits, and trade results. It should reject orders that exceed available cash. Add tests showing cash and positions update correctly.
```

### Task 6 — Claude CIO

```text
Create a Claude CIO agent module that takes ScoutSignal and AuditReport inputs and outputs strict TradeProposal JSON. The CIO must not place trades. It must include thesis, evidence, risk factors, confidence score, requested position size, and exit rules. Add parser logic that fails safely if Claude returns invalid JSON.
```

### Task 7 — Robinhood adapter stub

```text
Create RobinhoodMCPBroker adapter stub behind the BrokerAdapter interface. Do not execute real trades yet. Add methods for get_account, get_positions, preview_order, and place_order, but make place_order raise unless live trading is enabled and ExecutionGuard authorizes it. Include comments for Claude Code MCP setup.
```

### Task 8 — Approval workflow

```text
Add proposal status flow: draft → risk_rejected / needs_review / approved → executed / cancelled. Add CLI commands to list proposals, approve a proposal, cancel a proposal, and execute a proposal in dry-run mode. Live execution should remain disabled unless config explicitly enables it.
```

### Task 9 — Backtest engine

```text
Add a simple backtest engine that can simulate strategy proposals over historical daily prices. Include transaction cost and slippage assumptions. Return total return, max drawdown, win rate, average win, average loss, profit factor, number of trades, and average hold duration.
```

---

## 18. Definition of done

Phase 1 done when:

```text
- no secrets in repo
- imports fixed
- .env.example exists
- python -m octane_capital.cli research works
- README updated with safe setup instructions
```

Phase 2 done when:

```text
- trade proposal models exist
- risk engine exists
- tests cover main rejection rules
```

Phase 3 done when:

```text
- Claude CIO can generate structured proposal JSON
- invalid outputs fail safely
- Critic can flag weak proposals
```

Phase 4 done when:

```text
- paper broker can simulate trades
- proposal → risk decision → paper order → trade result is stored
```

Phase 5 done when:

```text
- Robinhood MCP adapter exists behind interface
- ExecutionGuard blocks unsafe live orders
- dry-run works
- live trading still disabled by default
```

Phase 6 done when:

```text
- basic backtest runs
- metrics are printed
- strategy performance can be compared before live trading
```

---

## 19. Non-negotiable safety rules

Cursor must preserve these rules permanently:

```text
1. No hardcoded secrets.
2. No live trading by default.
3. No direct LLM-to-broker execution.
4. RiskEngine must be deterministic.
5. ExecutionGuard is the final gate.
6. Human approval required before live orders.
7. Paper trading comes before live trading.
8. Every proposal, rejection, approval, order, and result must be logged.
9. Claude can reason, but rules decide.
10. The system must fail closed, not open.
```

---

## 20. First commit recommendation

First commit should only do:

```text
security-cleanup-and-package-refactor
```

Do not include Robinhood execution in the first commit.

Suggested commit message:

```text
Secure config and refactor Octane Capital package
```

Second commit:

```text
Add trade proposal models and deterministic risk engine
```

Third commit:

```text
Add paper broker and proposal workflow
```

Fourth commit:

```text
Add Claude CIO proposal generation
```

Fifth commit:

```text
Add guarded Robinhood MCP adapter stub
```
