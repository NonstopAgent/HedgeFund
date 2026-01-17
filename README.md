# Octane Global Trust - Predator Investment Engine

A high-leverage multi-agent investment research system using CrewAI and Perplexity Sonar API.

## Architecture

### The Scout (`sonar-reasoning-pro`)
Scans GitHub, Reddit, and tech news for alpha signals in AI and semiconductor stocks. Identifies high-potential tickers based on:
- GitHub star spikes
- Developer activity trends
- Reddit sentiment shifts
- Patent filings
- Job postings indicating R&D expansion

### The Auditor (`sonar-deep-research`)
Performs deep-dive audits on tickers with confidence scores > 8.0/10. Analyzes:
- Technical moats and patents
- SEC filings (10-K, 10-Q)
- Insider trading patterns
- Financial health metrics

### The Vault (Supabase)
Persistent storage for all ticker reports, sentiment scores, and audit findings.

## Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Environment Configuration
Create a `.env` file in the project root:

```env
# Perplexity API Configuration
PERPLEXITY_API_KEY=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
PERPLEXITY_BASE_URL=https://api.perplexity.ai

# Supabase Configuration (Optional)
SUPABASE_URL=your_supabase_url_here
SUPABASE_KEY=your_supabase_key_here

# Ghost Mode (Optional - runs silently)
GHOST_MODE=false
```

### 3. Supabase Database Setup

Create a table in Supabase:

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

### Run the Engine
```bash
python predator_engine.py
```

### Ghost Mode (Silent/Scheduled)
Set `GHOST_MODE=true` in `.env` for silent operation suitable for cron jobs or scheduled tasks.

## Project Structure

```
Octane_HedgeFund/
├── agents/
│   ├── __init__.py
│   ├── scout.py          # The Scout agent
│   └── auditor.py        # The Auditor agent
├── vault/
│   ├── __init__.py
│   └── database.py       # Supabase integration
├── config.py             # Configuration management
├── perplexity_client.py  # Perplexity API wrapper
├── octane_branding.py    # Visual branding utilities
├── predator_engine.py    # Main orchestration script
├── requirements.txt
└── README.md
```

## Features

- **Modular Architecture**: Clean separation of concerns
- **Octane Branding**: Obsidian/Chrome aesthetic console output
- **Ghost Mode**: Silent operation for scheduled execution
- **Confidence Thresholding**: Only audits high-confidence tickers
- **Persistent Storage**: All findings saved to Supabase

## Notes

- The system will run without Supabase credentials (vault will be in standby mode)
- Perplexity API rate limits apply
- Adjust `CONFIDENCE_THRESHOLD` in `config.py` to change audit trigger threshold

---

**Octane Global Trust** | Predator Investment Engine
