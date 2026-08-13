from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class InvestorManagementQuery(BaseModel):
    status_name: Optional[str] = None
    kyc_status_name: Optional[str] = None
    search_text: Optional[str] = None

    limit: int = Field(
        default=20,
        ge=1,
        le=100,
    )

    offset: int = Field(
        default=0,
        ge=0,
    )


class InvestorManagementResponse(BaseModel):
    success: bool
    data: List[Dict[str, Any]]
    total: int


class InvestorDetailsResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None


class ApproveInvestorKYCRequest(BaseModel):
    branch_id: Optional[int] = None
    remarks: Optional[str] = None


class ApproveInvestorKYCResponse(BaseModel):
    success: bool
    message: str
    data: Any = None


class RejectInvestorRequest(BaseModel):
    remarks: Optional[str] = None


class RejectInvestorResponse(BaseModel):
    success: bool
    message: str
    data: Any = None