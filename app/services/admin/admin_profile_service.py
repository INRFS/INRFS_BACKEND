from sqlalchemy.orm import Session
from typing import Optional

from app.models.generated_models import (
    TnApplicationUser,
)


def get_admin_profile(
    db: Session,
    user_id: int,
):
    user = (
        db.query(TnApplicationUser)
        .filter(
            TnApplicationUser.id == user_id
        )
        .first()
    )

    if not user:
        return {
            "success": False,
            "data": None,
        }

    role_name = None

    if user.role:
        role_name = user.role.role_name

    branch_name = None

    if user.branch:
        branch_name = user.branch.branch_name

    status_name = None

    if user.user_status:
        status_name = user.user_status.status_name

    return {
        "success": True,
        "data": {
            "id": user.id,
            "name": user.full_name,
            "email": user.email,
            "mobile": user.mobile,
            "role": role_name,
            "branch": branch_name,
            "branch_id": user.branch_id,
            "status": status_name,
            "is_active": user.is_active,
            "username": user.username,
        },
    }


def update_admin_profile(
    db: Session,
    user_id: int,
    name: str,
    email: Optional[str],
    mobile: Optional[str],
):
    user = (
        db.query(TnApplicationUser)
        .filter(
            TnApplicationUser.id == user_id
        )
        .first()
    )

    if not user:
        return {
            "success": False,
            "message": "Profile not found.",
            "data": None,
        }

    if email:
        existing_email = (
            db.query(TnApplicationUser)
            .filter(
                TnApplicationUser.email == email,
                TnApplicationUser.id != user_id,
            )
            .first()
        )

        if existing_email:
            return {
                "success": False,
                "message": "Email already exists.",
                "data": None,
            }

    if mobile:
        existing_mobile = (
            db.query(TnApplicationUser)
            .filter(
                TnApplicationUser.mobile == mobile,
                TnApplicationUser.id != user_id,
            )
            .first()
        )

        if existing_mobile:
            return {
                "success": False,
                "message": "Mobile number already exists.",
                "data": None,
            }

    user.full_name = name.strip()

    if email is not None:
        user.email = email.strip()

    if mobile is not None:
        user.mobile = mobile.strip()

    db.commit()
    db.refresh(user)

    role_name = None

    if user.role:
        role_name = user.role.role_name

    branch_name = None

    if user.branch:
        branch_name = user.branch.branch_name

    status_name = None

    if user.user_status:
        status_name = user.user_status.status_name

    return {
        "success": True,
        "message": "Profile updated successfully.",
        "data": {
            "id": user.id,
            "name": user.full_name,
            "email": user.email,
            "mobile": user.mobile,
            "role": role_name,
            "branch": branch_name,
            "branch_id": user.branch_id,
            "status": status_name,
            "is_active": user.is_active,
            "username": user.username,
        },
    }