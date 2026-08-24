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

from pydantic import BaseModel, Field

from sqlalchemy.orm import Session

from app.database import get_db
from app.utils.auth_utils import decode_access_token

from app.services.superadmin.branch_management_service import (
    get_superadmin_branches,
    get_superadmin_branch_details,
    get_superadmin_branch_states,
    create_superadmin_branch,
    update_superadmin_branch,
    delete_superadmin_branch,
)


router = APIRouter(
    prefix="/superadmin/branch-management",
    tags=[
        "Super Admin Branch Management"
    ],
)

security = HTTPBearer()


class BranchCreateRequest(BaseModel):
    branch_name: str = Field(
        ...,
        min_length=2,
        max_length=150,
    )

    city_name: str = Field(
        ...,
        min_length=2,
        max_length=100,
    )

    state_id: int = Field(
        ...,
        ge=1,
    )

    is_active: bool = True


class BranchUpdateRequest(BaseModel):
    branch_name: str = Field(
        ...,
        min_length=2,
        max_length=150,
    )

    city_name: str = Field(
        ...,
        min_length=2,
        max_length=100,
    )

    state_id: int = Field(
        ...,
        ge=1,
    )

    is_active: bool = True


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
def branch_management(
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
    if search is not None:
        search = search.strip()

        if not search:
            search = None

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
        "count": len(data),
        "total": len(data),
    }


@router.get("/states")
def branch_states(
    db: Session = Depends(get_db),
    current_user: dict = Depends(
        require_superadmin
    ),
):
    data = get_superadmin_branch_states(
        db=db
    )

    return {
        "success": True,
        "data": data,
    }


@router.get("/{branch_id}")
def branch_management_details(
    branch_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(
        require_superadmin
    ),
):
    if branch_id <= 0:
        raise HTTPException(
            status_code=400,
            detail="Invalid branch ID.",
        )

    data = get_superadmin_branch_details(
        db=db,
        branch_id=branch_id,
    )

    if not data:
        raise HTTPException(
            status_code=404,
            detail="Branch not found.",
        )

    return {
        "success": True,
        "data": data,
    }


@router.post("")
def add_branch(
    payload: BranchCreateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(
        require_superadmin
    ),
):
    try:
        data = create_superadmin_branch(
            db=db,
            branch_name=payload.branch_name,
            city_name=payload.city_name,
            state_id=payload.state_id,
            is_active=payload.is_active,
        )

        return {
            "success": True,
            "message":
                "Branch created successfully.",
            "data": data,
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


@router.put("/{branch_id}")
def edit_branch(
    branch_id: int,
    payload: BranchUpdateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(
        require_superadmin
    ),
):
    if branch_id <= 0:
        raise HTTPException(
            status_code=400,
            detail="Invalid branch ID.",
        )

    try:
        data = update_superadmin_branch(
            db=db,
            branch_id=branch_id,
            branch_name=payload.branch_name,
            city_name=payload.city_name,
            state_id=payload.state_id,
            is_active=payload.is_active,
        )

        return {
            "success": True,
            "message":
                "Branch updated successfully.",
            "data": data,
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


@router.delete("/{branch_id}")
def remove_branch(
    branch_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(
        require_superadmin
    ),
):
    if branch_id <= 0:
        raise HTTPException(
            status_code=400,
            detail="Invalid branch ID.",
        )

    try:
        data = delete_superadmin_branch(
            db=db,
            branch_id=branch_id,
        )

        return {
            "success": True,
            "message":
                "Branch deactivated successfully.",
            "data": data,
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )