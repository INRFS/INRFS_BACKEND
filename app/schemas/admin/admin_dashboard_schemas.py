from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class DashboardSummaryResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None


class DashboardInvestorGrowthResponse(BaseModel):
    success: bool
    data: List[Dict[str, Any]]


class DashboardMonthlyInvestmentTrendResponse(BaseModel):
    success: bool
    data: List[Dict[str, Any]]