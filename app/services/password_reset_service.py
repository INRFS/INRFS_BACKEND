import hashlib
import random
from datetime import datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.services.email_service import send_otp_email


OTP_EXPIRY_MINUTES = 5


def _hash_otp(otp: str) -> str:
    return hashlib.sha256(
        otp.encode("utf-8")
    ).hexdigest()


def send_forgot_password_otp(
    db: Session,
    email: str,
):
    email = email.strip().lower()

    if not email:
        raise HTTPException(
            status_code=400,
            detail="Email is required.",
        )

    user = db.execute(
        text(
            """
            SELECT id, full_name
            FROM public.tn_application_user
            WHERE LOWER(email) = :email
              AND is_active = TRUE
            LIMIT 1
            """
        ),
        {"email": email},
    ).fetchone()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="No active account found with this email address.",
        )

    otp = str(
        random.SystemRandom().randint(
            100000,
            999999,
        )
    )

    expiry_date = datetime.utcnow() + timedelta(
        minutes=OTP_EXPIRY_MINUTES
    )

    db.execute(
        text(
            """
            UPDATE public.tn_email_otp
            SET is_active = FALSE
            WHERE LOWER(email) = :email
              AND is_active = TRUE
            """
        ),
        {"email": email},
    )

    db.execute(
        text(
            """
            INSERT INTO public.tn_email_otp
            (
                email,
                otp_hash,
                expiry_date,
                is_verified,
                is_active,
                created_date
            )
            VALUES
            (
                :email,
                :otp_hash,
                :expiry_date,
                FALSE,
                TRUE,
                CURRENT_TIMESTAMP
            )
            """
        ),
        {
            "email": email,
            "otp_hash": _hash_otp(otp),
            "expiry_date": expiry_date,
        },
    )

    if not send_otp_email(
        email=email,
        name=user.full_name,
        otp=otp,
        expiry_minutes=OTP_EXPIRY_MINUTES,
    ):
        db.rollback()
        raise HTTPException(
            status_code=502,
            detail="Unable to send OTP email.",
        )

    db.commit()

    return {
        "success": True,
        "message": "Password reset OTP sent successfully.",
    }


def verify_forgot_password_otp(
    db: Session,
    email: str,
    otp: str,
):
    email = email.strip().lower()
    otp = otp.strip()

    if len(otp) != 6 or not otp.isdigit():
        raise HTTPException(
            status_code=400,
            detail="Invalid OTP.",
        )

    record = db.execute(
        text(
            """
            SELECT id, otp_hash, expiry_date
            FROM public.tn_email_otp
            WHERE LOWER(email) = :email
              AND is_active = TRUE
              AND is_verified = FALSE
            ORDER BY id DESC
            LIMIT 1
            """
        ),
        {"email": email},
    ).fetchone()

    if not record:
        raise HTTPException(
            status_code=400,
            detail="OTP not found. Please request a new OTP.",
        )

    if record.expiry_date < datetime.utcnow():
        db.execute(
            text(
                """
                UPDATE public.tn_email_otp
                SET is_active = FALSE
                WHERE id = :id
                """
            ),
            {"id": record.id},
        )
        db.commit()

        raise HTTPException(
            status_code=400,
            detail="OTP has expired. Please request a new OTP.",
        )

    if _hash_otp(otp) != record.otp_hash:
        raise HTTPException(
            status_code=400,
            detail="Invalid OTP.",
        )

    db.execute(
        text(
            """
            UPDATE public.tn_email_otp
            SET
                is_verified = TRUE,
                verified_date = CURRENT_TIMESTAMP
            WHERE id = :id
            """
        ),
        {"id": record.id},
    )

    db.commit()

    return {
        "success": True,
        "message": "OTP verified successfully.",
    }


def reset_password(
    db: Session,
    email: str,
    otp: str,
    new_password: str,
):
    email = email.strip().lower()
    otp = otp.strip()

    if len(new_password) < 8:
        raise HTTPException(
            status_code=400,
            detail="Password must contain at least 8 characters.",
        )

    record = db.execute(
        text(
            """
            SELECT id
            FROM public.tn_email_otp
            WHERE LOWER(email) = :email
              AND otp_hash = :otp_hash
              AND is_active = TRUE
              AND is_verified = TRUE
            ORDER BY id DESC
            LIMIT 1
            """
        ),
        {
            "email": email,
            "otp_hash": _hash_otp(otp),
        },
    ).fetchone()

    if not record:
        raise HTTPException(
            status_code=400,
            detail="OTP verification is required before resetting the password.",
        )

    from app.utils.security import hash_password

    updated = db.execute(
        text(
            """
            UPDATE public.tn_application_user
            SET
                password = :password,
                failed_login_attempts = 0,
                modified_date = CURRENT_TIMESTAMP
            WHERE LOWER(email) = :email
              AND is_active = TRUE
            RETURNING id
            """
        ),
        {
            "email": email,
            "password": hash_password(new_password),
        },
    ).fetchone()

    if not updated:
        db.rollback()
        raise HTTPException(
            status_code=404,
            detail="Active account not found.",
        )

    db.execute(
        text(
            """
            UPDATE public.tn_email_otp
            SET is_active = FALSE
            WHERE id = :id
            """
        ),
        {"id": record.id},
    )

    db.commit()

    return {
        "success": True,
        "message": "Password reset successfully.",
    }