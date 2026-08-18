from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user

from app.schemas.investor_profile import (
    InvestorProfileResponse,
    InvestorProfileUpdate,
)

from app.services.investor_profile_service import (
    get_investor_profile,
    update_investor_profile,
)


router = APIRouter(
    prefix="/investors",
    tags=["Investor Profile"],
)


def get_user_id(current_user):

    if current_user is None:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
        )

    if hasattr(current_user, "id"):
        return current_user.id

    if isinstance(current_user, dict):

        user_id = (
            current_user.get("id")
            or current_user.get("user_id")
        )

        if user_id:
            return int(user_id)

    user_id = getattr(
        current_user,
        "user_id",
        None,
    )

    if user_id:
        return int(user_id)

    raise HTTPException(
        status_code=401,
        detail="Invalid authentication token",
    )


@router.get(
    "/profile",
    response_model=InvestorProfileResponse,
)
def get_profile(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):

    user_id = get_user_id(
        current_user
    )

    return get_investor_profile(
        db=db,
        user_id=user_id,
    )


@router.put(
    "/profile",
    response_model=InvestorProfileResponse,
)
def update_profile(
    data: InvestorProfileUpdate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):

    user_id = get_user_id(
        current_user
    )

    return update_investor_profile(
        db=db,
        user_id=user_id,
        data=data,
    )