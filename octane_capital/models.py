"""
Octane Capital Lab - Pydantic Data Models
Structured data models for Scout and Auditor outputs.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


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
