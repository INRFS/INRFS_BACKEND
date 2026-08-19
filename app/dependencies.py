from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db

from app.models.generated_models import (
    TnApplicationUser,
)

from app.utils.auth_utils import decode_access_token


security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(
        security
    ),
    db: Session = Depends(get_db),
):

    token = credentials.credentials

    payload = decode_access_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={
                "WWW-Authenticate": "Bearer"
            },
        )

    user_id = payload.get("sub")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    try:
        user_id = int(user_id)

    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID in token",
        )

    user = (
        db.query(TnApplicationUser)
        .filter(
            TnApplicationUser.id == user_id
        )
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    return user


def require_role(*allowed_roles):

    def role_checker(
        current_user=Depends(
            get_current_user
        ),
    ):

        role_name = (
            current_user.role.role_name
            if current_user.role
            else ""
        )

        role_name_upper = role_name.upper()

        allowed_upper = [
            role.upper()
            for role in allowed_roles
        ]

        if role_name_upper not in allowed_upper:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this resource",
            )

        return current_user

    return role_checker


def require_superadmin(
    current_user=Depends(
        get_current_user
    ),
):

    role_name = (
        current_user.role.role_name
        if current_user.role
        else ""
    )

    if role_name.upper() != "SUPERADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superadmin access required",
        )

    return current_user


def require_admin_or_superadmin(
    current_user=Depends(
        get_current_user
    ),
):

    role_name = (
        current_user.role.role_name
        if current_user.role
        else ""
    ).upper()

    if role_name not in [
        "ADMIN",
        "SUPERADMIN",
    ]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or Superadmin access required",
        )

    return current_user


def require_investor(
    current_user=Depends(
        get_current_user
    ),
):

    role_name = (
        current_user.role.role_name
        if current_user.role
        else ""
    )

    if role_name.upper() != "INVESTOR":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Investor access required",
        )

    return current_user