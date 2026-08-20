from typing import Optional

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
)

from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user

from app.schemas.admin.investor_management_schema import (
    ApproveInvestorKYCRequest,
    ApproveInvestorKYCResponse,
    InvestorDetailsResponse,
    InvestorManagementResponse,
    RejectInvestorRequest,
    RejectInvestorResponse,
)

from app.services.admin.investor_management_service import (
    approve_investor_kyc,
    get_investor_details,
    get_investor_management,
    reject_investor_kyc,
)


router = APIRouter(
    prefix="/admin/investors",
    tags=["Admin Investor Management"],
)


def get_role_name(current_user):

    role = getattr(
        current_user,
        "role",
        None,
    )

    if role is not None:

        if isinstance(role, str):
            return str(role).strip().upper()

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


def require_admin(
    current_user=Depends(get_current_user),
):

    if current_user is None:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
        )

    if not getattr(
        current_user,
        "is_active",
        True,
    ):
        raise HTTPException(
            status_code=403,
            detail="User account is inactive",
        )

    role_name = get_role_name(
        current_user
    )

    if role_name not in (
        "ADMIN",
        "SUPERADMIN",
    ):
        raise HTTPException(
            status_code=403,
            detail="Admin access required",
        )

    return current_user


def get_branch_id_for_user(
    current_user,
):

    role_name = get_role_name(
        current_user
    )

    if role_name == "SUPERADMIN":
        return None

    if role_name != "ADMIN":
        raise HTTPException(
            status_code=403,
            detail="Admin access required",
        )

    branch_id = getattr(
        current_user,
        "branch_id",
        None,
    )

    if branch_id is None:
        raise HTTPException(
            status_code=403,
            detail="Branch is not assigned to this admin",
        )

    try:
        branch_id = int(branch_id)
    except (
        TypeError,
        ValueError,
    ):
        raise HTTPException(
            status_code=403,
            detail="Invalid admin branch",
        )

    if branch_id <= 0:
        raise HTTPException(
            status_code=403,
            detail="Invalid admin branch",
        )

    return branch_id


@router.get(
    "",
    response_model=InvestorManagementResponse,
)
def investor_management(
    status_name: Optional[str] = Query(
        default=None
    ),
    kyc_status_name: Optional[str] = Query(
        default=None
    ),
    search_text: Optional[str] = Query(
        default=None
    ),
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    offset: int = Query(
        default=0,
        ge=0,
    ),
    current_user=Depends(
        require_admin
    ),
    db: Session = Depends(
        get_db
    ),
):

    branch_id = get_branch_id_for_user(
        current_user
    )

    return get_investor_management(
        db=db,
        status_name=status_name,
        kyc_status_name=kyc_status_name,
        search_text=search_text,
        limit=limit,
        offset=offset,
        branch_id=branch_id,
    )


@router.get(
    "/{investor_registration_id}",
    response_model=InvestorDetailsResponse,
)
def investor_details(
    investor_registration_id: int,
    current_user=Depends(
        require_admin
    ),
    db: Session = Depends(
        get_db
    ),
):

    branch_id = get_branch_id_for_user(
        current_user
    )

    return get_investor_details(
        db=db,
        investor_registration_id=investor_registration_id,
        branch_id=branch_id,
    )


@router.put(
    "/{investor_id}/approve",
    response_model=ApproveInvestorKYCResponse,
)
def approve_investor(
    investor_id: str,
    request: ApproveInvestorKYCRequest,
    current_user=Depends(
        require_admin
    ),
    db: Session = Depends(
        get_db
    ),
):

    approved_by = getattr(
        current_user,
        "id",
        None,
    )

    if not approved_by:
        raise HTTPException(
            status_code=401,
            detail="Admin user ID not found",
        )

    branch_id = get_branch_id_for_user(
        current_user
    )

    if branch_id is None:
        branch_id = request.branch_id

        if branch_id is None:
            raise HTTPException(
                status_code=400,
                detail="Branch ID is required for SuperAdmin approval",
            )

        try:
            branch_id = int(branch_id)
        except (
            TypeError,
            ValueError,
        ):
            raise HTTPException(
                status_code=400,
                detail="Invalid branch ID",
            )

        if branch_id <= 0:
            raise HTTPException(
                status_code=400,
                detail="Invalid branch ID",
            )

    return approve_investor_kyc(
        db=db,
        investor_id=investor_id,
        branch_id=branch_id,
        approved_by=approved_by,
        remarks=request.remarks,
    )


@router.put(
    "/{investor_id}/reject",
    response_model=RejectInvestorResponse,
)
def reject_investor(
    investor_id: str,
    request: RejectInvestorRequest,
    current_user=Depends(
        require_admin
    ),
    db: Session = Depends(
        get_db
    ),
):

    rejected_by = getattr(
        current_user,
        "id",
        None,
    )

    if not rejected_by:
        raise HTTPException(
            status_code=401,
            detail="Admin user ID not found",
        )

    branch_id = get_branch_id_for_user(
        current_user
    )

    rejection_reason = (
        request.remarks.strip()
        if request.remarks
        else "Investor rejected by admin"
    )

    return reject_investor_kyc(
        db=db,
        investor_id=investor_id,
        rejection_reason=rejection_reason,
        rejected_by=rejected_by,
        remarks=request.remarks,
        branch_id=branch_id,
    )
