from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.investor_profile import (
    InvestorProfileResponse,
    InvestorProfileUpdate,
)
from app.services.investor_profile_service import (
    get_investor_profile,
    update_investor_profile,
)
from app.dependencies import get_current_user

router = APIRouter(
    prefix="/investors",
    tags=["Investor Profile"],
)


@router.get(
    "/profile",
    response_model=InvestorProfileResponse,
)
def get_profile(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return get_investor_profile(
        db=db,
        user_id=current_user.id,
    )


@router.put(
    "/profile",
    response_model=InvestorProfileResponse,
)
def update_profile(
    data: InvestorProfileUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return update_investor_profile(
        db=db,
        user_id=current_user.id,
        data=data,
    )