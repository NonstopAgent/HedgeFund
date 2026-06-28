"""
Octane Capital Lab - Pydantic Data Models (drop-in replacement)
Adds RiskLevel enum, swing fields on TradeProposal, strategy tag on grades,
and ticker/action/notional on TradeResult so the orders audit trail is complete.
"""

from enum import Enum
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import uuid


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


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


class RiskLevel(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"

    @classmethod
    def coerce(cls, v) -> "RiskLevel":
        s = str(v or "").strip().lower()
        if "high" in s or "elevated" in s:
            return cls.HIGH
        if "low" in s:
            return cls.LOW
        return cls.MEDIUM


class ExitRules(BaseModel):
    stop_loss_pct: float = Field(..., ge=0.0, le=0.5)
    take_profit_pct: Optional[float] = Field(None, ge=0.0, le=2.0)
    max_hold_days: int = Field(..., ge=1, le=365)
    invalidation_events: List[str] = Field(default_factory=list)


class TradeProposal(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=_utcnow)
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

    # --- swing/risk additions ---
    strategy: Optional[str] = None
    entry_price: Optional[float] = None
    atr: Optional[float] = None
    stop_price: Optional[float] = None

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
    checked_at: datetime = Field(default_factory=_utcnow)


class OrderRequest(BaseModel):
    proposal_id: str
    ticker: str
    action: TradeAction
    quantity: Optional[float] = None
    notional: Optional[float] = None
    order_type: str = "market"
    time_in_force: str = "day"
    dry_run: bool = True
    stop_price: Optional[float] = None


class TradeResult(BaseModel):
    proposal_id: str
    broker: str
    mode: TradingMode
    submitted: bool
    ticker: Optional[str] = None
    action: Optional[TradeAction] = None
    notional: Optional[float] = None
    broker_order_id: Optional[str] = None
    filled_quantity: Optional[float] = None
    average_fill_price: Optional[float] = None
    error: Optional[str] = None
    executed_at: datetime = Field(default_factory=_utcnow)


class TradeGrade(BaseModel):
    proposal_id: str
    ticker: str
    strategy: Optional[str] = None
    entry_price: float
    current_or_exit_price: float
    pnl_pct: float
    thesis_correct: Optional[bool] = None
    timing_score: float = Field(..., ge=0.0, le=10.0)
    risk_management_score: float = Field(..., ge=0.0, le=10.0)
    lesson: str
    should_repeat_strategy: bool
    graded_at: datetime = Field(default_factory=_utcnow)


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
    ticker: str = Field(..., description="Stock ticker symbol")
    company_name: str = Field(..., description="Full company name")
    sentiment_score: float = Field(..., ge=0.0, le=10.0)
    signals: List[str] = Field(default_factory=list)
    signal_sources: List[str] = Field(default_factory=list)
    summary: str = Field(...)


class MoatAnalysis(BaseModel):
    score: float = Field(..., ge=0.0, le=10.0)
    findings: List[str] = Field(default_factory=list)
    patents_mentioned: List[str] = Field(default_factory=list)


class SECAnalysis(BaseModel):
    score: float = Field(..., ge=0.0, le=10.0)
    revenue_trend: str = Field(...)
    key_metrics: Dict[str, Any] = Field(default_factory=dict)
    risk_factors: List[str] = Field(default_factory=list)


class InsiderTrading(BaseModel):
    score: float = Field(..., ge=0.0, le=10.0)
    recent_activity: str = Field(...)
    notable_transactions: List[str] = Field(default_factory=list)


class FinancialHealth(BaseModel):
    score: float = Field(..., ge=0.0, le=10.0)
    debt_equity_ratio: Optional[float] = None
    profit_margin: Optional[float] = None
    summary: str = Field(...)


class FinalAssessment(BaseModel):
    conviction_score: float = Field(..., ge=0.0, le=10.0)
    risk_level: str = Field(...)
    investment_thesis: str = Field(...)
    recommended_position: str = Field(...)


class AuditReport(BaseModel):
    ticker: str = Field(...)
    audit_date: datetime = Field(default_factory=_utcnow)
    moat_analysis: MoatAnalysis
    risk_factors: List[str] = Field(default_factory=list)
    sec_analysis: SECAnalysis
    insider_trading: InsiderTrading
    financial_health: FinancialHealth
    final_assessment: FinalAssessment


ResearchCycleResult.model_rebuild()
