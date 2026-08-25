from datetime import date

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
)

from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)

from sqlalchemy.orm import Session

from app.database import get_db
from app.utils.auth_utils import decode_access_token

from app.services.admin.report_service import (
    get_admin_report_filters,
    get_admin_report_summary,
    get_monthly_investment_trend,
    get_investor_growth,
    get_investment_status_distribution,
    get_recent_investments,
    get_pending_investments,
    get_admin_report_dashboard,
)


router = APIRouter(
    prefix="/admin/reports",
    tags=["Admin Reports"],
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


def get_role_name(
    current_user: dict,
) -> str:
    role = current_user.get(
        "role"
    )

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
) -> int:
    role_name = get_role_name(
        current_user
    )

    if role_name != "ADMIN":
        raise HTTPException(
            status_code=403,
            detail=(
                "Reports are available only "
                "for branch admins."
            ),
        )

    branch_id = current_user.get(
        "branch_id"
    )

    if branch_id is None:
        raise HTTPException(
            status_code=403,
            detail=(
                "Branch is not assigned "
                "to this admin."
            ),
        )

    try:
        branch_id = int(
            branch_id
        )
    except (
        TypeError,
        ValueError,
    ):
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


def require_admin(
    current_user: dict = Depends(
        get_current_user
    ),
):
    if get_role_name(
        current_user
    ) != "ADMIN":
        raise HTTPException(
            status_code=403,
            detail="Admin access required.",
        )

    return current_user


@router.get("/filters")
def admin_report_filters(
    db: Session = Depends(get_db),
    current_user: dict = Depends(
        require_admin
    ),
):
    branch_id = get_admin_branch_id(
        current_user
    )

    try:
        return {
            "success": True,
            **get_admin_report_filters(
                db=db,
                branch_id=branch_id,
            ),
        }

    except HTTPException:
        raise

    except Exception as exc:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )


@router.get("/dashboard")
def admin_report_dashboard(
    year: int = Query(
        default=None,
        ge=2000,
        le=2100,
    ),
    db: Session = Depends(get_db),
    current_user: dict = Depends(
        require_admin
    ),
):
    if year is None:
        year = date.today().year

    branch_id = get_admin_branch_id(
        current_user
    )

    try:
        data = get_admin_report_dashboard(
            db=db,
            year=year,
            branch_id=branch_id,
        )

        return {
            "success": True,
            "year": year,
            "branch_id": branch_id,
            **data,
        }

    except HTTPException:
        raise

    except Exception as exc:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )


@router.get("/summary")
def admin_report_summary(
    year: int = Query(
        default=None,
        ge=2000,
        le=2100,
    ),
    db: Session = Depends(get_db),
    current_user: dict = Depends(
        require_admin
    ),
):
    if year is None:
        year = date.today().year

    branch_id = get_admin_branch_id(
        current_user
    )

    try:
        data = get_admin_report_summary(
            db=db,
            year=year,
            branch_id=branch_id,
        )

        return {
            "success": True,
            "year": year,
            "branch_id": branch_id,
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


@router.get("/monthly-investments")
def admin_monthly_investments(
    year: int = Query(
        default=None,
        ge=2000,
        le=2100,
    ),
    db: Session = Depends(get_db),
    current_user: dict = Depends(
        require_admin
    ),
):
    if year is None:
        year = date.today().year

    branch_id = get_admin_branch_id(
        current_user
    )

    try:
        data = get_monthly_investment_trend(
            db=db,
            year=year,
            branch_id=branch_id,
        )

        return {
            "success": True,
            "year": year,
            "branch_id": branch_id,
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


@router.get("/investor-growth")
def admin_investor_growth(
    year: int = Query(
        default=None,
        ge=2000,
        le=2100,
    ),
    db: Session = Depends(get_db),
    current_user: dict = Depends(
        require_admin
    ),
):
    if year is None:
        year = date.today().year

    branch_id = get_admin_branch_id(
        current_user
    )

    try:
        data = get_investor_growth(
            db=db,
            year=year,
            branch_id=branch_id,
        )

        return {
            "success": True,
            "year": year,
            "branch_id": branch_id,
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


@router.get("/status-distribution")
def admin_status_distribution(
    year: int = Query(
        default=None,
        ge=2000,
        le=2100,
    ),
    db: Session = Depends(get_db),
    current_user: dict = Depends(
        require_admin
    ),
):
    if year is None:
        year = date.today().year

    branch_id = get_admin_branch_id(
        current_user
    )

    try:
        data = (
            get_investment_status_distribution(
                db=db,
                year=year,
                branch_id=branch_id,
            )
        )

        return {
            "success": True,
            "year": year,
            "branch_id": branch_id,
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


@router.get("/investments")
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
    current_user: dict = Depends(
        require_admin
    ),
):
    branch_id = get_admin_branch_id(
        current_user
    )

    try:
        data = get_recent_investments(
            db=db,
            branch_id=branch_id,
            limit=limit,
            offset=offset,
        )

        return {
            "success": True,
            "branch_id": branch_id,
            "data": data,
            "limit": limit,
            "offset": offset,
            "total": len(data),
        }

    except HTTPException:
        raise

    except Exception as exc:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )


@router.get("/pending-investments")
def admin_pending_investments(
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
    current_user: dict = Depends(
        require_admin
    ),
):
    branch_id = get_admin_branch_id(
        current_user
    )

    try:
        data = get_pending_investments(
            db=db,
            branch_id=branch_id,
            limit=limit,
            offset=offset,
        )

        return {
            "success": True,
            "branch_id": branch_id,
            "data": data,
            "limit": limit,
            "offset": offset,
            "total": len(data),
        }

    except HTTPException:
        raise

    except Exception as exc:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )
