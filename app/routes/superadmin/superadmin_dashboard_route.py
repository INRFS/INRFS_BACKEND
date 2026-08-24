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

from app.services.superadmin.dashboard_service import (
    get_superadmin_dashboard,
    get_superadmin_branches,
    get_superadmin_branch_details,
    get_superadmin_admins,
    get_superadmin_admin_details,
    get_superadmin_investors,
    get_superadmin_investor_details,
    get_superadmin_investments,
    get_superadmin_payment_queue,
    get_superadmin_payment_details,
)


router = APIRouter(
    prefix="/superadmin",
    tags=["Super Admin"],
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


@router.get("/dashboard")
def superadmin_dashboard(
    db: Session = Depends(get_db),
    current_user: dict = Depends(
        require_superadmin
    ),
):
    data = get_superadmin_dashboard(
        db=db
    )

    return {
        "success": True,
        "data": data,
    }


@router.get("/branches")
def superadmin_branches(
    search: Optional[str] = Query(
        default=None
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
    data = get_superadmin_branches(
        db=db,
        search=search,
        limit=limit,
        offset=offset,
    )

    return {
        "success": True,
        "data": data,
        "limit": limit,
        "offset": offset,
        "total": len(data),
    }


@router.get("/branches/{branch_id}")
def superadmin_branch_details(
    branch_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(
        require_superadmin
    ),
):
    data = get_superadmin_branch_details(
        db=db,
        branch_id=branch_id,
    )

    return {
        "success": True,
        "data": data,
    }


@router.get("/admins")
def superadmin_admins(
    search: Optional[str] = Query(
        default=None
    ),
    db: Session = Depends(get_db),
    current_user: dict = Depends(
        require_superadmin
    ),
):
    data = get_superadmin_admins(
        db=db,
        search=search,
    )

    return {
        "success": True,
        "data": data,
        "total": len(data),
    }


@router.get("/admins/{admin_id}")
def superadmin_admin_details(
    admin_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(
        require_superadmin
    ),
):
    data = get_superadmin_admin_details(
        db=db,
        admin_id=admin_id,
    )

    return {
        "success": True,
        "data": data,
    }


@router.get("/investors")
def superadmin_investors(
    search: Optional[str] = Query(
        default=None
    ),
    branch_id: Optional[int] = Query(
        default=None
    ),
    status_id: Optional[int] = Query(
        default=None
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
    data = get_superadmin_investors(
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
    }


@router.get("/investors/{investor_id}")
def superadmin_investor_details(
    investor_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(
        require_superadmin
    ),
):
    data = get_superadmin_investor_details(
        db=db,
        investor_id=investor_id,
    )

    return {
        "success": True,
        "data": data,
    }


@router.get("/investments")
def superadmin_investments(
    search: Optional[str] = Query(
        default=None
    ),
    branch_id: Optional[int] = Query(
        default=None
    ),
    status_id: Optional[int] = Query(
        default=None
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
    data = get_superadmin_investments(
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
    }


@router.get("/payments")
def superadmin_payment_queue(
    payment_type: str = Query(
        ...
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
    data = get_superadmin_payment_queue(
        db=db,
        payment_type=payment_type,
        limit=limit,
        offset=offset,
    )

    return {
        "success": True,
        "data": data,
        "limit": limit,
        "offset": offset,
        "total": len(data),
    }


@router.get("/payments/{source_id}")
def superadmin_payment_details(
    source_id: int,
    payment_type: str = Query(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(
        require_superadmin
    ),
):
    data = get_superadmin_payment_details(
        db=db,
        source_id=source_id,
        payment_type=payment_type,
    )

    return {
        "success": True,
        "data": data,
    }