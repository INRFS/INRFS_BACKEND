from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class InvestmentManagementResponse(BaseModel):
    success: bool
    data: List[Dict[str, Any]]
    total: int


class InvestmentDetailsResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None


class InvestmentBondDetailsResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None


class InvestmentApproveRequest(BaseModel):
    interest_rate: Decimal = Field(..., ge=0)
    remarks: Optional[str] = None


class InvestmentRejectRequest(BaseModel):
    rejection_reason: str = Field(..., min_length=1)
    remarks: Optional[str] = None


class InvestmentActionResponse(BaseModel):
    success: bool
    message: str
    data: Any = None


class TenureExtensionResponse(BaseModel):
    success: bool
    data: List[Dict[str, Any]]
    total: int


class TenureExtensionDetailsResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None


class TenureExtensionActionRequest(BaseModel):
    remarks: Optional[str] = None


class MonthlyInterestResponse(BaseModel):
    success: bool
    data: List[Dict[str, Any]]
    total: int


class MonthlyInterestDetailsResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None


class MonthlyInterestRejectRequest(BaseModel):
    rejection_reason: str = Field(..., min_length=1)
    remarks: Optional[str] = None


class MonthlyInterestActionResponse(BaseModel):
    success: bool
    message: str
    data: Any = None


class ApproveAllMonthlyInterestRequest(BaseModel):
    interest_due_date: date


class SettlementResponse(BaseModel):
    success: bool
    message: str
    data: Any = None


class InvestmentManagementQuery(BaseModel):
    bond_id: Optional[str] = None
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class MonthlyInterestQuery(BaseModel):
    interest_due_date: Optional[date] = None
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class DashboardResponse(BaseModel):
    success: bool
    data: List[Dict[str, Any]]


class DashboardSummaryResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None