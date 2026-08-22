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

from app.services.superadmin.investor_management_service import (
    get_investors,
    get_investor_details,
    get_investor_summary,
    get_superadmin_investor_branches,
    get_superadmin_investor_statuses,
)


router = APIRouter(
    prefix="/superadmin/investor-management",
    tags=["Super Admin Investor Management"],
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
    role_name = get_role_name(
        current_user
    )

    if role_name != "SUPERADMIN":
        raise HTTPException(
            status_code=403,
            detail="Super Admin access required.",
        )

    return current_user


@router.get("")
def investor_management(
    search: Optional[str] = Query(
        default=None
    ),
    branch_id: Optional[int] = Query(
        default=None,
        ge=1,
    ),
    status_id: Optional[int] = Query(
        default=None,
        ge=1,
    ),
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
        require_superadmin
    ),
):
    data = get_investors(
        db=db,
        search=search,
        branch_id=branch_id,
        status_id=status_id,
        limit=limit,
        offset=offset,
    )

    return {
        "success": True,
        "data": data,
        "limit": limit,
        "offset": offset,
        "total": len(data),
        "count": len(data),
    }


@router.get("/summary")
def investor_management_summary(
    db: Session = Depends(get_db),
    current_user: dict = Depends(
        require_superadmin
    ),
):
    data = get_investor_summary(
        db=db
    )

    return {
        "success": True,
        "data": data,
    }


@router.get("/filters/branches")
def investor_management_branches(
    db: Session = Depends(get_db),
    current_user: dict = Depends(
        require_superadmin
    ),
):
    data = get_superadmin_investor_branches(
        db=db
    )

    return {
        "success": True,
        "data": data,
        "total": len(data),
    }


@router.get("/filters/statuses")
def investor_management_statuses(
    db: Session = Depends(get_db),
    current_user: dict = Depends(
        require_superadmin
    ),
):
    data = get_superadmin_investor_statuses(
        db=db
    )

    return {
        "success": True,
        "data": data,
        "total": len(data),
    }


@router.get("/{investor_id}")
def investor_management_details(
    investor_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(
        require_superadmin
    ),
):
    data = get_investor_details(
        db=db,
        investor_id=investor_id,
    )

    if not data:
        raise HTTPException(
            status_code=404,
            detail="Investor not found.",
        )

    return {
        "success": True,
        "data": data,
    }