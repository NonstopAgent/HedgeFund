"""
Octane Capital Lab - Pydantic Data Models
Research, trade proposal, risk, order, and result models.
"""

from enum import Enum
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid


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


class ExitRules(BaseModel):
    stop_loss_pct: float = Field(..., ge=0.0, le=0.5)
    take_profit_pct: Optional[float] = Field(None, ge=0.0, le=2.0)
    max_hold_days: int = Field(..., ge=1, le=365)
    invalidation_events: List[str] = Field(default_factory=list)


class TradeProposal(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)
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

    @field_validator("thesis")
    @classmethod
    def thesis_not_empty(cls, v: str) -> str:
        if not v or len(v.strip()) < 20:
            raise ValueError("thesis must be at least 20 characters")
        return v.strip()

    @field_validator("evidence")
    @classmethod
    def evidence_not_empty(cls, v: List[str]) -> List[str]:
        if not v:
            raise ValueError("evidence must contain at least one item")
        return v


class RiskDecision(BaseModel):
    approved: bool
    decision: str
    reasons: List[str]
    adjusted_position_pct: Optional[float] = None
    adjusted_notional: Optional[float] = None
    max_allowed_loss: Optional[float] = None
    checked_at: datetime = Field(default_factory=datetime.utcnow)


class OrderRequest(BaseModel):
    proposal_id: str
    ticker: str
    action: TradeAction
    quantity: Optional[float] = None
    notional: Optional[float] = None
    order_type: str = "market"
    time_in_force: str = "day"
    dry_run: bool = True


class TradeResult(BaseModel):
    proposal_id: str
    broker: str
    mode: TradingMode
    submitted: bool
    broker_order_id: Optional[str] = None
    filled_quantity: Optional[float] = None
    average_fill_price: Optional[float] = None
    error: Optional[str] = None
    executed_at: datetime = Field(default_factory=datetime.utcnow)


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
    graded_at: datetime = Field(default_factory=datetime.utcnow)


class CriticReview(BaseModel):
    passed: bool
    concerns: List[str] = Field(default_factory=list)
    recommended_changes: List[str] = Field(default_factory=list)
    confidence_adjustment: float = 0.0


class AccountSnapshot(BaseModel):
    cash: float
    equity: float
    buying_power: float


class PositionSnapshot(BaseModel):
    ticker: str
    quantity: float
    average_cost: float
    market_value: float


class OrderPreview(BaseModel):
    ticker: str
    action: TradeAction
    estimated_quantity: float
    estimated_notional: float
    estimated_price: float
    warnings: List[str] = Field(default_factory=list)


class PortfolioContext(BaseModel):
    account_equity: float
    daily_loss_pct: float = 0.0
    weekly_loss_pct: float = 0.0
    open_positions: int = 0


class ResearchCycleResult(BaseModel):
    scout_signals: List["ScoutSignal"] = Field(default_factory=list)
    audit_reports: Dict[str, "AuditReport"] = Field(default_factory=dict)
    proposals: List[TradeProposal] = Field(default_factory=list)
    critic_reviews: Dict[str, CriticReview] = Field(default_factory=dict)
    risk_decisions: Dict[str, RiskDecision] = Field(default_factory=dict)
    approved_for_paper: List[TradeProposal] = Field(default_factory=list)
    proposals_needing_approval: List[TradeProposal] = Field(default_factory=list)


class BacktestResult(BaseModel):
    total_return_pct: float
    max_drawdown_pct: float
    win_rate: float
    average_win_pct: float
    average_loss_pct: float
    profit_factor: float
    sharpe_ratio: float
    num_trades: int
    average_hold_days: float


class ScoutSignal(BaseModel):
    """Scout's alpha signal detection output."""

    ticker: str = Field(..., description="Stock ticker symbol")
    company_name: str = Field(..., description="Full company name")
    sentiment_score: float = Field(..., ge=0.0, le=10.0, description="Sentiment/confidence score (0-10)")
    signals: List[str] = Field(default_factory=list, description="List of alpha signals detected")
    signal_sources: List[str] = Field(
        default_factory=list,
        description="Sources of signals (GitHub, Reddit, Tech News)",
    )
    summary: str = Field(..., description="Brief summary of why this ticker has alpha potential")


class MoatAnalysis(BaseModel):
    """Technical moat analysis component."""

    score: float = Field(..., ge=0.0, le=10.0, description="Moat strength score")
    findings: List[str] = Field(default_factory=list, description="Key findings about technical moats")
    patents_mentioned: List[str] = Field(default_factory=list, description="Relevant patents identified")


class SECAnalysis(BaseModel):
    """SEC filings analysis component."""

    score: float = Field(..., ge=0.0, le=10.0, description="SEC analysis score")
    revenue_trend: str = Field(..., description="Revenue trend: Growing/Stable/Declining")
    key_metrics: Dict[str, Any] = Field(default_factory=dict, description="Key financial metrics")
    risk_factors: List[str] = Field(default_factory=list, description="Identified risk factors")


class InsiderTrading(BaseModel):
    """Insider trading pattern analysis."""

    score: float = Field(..., ge=0.0, le=10.0, description="Insider sentiment score")
    recent_activity: str = Field(..., description="Net Buying/Selling/Neutral")
    notable_transactions: List[str] = Field(default_factory=list, description="Notable insider transactions")


class FinancialHealth(BaseModel):
    """Financial health metrics."""

    score: float = Field(..., ge=0.0, le=10.0, description="Financial health score")
    debt_equity_ratio: Optional[float] = Field(None, description="Debt-to-equity ratio")
    profit_margin: Optional[float] = Field(None, description="Profit margin percentage")
    summary: str = Field(..., description="Financial health summary")


class FinalAssessment(BaseModel):
    """Final investment assessment."""

    conviction_score: float = Field(..., ge=0.0, le=10.0, description="Final conviction score (0-10)")
    risk_level: str = Field(..., description="Risk level: Low/Medium/High")
    investment_thesis: str = Field(..., description="Detailed investment thesis")
    recommended_position: str = Field(..., description="Recommended position: Large/Medium/Small/None")


class AuditReport(BaseModel):
    """Auditor's comprehensive audit report."""

    ticker: str = Field(..., description="Stock ticker symbol")
    audit_date: datetime = Field(default_factory=datetime.now, description="Date of audit")
    moat_analysis: MoatAnalysis = Field(..., description="Technical moat analysis")
    risk_factors: List[str] = Field(default_factory=list, description="Aggregated risk factors")
    sec_analysis: SECAnalysis = Field(..., description="SEC filings analysis")
    insider_trading: InsiderTrading = Field(..., description="Insider trading analysis")
    financial_health: FinancialHealth = Field(..., description="Financial health analysis")
    final_assessment: FinalAssessment = Field(..., description="Final investment assessment")


ResearchCycleResult.model_rebuild()
