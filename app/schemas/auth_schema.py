from datetime import date
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class InvestorRegisterRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=255)
    mobile: str = Field(..., min_length=10, max_length=20)
    email: Optional[EmailStr] = None
    password: str = Field(..., min_length=8, max_length=128)
    date_of_birth: date
    aadhaar_number: str = Field(..., min_length=12, max_length=20)
    address: str = Field(..., max_length=500)
    city: str = Field(..., max_length=100)
    state_id: int
    pincode: str = Field(..., min_length=4, max_length=10)
    branch_id: int


class InvestorLoginRequest(BaseModel):
    investor_id: str = Field(..., min_length=3, max_length=20)
    password: str = Field(..., min_length=1, max_length=128)


class StaffRegisterRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=255)
    mobile: str = Field(..., min_length=10, max_length=20)
    email: Optional[EmailStr] = None
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=8, max_length=128)


class AdminLoginRequest(BaseModel):
    username: str
    password: str


class SuperAdminLoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    login_id: str
    full_name: str
    role: str


class UserResponse(BaseModel):
    id: int
    login_id: str
    full_name: str
    mobile: str
    email: Optional[str]
    role: str
    is_active: bool