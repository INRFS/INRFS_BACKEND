from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.auth_schema import (
    ForgotPasswordSendOtpRequest,
    ForgotPasswordVerifyOtpRequest,
    ForgotPasswordResetRequest,
)
from app.services.password_reset_service import (
    send_forgot_password_otp,
    verify_forgot_password_otp,
    reset_password,
)


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/forgot-password/send-otp",
)
def send_forgot_password_otp_api(
    data: ForgotPasswordSendOtpRequest,
    db: Session = Depends(get_db),
):
    return send_forgot_password_otp(
        db=db,
        email=str(data.email),
    )


@router.post(
    "/forgot-password/verify-otp",
)
def verify_forgot_password_otp_api(
    data: ForgotPasswordVerifyOtpRequest,
    db: Session = Depends(get_db),
):
    return verify_forgot_password_otp(
        db=db,
        email=str(data.email),
        otp=data.otp,
    )


@router.post(
    "/forgot-password/reset",
)
def reset_password_api(
    data: ForgotPasswordResetRequest,
    db: Session = Depends(get_db),
):
    return reset_password(
        db=db,
        email=str(data.email),
        otp=data.otp,
        new_password=data.new_password,
    )