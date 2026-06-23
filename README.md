# Octane Capital Lab

A safe, Claude-ready research and risk-limited trading system built on CrewAI and Perplexity Sonar API.

**Important:** This is a private research and paper-trading lab — not a registered investment adviser or public hedge fund. Live trading is disabled by default.

## Architecture

- **The Scout** (`sonar-reasoning-pro`) — scans for alpha signals in AI/semiconductor equities
- **The Auditor** (`sonar-deep-research`) — deep-dive due diligence on high-confidence tickers
- **The CIO** — hierarchical manager coordinating Scout and Auditor (research only, no orders)
- **The Vault** — Supabase storage for research reports

See `CURSOR_ROBINHOOD_CLAUDE_PLAN.md` for the full build roadmap.

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment

Copy the example file and add your keys:

```bash
cp .env.example .env
```

Required for research:

```env
PERPLEXITY_API_KEY=your_perplexity_key_here
```

Optional:

```env
SUPABASE_URL=your_supabase_url_here
SUPABASE_KEY=your_supabase_key_here
GHOST_MODE=false
```

**Never commit `.env` or hardcode API keys.** If a key was ever exposed in git history, rotate it immediately.

### 3. Supabase (optional)

```sql
CREATE TABLE ticker_reports (
    id BIGSERIAL PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL,
    company_name TEXT,
    scout_confidence DECIMAL(3,1),
    alpha_signals JSONB,
    signal_sources JSONB,
    scout_summary TEXT,
    audit_performed BOOLEAN DEFAULT FALSE,
    audit_data JSONB,
    revised_confidence DECIMAL(3,1),
    risk_level VARCHAR(20),
    investment_thesis TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

## Usage

### Run research (default mode)

```bash
python -m octane_capital.cli research
```

Or via the convenience script:

```bash
python scripts/run_research.py
```

### Trading safety defaults

```env
TRADING_MODE=research
ENABLE_LIVE_TRADING=false
```

Live execution requires explicit configuration and is not implemented in Phase 1.

## Project structure

```text
octane_capital/
├── agents/          # Scout, Auditor, CIO
├── vault/           # Supabase storage
├── llm/             # Perplexity integrations
├── config.py        # Environment-based configuration
├── models.py        # Pydantic research models
├── engine.py        # Research orchestration
└── cli.py           # CLI entry point
```

## Development phases

1. **Phase 1** (current) — security cleanup, package refactor, research CLI
2. **Phase 2** — trade proposal models and risk engine
3. **Phase 3** — Claude CIO proposal generation
4. **Phase 4** — paper broker
5. **Phase 5** — Robinhood MCP adapter stub + execution guard
6. **Phase 6** — backtesting

---

**Octane Capital Lab** | Research-first, risk-limited by design
