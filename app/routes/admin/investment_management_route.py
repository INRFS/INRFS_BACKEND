from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user

from app.schemas.admin.investment_management_schema import (
    ApproveAllMonthlyInterestRequest,
    InvestmentActionResponse,
    InvestmentApproveRequest,
    InvestmentBondDetailsResponse,
    InvestmentDetailsResponse,
    InvestmentManagementResponse,
    InvestmentRejectRequest,
    MonthlyInterestActionResponse,
    MonthlyInterestDetailsResponse,
    MonthlyInterestResponse,
    MonthlyInterestRejectRequest,
    SettlementResponse,
    TenureExtensionActionRequest,
    TenureExtensionDetailsResponse,
    TenureExtensionResponse,
)

from app.services.admin.investment_management_service import (
    approve_all_monthly_interest,
    approve_investment,
    approve_monthly_interest,
    approve_tenure_extension,
    create_tenure_timeout_settlement,
    get_all_investments,
    get_investment_bond_details,
    get_investment_details,
    get_monthly_interest,
    get_monthly_interest_details,
    get_pending_investments,
    get_pending_tenure_extensions,
    get_tenure_extension_details,
    reject_investment,
    reject_monthly_interest,
    reject_tenure_extension,
)


router = APIRouter(
    prefix="/admin",
    tags=["Admin Investment Management"],
)


def get_role_name(current_user):

    role = getattr(
        current_user,
        "role",
        None,
    )

    if isinstance(role, str):
        return role.strip().upper()

    if role is not None:
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


def get_admin_branch_id(current_user):

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


@router.get(
    "/investments",
    response_model=InvestmentManagementResponse,
)
def get_investments(
    bond_id: Optional[str] = Query(
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
    current_user=Depends(require_admin),
    db: Session = Depends(get_db),
):

    branch_id = get_admin_branch_id(
        current_user
    )

    return get_all_investments(
        db=db,
        branch_id=branch_id,
        bond_id=bond_id,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/investments/pending",
    response_model=InvestmentManagementResponse,
)
def get_pending_investment_list(
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    offset: int = Query(
        default=0,
        ge=0,
    ),
    current_user=Depends(require_admin),
    db: Session = Depends(get_db),
):

    branch_id = get_admin_branch_id(
        current_user
    )

    return get_pending_investments(
        db=db,
        branch_id=branch_id,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/investments/{investment_id}/bond",
    response_model=InvestmentBondDetailsResponse,
)
def get_investment_bond(
    investment_id: str,
    current_user=Depends(require_admin),
    db: Session = Depends(get_db),
):

    return get_investment_bond_details(
        db=db,
        investment_id=investment_id,
    )


@router.get(
    "/investments/{investment_id}",
    response_model=InvestmentDetailsResponse,
)
def get_investment(
    investment_id: str,
    current_user=Depends(require_admin),
    db: Session = Depends(get_db),
):

    return get_investment_details(
        db=db,
        investment_id=investment_id,
    )


@router.put(
    "/investments/{investment_id}/approve",
    response_model=InvestmentActionResponse,
)
def approve_investment_route(
    investment_id: str,
    request: InvestmentApproveRequest,
    current_user=Depends(require_admin),
    db: Session = Depends(get_db),
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

    try:

        return approve_investment(
            db=db,
            investment_id=investment_id,
            interest_rate=request.interest_rate,
            approved_by=approved_by,
            remarks=request.remarks,
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )


@router.put(
    "/investments/{investment_id}/reject",
    response_model=InvestmentActionResponse,
)
def reject_investment_route(
    investment_id: str,
    request: InvestmentRejectRequest,
    current_user=Depends(require_admin),
    db: Session = Depends(get_db),
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

    try:

        return reject_investment(
            db=db,
            investment_id=investment_id,
            rejected_by=rejected_by,
            rejection_reason=request.rejection_reason,
            remarks=request.remarks,
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )


@router.get(
    "/tenure-extensions/pending",
    response_model=TenureExtensionResponse,
)
def get_pending_extensions(
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    offset: int = Query(
        default=0,
        ge=0,
    ),
    current_user=Depends(require_admin),
    db: Session = Depends(get_db),
):

    branch_id = get_admin_branch_id(
        current_user
    )

    return get_pending_tenure_extensions(
        db=db,
        branch_id=branch_id,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/tenure-extensions/{request_id}",
    response_model=TenureExtensionDetailsResponse,
)
def get_extension_details(
    request_id: int,
    current_user=Depends(require_admin),
    db: Session = Depends(get_db),
):

    return get_tenure_extension_details(
        db=db,
        request_id=request_id,
    )


@router.put(
    "/tenure-extensions/{request_id}/approve",
    response_model=InvestmentActionResponse,
)
def approve_extension(
    request_id: int,
    request: TenureExtensionActionRequest,
    current_user=Depends(require_admin),
    db: Session = Depends(get_db),
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

    return approve_tenure_extension(
        db=db,
        request_id=request_id,
        approved_by=approved_by,
        remarks=request.remarks,
    )


@router.put(
    "/tenure-extensions/{request_id}/reject",
    response_model=InvestmentActionResponse,
)
def reject_extension(
    request_id: int,
    request: TenureExtensionActionRequest,
    current_user=Depends(require_admin),
    db: Session = Depends(get_db),
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

    return reject_tenure_extension(
        db=db,
        request_id=request_id,
        rejected_by=rejected_by,
        remarks=request.remarks,
    )


@router.get(
    "/monthly-interest",
    response_model=MonthlyInterestResponse,
)
def get_monthly_interest_route(
    interest_due_date: Optional[date] = Query(
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
    current_user=Depends(require_admin),
    db: Session = Depends(get_db),
):

    branch_id = get_admin_branch_id(
        current_user
    )

    return get_monthly_interest(
        db=db,
        branch_id=branch_id,
        interest_due_date=interest_due_date,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/monthly-interest/{interest_schedule_id}",
    response_model=MonthlyInterestDetailsResponse,
)
def get_monthly_interest_details_route(
    interest_schedule_id: int,
    current_user=Depends(require_admin),
    db: Session = Depends(get_db),
):

    return get_monthly_interest_details(
        db=db,
        interest_schedule_id=interest_schedule_id,
    )


@router.put(
    "/monthly-interest/{interest_schedule_id}/approve",
    response_model=MonthlyInterestActionResponse,
)
def approve_monthly_interest_route(
    interest_schedule_id: int,
    current_user=Depends(require_admin),
    db: Session = Depends(get_db),
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

    return approve_monthly_interest(
        db=db,
        interest_schedule_id=interest_schedule_id,
        approved_by=approved_by,
    )


@router.put(
    "/monthly-interest/{interest_schedule_id}/reject",
    response_model=MonthlyInterestActionResponse,
)
def reject_monthly_interest_route(
    interest_schedule_id: int,
    request: MonthlyInterestRejectRequest,
    current_user=Depends(require_admin),
    db: Session = Depends(get_db),
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

    return reject_monthly_interest(
        db=db,
        interest_schedule_id=interest_schedule_id,
        rejected_by=rejected_by,
        rejection_reason=request.rejection_reason,
        remarks=request.remarks,
    )


@router.put(
    "/monthly-interest/approve-all",
    response_model=MonthlyInterestActionResponse,
)
def approve_all_monthly_interest_route(
    request: ApproveAllMonthlyInterestRequest,
    current_user=Depends(require_admin),
    db: Session = Depends(get_db),
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

    return approve_all_monthly_interest(
        db=db,
        approved_by=approved_by,
        interest_due_date=request.interest_due_date,
    )


@router.post(
    "/investments/{investment_id}/settlement",
    response_model=SettlementResponse,
)
def create_settlement_route(
    investment_id: int,
    current_user=Depends(require_admin),
    db: Session = Depends(get_db),
):

    created_by = getattr(
        current_user,
        "id",
        None,
    )

    if not created_by:
        raise HTTPException(
            status_code=401,
            detail="Admin user ID not found",
        )

    return create_tenure_timeout_settlement(
        db=db,
        investment_id=investment_id,
        created_by=created_by,
    )