from typing import Any, Dict, List

from pydantic import BaseModel


class InvestorDashboardResponse(BaseModel):
    summary: Any
    growth: List[Dict[str, Any]]
    portfolio_split: List[Dict[str, Any]]
    recent_investments: List[Dict[str, Any]]
    investor: Any