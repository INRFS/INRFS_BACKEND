from typing import Optional

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

from app.services.superadmin.superadmin_reports_service import (
    get_report_filters,
    get_investments,
    get_investment_details,
    get_admin_report,
    get_investor_report,
    get_settlement_report,
    get_extension_report,
)


router = APIRouter(
    prefix="/superadmin/reports",
    tags=["Super Admin Reports"],
)

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(
        security
    ),
):
    payload = decode_access_token(
        credentials.credentials
    )

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


def require_superadmin(
    current_user: dict = Depends(
        get_current_user
    ),
):
    if get_role_name(
        current_user
    ) != "SUPERADMIN":
        raise HTTPException(
            status_code=403,
            detail="Super Admin access required.",
        )

    return current_user


@router.get("/filters")
def report_filters(
    db: Session = Depends(get_db),
    current_user: dict = Depends(
        require_superadmin
    ),
):
    try:
        return get_report_filters(
            db=db
        )

    except HTTPException:
        raise

    except Exception as exc:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )


@router.get("/investments")
def report_investments(
    search: Optional[str] = Query(
        default=None
    ),
    branch_id: Optional[int] = Query(
        default=None
    ),
    admin_id: Optional[int] = Query(
        default=None
    ),
    status_id: Optional[int] = Query(
        default=None
    ),
    from_date: Optional[str] = Query(
        default=None
    ),
    to_date: Optional[str] = Query(
        default=None
    ),
    limit: int = Query(
        default=500,
        ge=1,
        le=500,
    ),
    offset: int = Query(
        default=0,
        ge=0,
    ),
    db: Session = Depends(get_db),
    current_user: dict = Depends(
        require_superadmin
    ),
):
    try:
        return get_investments(
            db=db,
            search=search,
            branch_id=branch_id,
            admin_id=admin_id,
            status_id=status_id,
            from_date=from_date,
            to_date=to_date,
            limit=limit,
            offset=offset,
        )

    except HTTPException:
        raise

    except Exception as exc:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )


@router.get(
    "/investments/{investment_id}"
)
def report_investment_details(
    investment_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(
        require_superadmin
    ),
):
    try:
        result = get_investment_details(
            db=db,
            investment_id=investment_id,
        )

        if not result.get("data"):
            raise HTTPException(
                status_code=404,
                detail="Investment not found.",
            )

        return result

    except HTTPException:
        raise

    except Exception as exc:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )


@router.get("/admins")
def report_admins(
    search: Optional[str] = Query(
        default=None
    ),
    branch_id: Optional[int] = Query(
        default=None
    ),
    status_id: Optional[int] = Query(
        default=None
    ),
    admin_id: Optional[int] = Query(
        default=None
    ),
    from_date: Optional[str] = Query(
        default=None
    ),
    to_date: Optional[str] = Query(
        default=None
    ),
    db: Session = Depends(get_db),
    current_user: dict = Depends(
        require_superadmin
    ),
):
    try:
        return get_admin_report(
            db=db,
            search=search,
            branch_id=branch_id,
            status_id=status_id,
            admin_id=admin_id,
            from_date=from_date,
            to_date=to_date,
        )

    except HTTPException:
        raise

    except Exception as exc:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )


@router.get("/investors")
def report_investors(
    search: Optional[str] = Query(
        default=None
    ),
    branch_id: Optional[int] = Query(
        default=None
    ),
    status_id: Optional[int] = Query(
        default=None
    ),
    admin_id: Optional[int] = Query(
        default=None
    ),
    from_date: Optional[str] = Query(
        default=None
    ),
    to_date: Optional[str] = Query(
        default=None
    ),
    db: Session = Depends(get_db),
    current_user: dict = Depends(
        require_superadmin
    ),
):
    try:
        return get_investor_report(
            db=db,
            search=search,
            branch_id=branch_id,
            status_id=status_id,
            admin_id=admin_id,
            from_date=from_date,
            to_date=to_date,
        )

    except HTTPException:
        raise

    except Exception as exc:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )


@router.get("/settlements")
def report_settlements(
    search: Optional[str] = Query(
        default=None
    ),
    branch_id: Optional[int] = Query(
        default=None
    ),
    admin_id: Optional[int] = Query(
        default=None
    ),
    status_id: Optional[int] = Query(
        default=None
    ),
    from_date: Optional[str] = Query(
        default=None
    ),
    to_date: Optional[str] = Query(
        default=None
    ),
    limit: int = Query(
        default=500,
        ge=1,
        le=500,
    ),
    offset: int = Query(
        default=0,
        ge=0,
    ),
    db: Session = Depends(get_db),
    current_user: dict = Depends(
        require_superadmin
    ),
):
    try:
        return get_settlement_report(
            db=db,
            search=search,
            branch_id=branch_id,
            admin_id=admin_id,
            status_id=status_id,
            from_date=from_date,
            to_date=to_date,
            limit=limit,
            offset=offset,
        )

    except HTTPException:
        raise

    except Exception as exc:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )


@router.get("/extensions")
def report_extensions(
    search: Optional[str] = Query(
        default=None
    ),
    branch_id: Optional[int] = Query(
        default=None
    ),
    admin_id: Optional[int] = Query(
        default=None
    ),
    status_id: Optional[int] = Query(
        default=None
    ),
    from_date: Optional[str] = Query(
        default=None
    ),
    to_date: Optional[str] = Query(
        default=None
    ),
    limit: int = Query(
        default=500,
        ge=1,
        le=500,
    ),
    offset: int = Query(
        default=0,
        ge=0,
    ),
    db: Session = Depends(get_db),
    current_user: dict = Depends(
        require_superadmin
    ),
):
    try:
        return get_extension_report(
            db=db,
            search=search,
            branch_id=branch_id,
            admin_id=admin_id,
            status_id=status_id,
            from_date=from_date,
            to_date=to_date,
            limit=limit,
            offset=offset,
        )

    except HTTPException:
        raise

    except Exception as exc:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )
