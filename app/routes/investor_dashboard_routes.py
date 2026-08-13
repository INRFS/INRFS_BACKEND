from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.schemas.investor_dashboard_schema import InvestorDashboardResponse
from app.services.investor_dashboard_service import get_investor_dashboard

router = APIRouter(
    prefix="/investor",
    tags=["Investor Dashboard"],
)


@router.get(
    "/dashboard",
    response_model=InvestorDashboardResponse,
)
def investor_dashboard(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    role_name = None

    role_value = getattr(current_user, "role", None)

    if role_value is not None:
        if isinstance(role_value, str):
            role_name = role_value
        else:
            role_name = getattr(role_value, "role_name", None)

    if not role_name:
        role_name = getattr(current_user, "role_name", None)

    if not role_name:
        role_name = getattr(current_user, "rolename", None)

    if not role_name:
        role_id = getattr(current_user, "role_id", None)

        if role_id is not None:
            result = db.execute(
                """
                SELECT role_name
                FROM master_role
                WHERE id = :role_id
                LIMIT 1
                """,
                {
                    "role_id": role_id,
                },
            )

            row = result.first()

            if row:
                role_name = row[0]

    if not role_name or str(role_name).strip().upper() != "INVESTOR":
        raise HTTPException(
            status_code=403,
            detail="Investor access required",
        )

    investor_id = getattr(current_user, "investor_id", None)

    if not investor_id:
        investor_id = getattr(current_user, "login_id", None)

    if not investor_id:
        investor_id = getattr(current_user, "username", None)

    if not investor_id:
        raise HTTPException(
            status_code=401,
            detail="Investor ID not found for current user",
        )

    return get_investor_dashboard(
        db=db,
        investor_id=str(investor_id),
        year=datetime.now().year,
    )