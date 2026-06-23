# Octane Capital Lab

A safe, multi-agent investment **research** engine built on CrewAI and the
Perplexity Sonar API. The current scope is research and analysis only.

> **Important framing:** This is not a hedge fund, a registered investment
> adviser, or a system for managing outside capital. It is a private research
> tool. Live trading is **not** implemented and is intentionally disabled by
> default. See `CURSOR_ROBINHOOD_CLAUDE_PLAN.md` for the phased roadmap.

## Architecture

### The Scout (`sonar-reasoning-pro`)
Scans GitHub, Reddit, and tech news for alpha signals in AI and semiconductor
stocks (GitHub star spikes, developer activity, sentiment shifts, patent
filings, R&D-related job postings).

### The CIO (`sonar-reasoning-pro`)
Reviews Scout findings and decides which tickers warrant a deep-dive audit.

### The Auditor (`sonar-deep-research`)
Performs deep due diligence on high-confidence tickers: technical moats, SEC
filings, insider trading patterns, and financial health.

### The Vault (Supabase)
Optional persistent storage for ticker reports and audit findings. Runs in
standby mode when no Supabase credentials are provided.

## Project structure

```text
octane_capital/
├── __init__.py
├── config.py             # Fail-closed configuration (no embedded secrets)
├── models.py             # Pydantic models (ScoutSignal, AuditReport, ...)
├── engine.py             # OctaneCapitalEngine research orchestration
├── cli.py                # Command line interface
├── perplexity_client.py  # Perplexity API wrapper (lazy client)
├── perplexity_llm.py     # CrewAI LLM factory for Perplexity
├── octane_branding.py    # Console branding helpers
├── agents/
│   ├── scout.py          # The Scout agent
│   ├── auditor.py        # The Auditor agent
│   └── cio.py            # The CIO agent
└── vault/
    └── database.py       # Supabase integration
```

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure the environment

Copy the example file and fill in your own keys. Never commit a real `.env`.

```bash
cp .env.example .env
```

Then edit `.env` and set at least `PERPLEXITY_API_KEY`. Configuration is
fail-closed: there are no embedded fallback API keys, so a missing key
produces a clear error instead of silently using a hardcoded credential.

### 3. (Optional) Supabase

If you want findings persisted, create a `ticker_reports` table:

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

Run a research cycle:

```bash
python -m octane_capital.cli research
```

Set `GHOST_MODE=true` in `.env` for silent operation suitable for scheduled jobs.

## Safety notes

- No live trading is implemented; `TRADING_MODE` defaults to `research` and
  `ENABLE_LIVE_TRADING` defaults to `false`.
- No secrets are hardcoded anywhere in the codebase.
- If you previously exposed an API key in this repository's history, rotate it.

---

**Octane Capital Lab** — research first, trade never by accident.
