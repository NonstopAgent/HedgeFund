# Octane Capital Lab

Octane Capital Lab is a private research prototype for AI and semiconductor
equity analysis. Phase 1 is research-only: it can run Scout/CIO/Auditor research
flows and optionally store ticker reports in Supabase. It does not implement
Robinhood execution, paper trading, or live trading yet.

## Safety defaults

- No hardcoded API keys.
- Default mode is `TRADING_MODE=research`.
- Live trading is disabled with `ENABLE_LIVE_TRADING=false`.
- Supabase is optional; without credentials, the vault stays in standby mode.
- If a Perplexity key is missing, the research command exits with a clear
  configuration message instead of falling back to any bundled secret.

If you previously committed or shared a real API key, rotate/delete that key
before using the project again.

## Architecture

### The Scout (`sonar-reasoning-pro`)

Scans GitHub, Reddit, and tech news for AI/semiconductor research signals:

- GitHub star spikes
- Developer activity trends
- Reddit sentiment shifts
- Patent filings
- Job postings indicating R&D expansion

### The Auditor (`sonar-deep-research`)

Performs deep-dive audits on tickers with confidence scores above the configured
threshold. It analyzes:

- Technical moats and patents
- SEC filings
- Insider trading patterns
- Financial health metrics

### The Vault (Supabase)

Stores ticker reports, scout signals, and audit findings when Supabase
credentials are provided.

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment

Copy the example file and add your own credentials:

```bash
cp .env.example .env
```

Required for research cycles:

```env
PERPLEXITY_API_KEY=your_rotated_perplexity_key_here
```

Optional Supabase storage:

```env
SUPABASE_URL=your_supabase_url_here
SUPABASE_KEY=your_supabase_key_here
```

Keep the safety defaults unless you are working on a later guarded phase:

```env
TRADING_MODE=research
ENABLE_LIVE_TRADING=false
REQUIRE_HUMAN_APPROVAL=true
```

### 3. Supabase database setup

Create this table if you want persistent ticker reports:

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

CREATE INDEX idx_ticker_reports_created_at ON ticker_reports(created_at DESC);
CREATE INDEX idx_ticker_reports_ticker ON ticker_reports(ticker);
```

## Usage

Run the research command:

```bash
python -m octane_capital.cli research
```

The legacy entry point still delegates to the package:

```bash
python predator_engine.py
```

Set `GHOST_MODE=true` in `.env` for quieter scheduled operation.

## Project structure

```text
.
├── octane_capital/
│   ├── agents/
│   │   ├── auditor.py
│   │   ├── manager.py
│   │   └── scout.py
│   ├── vault/
│   │   └── database.py
│   ├── branding.py
│   ├── cli.py
│   ├── config.py
│   ├── engine.py
│   ├── models.py
│   ├── perplexity_client.py
│   └── perplexity_llm.py
├── .env.example
├── CURSOR_ROBINHOOD_CLAUDE_PLAN.md
├── predator_engine.py
├── requirements.txt
└── README.md
```

## Phase status

Phase 1 complete scope:

- Security cleanup
- Package refactor
- Fixed imports
- `.env.example`
- Research CLI command

Future phases should add trade proposal models, deterministic risk checks, paper
broker simulation, approval workflow, and only then a guarded Robinhood adapter.
