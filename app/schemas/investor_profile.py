from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class InvestorBankDetailsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = None
    account_holder_name: Optional[str] = None
    bank_name: Optional[str] = None
    account_type_id: Optional[int] = None
    account_type: Optional[str] = None
    account_number: Optional[str] = None
    ifsc_code: Optional[str] = None
    is_primary: Optional[bool] = None


class InvestorBankDetailsUpdate(BaseModel):
    account_holder_name: Optional[str] = Field(
        default=None,
        max_length=150,
    )

    bank_name: Optional[str] = Field(
        default=None,
        max_length=100,
    )

    account_type_id: Optional[int] = None

    account_number: Optional[str] = Field(
        default=None,
        max_length=30,
    )

    ifsc_code: Optional[str] = Field(
        default=None,
        max_length=20,
    )


class InvestorProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    investor_id: Optional[str] = None
    full_name: str
    mobile: str
    email: Optional[EmailStr] = None

    date_of_birth: Optional[date] = None
    aadhaar_number: Optional[str] = None

    address: Optional[str] = None
    city: Optional[str] = None

    state_id: Optional[int] = None
    state_name: Optional[str] = None

    pincode: Optional[str] = None

    branch_id: Optional[int] = None
    branch_name: Optional[str] = None

    status: Optional[str] = None

    bank: Optional[InvestorBankDetailsResponse] = None


class InvestorProfileUpdate(BaseModel):
    full_name: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=255,
    )

    mobile: Optional[str] = Field(
        default=None,
        min_length=10,
        max_length=20,
    )

    email: Optional[EmailStr] = None

    date_of_birth: Optional[date] = None

    address: Optional[str] = Field(
        default=None,
        max_length=500,
    )

    city: Optional[str] = Field(
        default=None,
        max_length=100,
    )

    state_id: Optional[int] = None

    pincode: Optional[str] = Field(
        default=None,
        max_length=10,
    )

    branch_id: Optional[int] = None

    bank: Optional[InvestorBankDetailsUpdate] = None