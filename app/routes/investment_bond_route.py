from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.services.investment_service import (
    get_my_investment_bond,
)


router = APIRouter(
    prefix="/investments",
    tags=["Investor Investments"],
)


@router.get(
    "/my-investments/{investment_id}/bond"
)
def get_my_investment_bond_route(
    investment_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user is None:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
        )

    user_id = getattr(
        current_user,
        "id",
        None,
    )

    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="User ID not found",
        )

    return get_my_investment_bond(
        db=db,
        user_id=user_id,
        investment_id=investment_id,
    )