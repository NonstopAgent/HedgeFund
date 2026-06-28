-- Octane Capital Lab - Supabase migrations

ALTER TABLE ticker_reports
ADD COLUMN IF NOT EXISTS source_run_id UUID,
ADD COLUMN IF NOT EXISTS model_provider TEXT,
ADD COLUMN IF NOT EXISTS model_name TEXT,
ADD COLUMN IF NOT EXISTS raw_output JSONB,
ADD COLUMN IF NOT EXISTS data_quality_score NUMERIC;

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
