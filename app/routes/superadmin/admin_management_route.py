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

from pydantic import BaseModel, EmailStr

from sqlalchemy.orm import Session

from pwdlib import PasswordHash

from app.database import get_db
from app.utils.auth_utils import decode_access_token

from app.services.superadmin.admin_management_service import (
    get_superadmin_admins,
    get_superadmin_admin_details,
    get_superadmin_master_branches,
    get_superadmin_roles,
    get_superadmin_statuses,
    create_superadmin_admin,
    update_superadmin_admin,
    suspend_superadmin_admin,
)


router = APIRouter(
    prefix="/superadmin/admins",
    tags=["Super Admin Admin Management"],
)

security = HTTPBearer()

password_hash = PasswordHash.recommended()


# =========================================================
# REQUEST MODELS
# =========================================================

class AdminCreateRequest(BaseModel):
    full_name: str
    email: EmailStr
    mobile: str
    branch_id: int
    role_id: int
    status_id: int = 2
    password: str


class AdminUpdateRequest(BaseModel):
    full_name: str
    email: EmailStr
    mobile: str
    branch_id: int
    role_id: int
    status_id: int


# =========================================================
# AUTH
# =========================================================

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


# =========================================================
# GET ADMINS
# =========================================================

@router.get("")
def get_admins(
    search: Optional[str] = Query(
        default=None
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

    data = get_superadmin_admins(
        db=db,
        search=search,
    )

    return {
        "success": True,
        "data": data,
        "count": len(data),
        "total": len(data),
    }


# =========================================================
# BRANCH FILTER
# =========================================================

@router.get("/filters/branches")
def get_admin_branches(
    db: Session = Depends(get_db),
    current_user: dict = Depends(
        require_superadmin
    ),
):
    data = get_superadmin_master_branches(
        db=db
    )

    return {
        "success": True,
        "data": data,
    }


# =========================================================
# ROLE FILTER
# =========================================================

@router.get("/filters/roles")
def get_admin_roles(
    db: Session = Depends(get_db),
    current_user: dict = Depends(
        require_superadmin
    ),
):
    data = get_superadmin_roles(
        db=db
    )

    return {
        "success": True,
        "data": data,
    }


# =========================================================
# STATUS FILTER
# =========================================================

@router.get("/filters/statuses")
def get_admin_statuses(
    db: Session = Depends(get_db),
    current_user: dict = Depends(
        require_superadmin
    ),
):
    data = get_superadmin_statuses(
        db=db
    )

    return {
        "success": True,
        "data": data,
    }


# =========================================================
# ADMIN DETAILS
# =========================================================

@router.get("/{admin_id}")
def get_admin_details(
    admin_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(
        require_superadmin
    ),
):
    if admin_id <= 0:
        raise HTTPException(
            status_code=400,
            detail="Invalid admin ID.",
        )

    data = get_superadmin_admin_details(
        db=db,
        admin_id=admin_id,
    )

    if not data:
        raise HTTPException(
            status_code=404,
            detail="Admin not found.",
        )

    return {
        "success": True,
        "data": data,
    }


# =========================================================
# CREATE ADMIN
# =========================================================

@router.post("")
def create_admin(
    payload: AdminCreateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(
        require_superadmin
    ),
):
    try:

        # -----------------------------------------
        # CREATED BY
        # -----------------------------------------

        user_id = current_user.get("sub")

        if not user_id:
            raise HTTPException(
                status_code=401,
                detail="User ID missing from token.",
            )

        try:
            created_by = int(user_id)

        except (
            TypeError,
            ValueError,
        ):
            raise HTTPException(
                status_code=401,
                detail="Invalid user ID in token.",
            )

        # -----------------------------------------
        # CLEAN INPUT
        # -----------------------------------------

        full_name = payload.full_name.strip()
        email = str(payload.email).strip().lower()
        mobile = payload.mobile.strip()
        password = payload.password.strip()

        # -----------------------------------------
        # VALIDATION
        # -----------------------------------------

        if not full_name:
            raise HTTPException(
                status_code=400,
                detail="Full name is required.",
            )

        if not mobile:
            raise HTTPException(
                status_code=400,
                detail="Mobile number is required.",
            )

        if not password:
            raise HTTPException(
                status_code=400,
                detail="Password is required.",
            )

        if len(password) < 8:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Password must be at least "
                    "8 characters."
                ),
            )

        # -----------------------------------------
        # HASH PASSWORD
        # -----------------------------------------

        hashed_password = password_hash.hash(
            password
        )

        # -----------------------------------------
        # CREATE USER
        # -----------------------------------------

        data = create_superadmin_admin(
            db=db,
            full_name=full_name,
            email=email,
            mobile=mobile,
            branch_id=payload.branch_id,
            role_id=payload.role_id,
            status_id=payload.status_id,
            password=hashed_password,
            created_by=created_by,
        )

        return {
            "success": True,
            "message": data.get(
                "message",
                "Admin created successfully.",
            ),
            "data": data,
        }

    except HTTPException:
        raise

    except ValueError as exc:
        db.rollback()

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except Exception as exc:
        db.rollback()

        print(
            "ADMIN CREATION ERROR:",
            repr(exc),
        )

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )


# =========================================================
# UPDATE ADMIN
# =========================================================

@router.put("/{admin_id}")
def update_admin(
    admin_id: int,
    payload: AdminUpdateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(
        require_superadmin
    ),
):
    if admin_id <= 0:
        raise HTTPException(
            status_code=400,
            detail="Invalid admin ID.",
        )

    try:

        data = update_superadmin_admin(
            db=db,
            admin_id=admin_id,
            full_name=payload.full_name,
            email=str(payload.email),
            mobile=payload.mobile,
            branch_id=payload.branch_id,
            role_id=payload.role_id,
            status_id=payload.status_id,
        )

        return {
            "success": True,
            "message": data.get(
                "message",
                "Admin updated successfully.",
            ),
            "data": data,
        }

    except ValueError as exc:
        db.rollback()

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except Exception as exc:
        db.rollback()

        print(
            "ADMIN UPDATE ERROR:",
            repr(exc),
        )

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )


# =========================================================
# SUSPEND ADMIN
# =========================================================

@router.patch("/{admin_id}/suspend")
def suspend_admin(
    admin_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(
        require_superadmin
    ),
):
    if admin_id <= 0:
        raise HTTPException(
            status_code=400,
            detail="Invalid admin ID.",
        )

    user_id = current_user.get("sub")

    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="User ID missing from token.",
        )

    try:

        data = suspend_superadmin_admin(
            db=db,
            admin_id=admin_id,
            modified_by=int(user_id),
        )

        return {
            "success": True,
            "message": data.get(
                "message",
                "Admin suspended successfully.",
            ),
            "data": data,
        }

    except ValueError as exc:
        db.rollback()

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except Exception as exc:
        db.rollback()

        print(
            "ADMIN SUSPEND ERROR:",
            repr(exc),
        )

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )