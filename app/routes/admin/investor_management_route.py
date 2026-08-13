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


# =========================================================
# ADMIN AUTHORIZATION
# =========================================================

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

    role_id = getattr(
        current_user,
        "role_id",
        None,
    )

    if role_id not in (1, 2):

        raise HTTPException(
            status_code=403,
            detail="Admin access required",
        )

    return current_user


# =========================================================
# GET INVESTORS
# =========================================================

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

    return get_investor_management(
        db=db,
        status_name=status_name,
        kyc_status_name=kyc_status_name,
        search_text=search_text,
        limit=limit,
        offset=offset,
    )


# =========================================================
# GET INVESTOR DETAILS
# =========================================================

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

    return get_investor_details(
        db=db,
        investor_registration_id=
            investor_registration_id,
    )


# =========================================================
# APPROVE INVESTOR KYC
# =========================================================

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

    if request.branch_id is None:

        raise HTTPException(
            status_code=400,
            detail="Branch ID is required",
        )

    return approve_investor_kyc(
        db=db,
        investor_id=investor_id,
        branch_id=request.branch_id,
        approved_by=approved_by,
        remarks=request.remarks,
    )


# =========================================================
# REJECT INVESTOR
# =========================================================

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

    rejection_reason = (
        request.remarks.strip()
        if request.remarks
        else "Investor rejected by admin"
    )

    return reject_investor_kyc(
        db=db,
        investor_id=investor_id,
        rejection_reason=
            rejection_reason,
        rejected_by=rejected_by,
        remarks=request.remarks,
    )