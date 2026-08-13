from datetime import date
from typing import Optional

from pydantic import BaseModel, EmailStr


class InvestorProfileResponse(BaseModel):
    investor_id: str
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


class InvestorProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    mobile: Optional[str] = None
    email: Optional[EmailStr] = None
    date_of_birth: Optional[date] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state_id: Optional[int] = None
    pincode: Optional[str] = None
    branch_id: Optional[int] = None