from fastapi import APIRouter, Depends

from sqlalchemy.orm import Session

from app.database import get_db

from app.dependencies import (
    require_investor,
    require_admin_or_superadmin,
)

from app.schemas.investment_schemas import (
    InvestmentCreate,
    InvestmentResponse,
    InvestmentCalculationResponse,
    InvestmentApprove,
    InvestmentReject,
    TenureExtensionRequest,
    TenureExtensionResponse,
    PreCloseRequest,
    PreCloseResponse,
    BondResponse,
)

from app.services.investment_service import (
    calculate_investment,
    create_investment,
    get_my_investments,
    get_my_investment,
    get_my_investment_bond,
    get_branch_pending_investments,
    approve_investment,
    reject_investment,
    request_tenure_extension,
    request_preclose,
)

router = APIRouter(
    prefix="/investments",
    tags=["Investments"],
)


@router.post(
    "/calculate",
    response_model=InvestmentCalculationResponse,
)
def calculate_investment_api(
    data: InvestmentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_investor),
):
    return calculate_investment(
        db=db,
        investment_amount=data.investment_amount,
        tenure_id=data.tenure_id,
    )


@router.post(
    "/",
    response_model=InvestmentResponse,
)
def create_investment_api(
    data: InvestmentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_investor),
):
    return create_investment(
        db=db,
        user_id=current_user.id,
        data=data,
    )


@router.get(
    "/my-investments",
    response_model=list[InvestmentResponse],
)
def my_investments_api(
    db: Session = Depends(get_db),
    current_user=Depends(require_investor),
):
    return get_my_investments(
        db=db,
        user_id=current_user.id,
    )


@router.get(
    "/my-investments/{investment_id}",
    response_model=InvestmentResponse,
)
def my_investment_api(
    investment_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_investor),
):
    return get_my_investment(
        db=db,
        user_id=current_user.id,
        investment_id=investment_id,
    )


@router.get(
    "/my-investments/{investment_id}/bond",
    response_model=BondResponse,
)
def my_investment_bond_api(
    investment_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_investor),
):
    return get_my_investment_bond(
        db=db,
        user_id=current_user.id,
        investment_id=investment_id,
    )


@router.post(
    "/my-investments/{investment_id}/tenure-extension",
    response_model=TenureExtensionResponse,
)
def request_tenure_extension_api(
    investment_id: int,
    data: TenureExtensionRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_investor),
):
    return request_tenure_extension(
        db=db,
        user_id=current_user.id,
        investment_id=investment_id,
        extension_months=data.extension_months,
        remarks=data.remarks,
    )


@router.post(
    "/my-investments/{investment_id}/preclose",
    response_model=PreCloseResponse,
)
def request_preclose_api(
    investment_id: int,
    data: PreCloseRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_investor),
):
    return request_preclose(
        db=db,
        user_id=current_user.id,
        investment_id=investment_id,
        reason=data.reason,
    )


@router.get(
    "/admin/branch/{branch_id}/pending",
    response_model=list[InvestmentResponse],
)
def branch_pending_investments_api(
    branch_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin_or_superadmin),
):
    return get_branch_pending_investments(
        db=db,
        branch_id=branch_id,
    )


@router.put(
    "/admin/{investment_id}/approve",
    response_model=InvestmentResponse,
)
def approve_investment_api(
    investment_id: int,
    data: InvestmentApprove,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin_or_superadmin),
):
    return approve_investment(
        db=db,
        investment_id=investment_id,
        admin_id=current_user.id,
        data=data,
    )


@router.put(
    "/admin/{investment_id}/reject",
    response_model=InvestmentResponse,
)
def reject_investment_api(
    investment_id: int,
    data: InvestmentReject,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin_or_superadmin),
):
    return reject_investment(
        db=db,
        investment_id=investment_id,
        admin_id=current_user.id,
        data=data,
    )
