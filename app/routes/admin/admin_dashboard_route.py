from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user

from app.schemas.admin.admin_dashboard_schemas import (
    DashboardSummaryResponse,
    DashboardInvestorGrowthResponse,
    DashboardMonthlyInvestmentTrendResponse,
)

from app.services.admin.admin_dashboard_service import (
    get_dashboard_summary,
    get_investor_growth,
    get_monthly_investment_trend,
)


router = APIRouter(
    prefix="/admin/dashboard",
    tags=["Admin Dashboard"],
)


def get_role_name(current_user):

    role = getattr(
        current_user,
        "role",
        None,
    )

    if role is not None:

        if isinstance(role, str):
            return role.strip().upper()

        role_name = getattr(
            role,
            "role_name",
            None,
        )

        if role_name:
            return str(
                role_name
            ).strip().upper()

    role_name = getattr(
        current_user,
        "role_name",
        None,
    )

    if role_name:
        return str(
            role_name
        ).strip().upper()

    return ""


def get_admin_branch_id(current_user):

    role_name = get_role_name(
        current_user
    )

    if role_name == "SUPERADMIN":
        return None

    if role_name != "ADMIN":
        raise HTTPException(
            status_code=403,
            detail="Admin access required.",
        )

    branch_id = getattr(
        current_user,
        "branch_id",
        None,
    )

    if branch_id is None:
        raise HTTPException(
            status_code=403,
            detail="Admin branch is not assigned.",
        )

    try:
        branch_id = int(branch_id)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=403,
            detail="Invalid admin branch.",
        )

    if branch_id <= 0:
        raise HTTPException(
            status_code=403,
            detail="Invalid admin branch.",
        )

    return branch_id


@router.get(
    "/summary",
    response_model=DashboardSummaryResponse,
)
def dashboard_summary(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):

    branch_id = get_admin_branch_id(
        current_user
    )

    try:

        data = get_dashboard_summary(
            db=db,
            branch_id=branch_id,
        )

        return {
            "success": True,
            "data": data,
        }

    except HTTPException:
        raise

    except Exception as exc:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )


@router.get(
    "/investor-growth",
    response_model=DashboardInvestorGrowthResponse,
)
def dashboard_investor_growth(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):

    branch_id = get_admin_branch_id(
        current_user
    )

    try:

        data = get_investor_growth(
            db=db,
            branch_id=branch_id,
        )

        return {
            "success": True,
            "data": data,
        }

    except HTTPException:
        raise

    except Exception as exc:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )


@router.get(
    "/monthly-investment-trend",
    response_model=DashboardMonthlyInvestmentTrendResponse,
)
def dashboard_monthly_investment_trend(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):

    branch_id = get_admin_branch_id(
        current_user
    )

    try:

        data = get_monthly_investment_trend(
            db=db,
            branch_id=branch_id,
        )

        return {
            "success": True,
            "data": data,
        }

    except HTTPException:
        raise

    except Exception as exc:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )