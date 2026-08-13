from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)
from sqlalchemy.orm import Session

from app.database import get_db
from app.utils.auth_utils import decode_access_token

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


def require_admin(
    current_user: dict = Depends(get_current_user),
):
    role = current_user.get("role")

    if role not in {
        "ADMIN",
        "SUPERADMIN",
        "Admin",
        "Super Admin",
        "admin",
        "superadmin",
    }:
        raise HTTPException(
            status_code=403,
            detail="Admin access required.",
        )

    return current_user


@router.get(
    "/summary",
    response_model=DashboardSummaryResponse,
)
def dashboard_summary(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    try:
        data = get_dashboard_summary(db)

        return {
            "success": True,
            "data": data,
        }

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
    current_user: dict = Depends(require_admin),
):
    try:
        data = get_investor_growth(db)

        return {
            "success": True,
            "data": data,
        }

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
    current_user: dict = Depends(require_admin),
):
    try:
        data = get_monthly_investment_trend(db)

        return {
            "success": True,
            "data": data,
        }

    except Exception as exc:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )