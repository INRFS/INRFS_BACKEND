import hashlib
import random
from datetime import datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.services.email_service import send_otp_email


OTP_EXPIRY_MINUTES = 5


def hash_otp(otp: str) -> str:
    return hashlib.sha256(
        otp.encode("utf-8")
    ).hexdigest()


def send_email_otp(
    db: Session,
    email: str,
    name: str = "User",
):
    email = email.strip().lower()

    if not email:
        raise HTTPException(
            status_code=400,
            detail="Email is required.",
        )

    existing_user = db.execute(
        text(
            """
            SELECT id
            FROM public.tn_application_user
            WHERE LOWER(email) = :email
            LIMIT 1
            """
        ),
        {"email": email},
    ).fetchone()

    if existing_user:
        raise HTTPException(
            status_code=409,
            detail="Email already exists.",
        )

    otp = str(
        random.SystemRandom().randint(
            100000,
            999999,
        )
    )

    otp_hash = hash_otp(otp)

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
              AND is_verified = FALSE
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
            "otp_hash": otp_hash,
            "expiry_date": expiry_date,
        },
    )

    if not send_otp_email(
        email=email,
        name=name,
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
        "message": "OTP sent successfully to your email.",
    }


def verify_email_otp(
    db: Session,
    email: str,
    otp: str,
):
    email = email.strip().lower()
    otp = otp.strip()

    if not email:
        raise HTTPException(
            status_code=400,
            detail="Email is required.",
        )

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

    if hash_otp(otp) != record.otp_hash:
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
        "message": "Email verified successfully.",
    }


def is_email_verified(
    db: Session,
    email: str,
) -> bool:
    email = email.strip().lower()

    record = db.execute(
        text(
            """
            SELECT id
            FROM public.tn_email_otp
            WHERE LOWER(email) = :email
              AND is_verified = TRUE
              AND is_active = TRUE
            ORDER BY id DESC
            LIMIT 1
            """
        ),
        {"email": email},
    ).fetchone()

    return record is not None


def clear_email_otp(
    db: Session,
    email: str,
):
    email = email.strip().lower()

    db.execute(
        text(
            """
            UPDATE public.tn_email_otp
            SET is_active = FALSE
            WHERE LOWER(email) = :email
            """
        ),
        {"email": email},
    )