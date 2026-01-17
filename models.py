"""
Octane Global Trust - Pydantic Data Models
Structured data models for Scout and Auditor outputs
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class ScoutSignal(BaseModel):
    """Scout's alpha signal detection output"""
    ticker: str = Field(..., description="Stock ticker symbol")
    company_name: str = Field(..., description="Full company name")
    sentiment_score: float = Field(..., ge=0.0, le=10.0, description="Sentiment/confidence score (0-10)")
    signals: List[str] = Field(default_factory=list, description="List of alpha signals detected")
    signal_sources: List[str] = Field(default_factory=list, description="Sources of signals (GitHub, Reddit, Tech News)")
    summary: str = Field(..., description="Brief summary of why this ticker has alpha potential")
    
    class Config:
        json_schema_extra = {
            "example": {
                "ticker": "NVDA",
                "company_name": "NVIDIA Corporation",
                "sentiment_score": 8.5,
                "signals": [
                    "Massive spike in CUDA repository stars",
                    "New patent filing for AI acceleration technology"
                ],
                "signal_sources": ["GitHub", "Tech News"],
                "summary": "Strong developer community growth and IP expansion indicate sustained competitive advantage."
            }
        }


class MoatAnalysis(BaseModel):
    """Technical moat analysis component"""
    score: float = Field(..., ge=0.0, le=10.0, description="Moat strength score")
    findings: List[str] = Field(default_factory=list, description="Key findings about technical moats")
    patents_mentioned: List[str] = Field(default_factory=list, description="Relevant patents identified")


class SECAnalysis(BaseModel):
    """SEC filings analysis component"""
    score: float = Field(..., ge=0.0, le=10.0, description="SEC analysis score")
    revenue_trend: str = Field(..., description="Revenue trend: Growing/Stable/Declining")
    key_metrics: Dict[str, Any] = Field(default_factory=dict, description="Key financial metrics")
    risk_factors: List[str] = Field(default_factory=list, description="Identified risk factors")


class InsiderTrading(BaseModel):
    """Insider trading pattern analysis"""
    score: float = Field(..., ge=0.0, le=10.0, description="Insider sentiment score")
    recent_activity: str = Field(..., description="Net Buying/Selling/Neutral")
    notable_transactions: List[str] = Field(default_factory=list, description="Notable insider transactions")


class FinancialHealth(BaseModel):
    """Financial health metrics"""
    score: float = Field(..., ge=0.0, le=10.0, description="Financial health score")
    debt_equity_ratio: Optional[float] = Field(None, description="Debt-to-equity ratio")
    profit_margin: Optional[float] = Field(None, description="Profit margin percentage")
    summary: str = Field(..., description="Financial health summary")


class FinalAssessment(BaseModel):
    """Final investment assessment"""
    conviction_score: float = Field(..., ge=0.0, le=10.0, description="Final conviction score (0-10)")
    risk_level: str = Field(..., description="Risk level: Low/Medium/High")
    investment_thesis: str = Field(..., description="Detailed investment thesis")
    recommended_position: str = Field(..., description="Recommended position: Large/Medium/Small/None")


class AuditReport(BaseModel):
    """Auditor's comprehensive audit report"""
    ticker: str = Field(..., description="Stock ticker symbol")
    audit_date: datetime = Field(default_factory=datetime.now, description="Date of audit")
    moat_analysis: MoatAnalysis = Field(..., description="Technical moat analysis")
    risk_factors: List[str] = Field(default_factory=list, description="Aggregated risk factors")
    sec_analysis: SECAnalysis = Field(..., description="SEC filings analysis")
    insider_trading: InsiderTrading = Field(..., description="Insider trading analysis")
    financial_health: FinancialHealth = Field(..., description="Financial health analysis")
    final_assessment: FinalAssessment = Field(..., description="Final investment assessment")
    
    class Config:
        json_schema_extra = {
            "example": {
                "ticker": "NVDA",
                "audit_date": "2024-01-15T10:00:00",
                "moat_analysis": {
                    "score": 9.0,
                    "findings": ["Dominant GPU market position", "Proprietary CUDA ecosystem"],
                    "patents_mentioned": ["US12345678", "US87654321"]
                },
                "risk_factors": ["Cyclical demand", "Regulatory scrutiny"],
                "sec_analysis": {
                    "score": 8.5,
                    "revenue_trend": "Growing",
                    "key_metrics": {"revenue_growth": "125% YoY"},
                    "risk_factors": ["Market concentration"]
                },
                "insider_trading": {
                    "score": 7.5,
                    "recent_activity": "Net Buying",
                    "notable_transactions": ["CEO purchased 50,000 shares"]
                },
                "financial_health": {
                    "score": 9.0,
                    "debt_equity_ratio": 0.15,
                    "profit_margin": 45.2,
                    "summary": "Exceptional financial position with strong cash flow"
                },
                "final_assessment": {
                    "conviction_score": 8.8,
                    "risk_level": "Medium",
                    "investment_thesis": "Strong buy with exceptional moat and growth trajectory",
                    "recommended_position": "Large"
                }
            }
        }
