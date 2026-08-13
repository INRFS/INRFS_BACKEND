from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class InvestmentCreate(BaseModel):
    investment_amount: Decimal = Field(..., gt=0)
    tenure_id: int = Field(..., gt=0)


class InvestmentCalculationResponse(BaseModel):
    investment_amount: Decimal
    tenure_id: int
    tenure_months: int
    interest_rate: Decimal
    expected_monthly_interest: Decimal
    expected_interest_amount: Decimal
    maturity_amount: Decimal
    maturity_date: date


class InvestmentResponse(BaseModel):
    id: int
    investment_id: Optional[str]
    investor_registration_id: int
    tenure_id: int
    investment_amount: Decimal
    interest_rate: Decimal
    expected_interest_amount: Decimal
    maturity_amount: Decimal
    investment_status_id: int
    investment_date: Optional[datetime]
    maturity_date: Optional[date]
    approved_by: Optional[int]
    approved_date: Optional[datetime]
    remarks: Optional[str]

    model_config = ConfigDict(
        from_attributes=True
    )


class InvestmentApprove(BaseModel):
    interest_rate: Decimal = Field(
        ...,
        gt=0,
        le=100
    )
    remarks: Optional[str] = None


class InvestmentReject(BaseModel):
    remarks: str = Field(
        ...,
        min_length=1,
        max_length=500
    )


class TenureExtensionRequest(BaseModel):
    extension_months: int = Field(
        ...,
        gt=0
    )
    remarks: Optional[str] = None


class TenureExtensionResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None


class PreCloseRequest(BaseModel):
    reason: str = Field(
        ...,
        min_length=1,
        max_length=500
    )


class PreCloseResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None