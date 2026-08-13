from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user

from app.schemas.admin.admin_profile_schema import (
    AdminProfileResponse,
    AdminProfileUpdate,
)

from app.services.admin.admin_profile_service import (
    get_admin_profile,
    update_admin_profile,
)


router = APIRouter(
    prefix="/admin",
    tags=["Admin Profile"],
)


def get_logged_in_user_id(
    current_user=Depends(
        get_current_user
    ),
):
    if current_user is None:
        raise HTTPException(
            status_code=401,
            detail="Authentication required.",
        )

    if isinstance(
        current_user,
        dict,
    ):
        user_id = current_user.get("sub")

        if user_id is None:
            user_id = current_user.get("id")

    else:
        user_id = getattr(
            current_user,
            "id",
            None,
        )

        if user_id is None:
            user_id = getattr(
                current_user,
                "sub",
                None,
            )

    try:
        return int(user_id)
    except (
        TypeError,
        ValueError,
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid user information.",
        )


@router.get(
    "/profile",
    response_model=AdminProfileResponse,
)
def get_profile(
    user_id: int = Depends(
        get_logged_in_user_id
    ),
    db: Session = Depends(get_db),
):
    result = get_admin_profile(
        db=db,
        user_id=user_id,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=404,
            detail="Profile not found.",
        )

    return result


@router.put(
    "/profile",
    response_model=AdminProfileResponse,
)
def update_profile(
    data: AdminProfileUpdate,
    user_id: int = Depends(
        get_logged_in_user_id
    ),
    db: Session = Depends(get_db),
):
    result = update_admin_profile(
        db=db,
        user_id=user_id,
        name=data.name,
        email=data.email,
        mobile=data.mobile,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=400,
            detail=result.get(
                "message",
                "Unable to update profile.",
            ),
        )

    return result