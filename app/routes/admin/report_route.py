from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)
from sqlalchemy.orm import Session

from app.database import get_db
from app.utils.auth_utils import decode_access_token

from app.schemas.admin.report_schemas import (
    ReportDashboardResponse,
    ReportSummaryResponse,
    ReportChartResponse,
    ReportInvestmentResponse,
)

from app.services.admin.report_service import (
    get_admin_report_summary,
    get_monthly_investment_trend,
    get_investor_growth,
    get_investment_status_distribution,
    get_recent_investments,
    get_admin_report_dashboard,
)


router = APIRouter(
    prefix="/admin/reports",
    tags=["Admin Reports"],
)

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials =
    Depends(security),
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
    current_user: dict =
    Depends(get_current_user),
):
    role = str(
        current_user.get("role", "")
    ).upper()

    if role not in {
        "ADMIN",
        "SUPERADMIN",
    }:
        raise HTTPException(
            status_code=403,
            detail="Admin access required.",
        )

    return current_user


@router.get(
    "/dashboard",
    response_model=ReportDashboardResponse,
)
def admin_report_dashboard(
    db: Session = Depends(get_db),
    current_user: dict =
    Depends(require_admin),
):
    data = get_admin_report_dashboard(
        db=db,
    )

    return {
        "success": True,
        **data,
    }


@router.get(
    "/summary",
    response_model=ReportSummaryResponse,
)
def admin_report_summary(
    db: Session = Depends(get_db),
    current_user: dict =
    Depends(require_admin),
):
    return {
        "success": True,
        "data": get_admin_report_summary(
            db=db,
        ),
    }


@router.get(
    "/monthly-investments",
    response_model=ReportChartResponse,
)
def admin_monthly_investments(
    db: Session = Depends(get_db),
    current_user: dict =
    Depends(require_admin),
):
    return {
        "success": True,
        "data": get_monthly_investment_trend(
            db=db,
        ),
    }


@router.get(
    "/investor-growth",
    response_model=ReportChartResponse,
)
def admin_investor_growth(
    db: Session = Depends(get_db),
    current_user: dict =
    Depends(require_admin),
):
    return {
        "success": True,
        "data": get_investor_growth(
            db=db,
        ),
    }


@router.get(
    "/status-distribution",
    response_model=ReportChartResponse,
)
def admin_status_distribution(
    db: Session = Depends(get_db),
    current_user: dict =
    Depends(require_admin),
):
    return {
        "success": True,
        "data": get_investment_status_distribution(
            db=db,
        ),
    }


@router.get(
    "/investments",
    response_model=ReportInvestmentResponse,
)
def admin_report_investments(
    limit: int = 10,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: dict =
    Depends(require_admin),
):
    if limit < 1 or limit > 100:
        raise HTTPException(
            status_code=400,
            detail="Limit must be between 1 and 100.",
        )

    if offset < 0:
        raise HTTPException(
            status_code=400,
            detail="Offset cannot be negative.",
        )

    data = get_recent_investments(
        db=db,
        limit=limit,
        offset=offset,
    )

    return {
        "success": True,
        "data": data,
        "total": len(data),
    }