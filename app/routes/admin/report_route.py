from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
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

def get_admin_branch_id(
    current_user: dict,
) -> Optional[int]:

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

    branch_id = current_user.get(
        "branch_id"
    )

    if branch_id is None:
        raise HTTPException(
            status_code=403,
            detail="Branch is not assigned to this admin.",
        )

    try:
        branch_id = int(branch_id)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=403,
            detail="Invalid admin branch.",
        )

    return branch_id


def require_admin(
    current_user: dict =
    Depends(get_current_user),
):
    role_name = get_role_name(
        current_user
    )

    if role_name not in {
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
    current_user: dict = Depends(require_admin),
):
    branch_id = get_admin_branch_id(
        current_user
    )

    data = get_admin_report_dashboard(
        db=db,
        branch_id=branch_id,
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

    branch_id = get_admin_branch_id(
        current_user
    )

    return {
        "success": True,
        "data": get_admin_report_summary(
            db=db,
            branch_id=branch_id,
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

    branch_id = get_admin_branch_id(
        current_user
    )

    return {
        "success": True,
        "data": get_monthly_investment_trend(
            db=db,
            branch_id=branch_id,
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

    branch_id = get_admin_branch_id(
        current_user
    )

    return {
        "success": True,
        "data": get_investor_growth(
            db=db,
            branch_id=branch_id,
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

    branch_id = get_admin_branch_id(
        current_user
    )

    return {
        "success": True,
        "data": get_investment_status_distribution(
            db=db,
            branch_id=branch_id,
        ),
    }


@router.get(
    "/investments",
    response_model=ReportInvestmentResponse,
)
def admin_report_investments(
    limit: int = Query(
        default=10,
        ge=1,
        le=100,
    ),
    offset: int = Query(
        default=0,
        ge=0,
    ),
    db: Session = Depends(get_db),
    current_user: dict =
    Depends(require_admin),
):

    branch_id = get_admin_branch_id(
        current_user
    )

    data = get_recent_investments(
        db=db,
        branch_id=branch_id,
        limit=limit,
        offset=offset,
    )

    return {
        "success": True,
        "data": data,
        "total": len(data),
    }