from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class ReportSummaryResponse(BaseModel):
    success: bool
    data: Dict[str, Any]


class ReportChartResponse(BaseModel):
    success: bool
    data: List[Dict[str, Any]]


class ReportInvestmentResponse(BaseModel):
    success: bool
    data: List[Dict[str, Any]]
    total: int


class ReportDashboardResponse(BaseModel):
    success: bool
    summary: Dict[str, Any]
    monthly_investments: List[Dict[str, Any]]
    investor_growth: List[Dict[str, Any]]
    status_distribution: List[Dict[str, Any]]
    recent_investments: List[Dict[str, Any]]