from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.database import get_db
from app.utils.auth_utils import decode_access_token

from app.services.superadmin.profile_service import (
    get_superadmin_profile,
    update_superadmin_profile,
)


router = APIRouter(
    prefix="/superadmin/profile",
    tags=["Super Admin Profile"],
)

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(
        security
    ),
):
    token = credentials.credentials

    payload = decode_access_token(token)

    if not payload:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token.",
        )

    return payload


def get_user_id(
    current_user: dict,
) -> int:
    user_id = (
        current_user.get("user_id")
        or current_user.get("id")
        or current_user.get("sub")
    )

    if user_id is None:
        raise HTTPException(
            status_code=401,
            detail="User ID not found in token.",
        )

    try:
        return int(user_id)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=401,
            detail="Invalid user ID in token.",
        )


def get_role_name(
    current_user: dict,
) -> str:

    role = current_user.get("role")

    if isinstance(role, dict):
        role = (
            role.get("role_name")
            or role.get("name")
            or role.get("role")
        )

    if role is None:
        role = current_user.get(
            "role_name",
            "",
        )

    return str(role).strip().upper()


def require_superadmin(
    current_user: dict = Depends(
        get_current_user
    ),
):
    role_name = get_role_name(
        current_user
    )

    if role_name != "SUPERADMIN":
        raise HTTPException(
            status_code=403,
            detail="Super Admin access required.",
        )

    return current_user


class ProfileUpdate(BaseModel):
    full_name: str
    email: EmailStr
    mobile: str


@router.get("")
def get_profile(
    db: Session = Depends(get_db),
    current_user: dict = Depends(
        require_superadmin
    ),
):
    user_id = get_user_id(
        current_user
    )

    profile = get_superadmin_profile(
        db=db,
        user_id=user_id,
    )

    if not profile:
        raise HTTPException(
            status_code=404,
            detail="Profile not found.",
        )

    return {
        "success": True,
        "data": profile,
    }


@router.put("")
def update_profile(
    payload: ProfileUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(
        require_superadmin
    ),
):
    user_id = get_user_id(
        current_user
    )

    full_name = payload.full_name.strip()
    email = str(payload.email).strip()
    mobile = payload.mobile.strip()

    if not full_name:
        raise HTTPException(
            status_code=400,
            detail="Full name is required.",
        )

    if not mobile:
        raise HTTPException(
            status_code=400,
            detail="Mobile number is required.",
        )

    try:
        profile = update_superadmin_profile(
            db=db,
            user_id=user_id,
            full_name=full_name,
            email=email,
            mobile=mobile,
        )

        return {
            "success": True,
            "message": "Profile updated successfully.",
            "data": profile,
        }

    except Exception as exc:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )