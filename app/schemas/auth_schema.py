from datetime import date
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class InvestorRegisterRequest(BaseModel):
    full_name: str = Field(
        ...,
        min_length=2,
        max_length=255,
    )

    mobile: str = Field(
        ...,
        min_length=10,
        max_length=20,
    )

    email: Optional[EmailStr] = None

    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
    )

    date_of_birth: date

    aadhaar_number: str = Field(
        ...,
        min_length=12,
        max_length=20,
    )

    address: str = Field(
        ...,
        max_length=500,
    )

    city: str = Field(
        ...,
        max_length=100,
    )

    state_id: int

    pincode: str = Field(
        ...,
        min_length=4,
        max_length=10,
    )

    branch_id: int


class InvestorLoginRequest(BaseModel):
    investor_id: str = Field(
        ...,
        min_length=3,
        max_length=20,
    )

    password: str = Field(
        ...,
        min_length=1,
        max_length=128,
    )


class StaffRegisterRequest(BaseModel):
    full_name: str = Field(
        ...,
        min_length=2,
        max_length=255,
    )

    mobile: str = Field(
        ...,
        min_length=10,
        max_length=20,
    )

    email: Optional[EmailStr] = None

    username: str = Field(
        ...,
        min_length=3,
        max_length=100,
    )

    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
    )

    branch_id: Optional[int] = None


class AdminLoginRequest(BaseModel):
    username: str = Field(
        ...,
        min_length=1,
        max_length=100,
    )

    password: str = Field(
        ...,
        min_length=1,
        max_length=128,
    )


class SuperAdminLoginRequest(BaseModel):
    username: str = Field(
        ...,
        min_length=1,
        max_length=100,
    )

    password: str = Field(
        ...,
        min_length=1,
        max_length=128,
    )


class SendEmailOtpRequest(BaseModel):
    email: EmailStr
    name: str = Field(
        default="User",
        min_length=1,
        max_length=255,
    )


class VerifyEmailOtpRequest(BaseModel):
    email: EmailStr
    otp: str = Field(
        ...,
        min_length=6,
        max_length=6,
    )


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    login_id: str
    full_name: str
    role: str
    branch_id: Optional[int] = None





class ForgotPasswordSendOtpRequest(BaseModel):
    email: EmailStr


class ForgotPasswordVerifyOtpRequest(BaseModel):
    email: EmailStr
    otp: str = Field(
        ...,
        min_length=6,
        max_length=6,
    )


class ForgotPasswordResetRequest(BaseModel):
    email: EmailStr
    otp: str = Field(
        ...,
        min_length=6,
        max_length=6,
    )
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=128,
    )




class UserResponse(BaseModel):
    id: int
    login_id: str
    full_name: str
    mobile: Optional[str] = None
    email: Optional[str] = None
    role: str
    is_active: bool
    branch_id: Optional[int] = None


class ApproveInvestorKYCRequest(BaseModel):
    remarks: Optional[str] = None


class ApproveInvestorKYCResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None


class RejectInvestorRequest(BaseModel):
    remarks: Optional[str] = None


class RejectInvestorResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None