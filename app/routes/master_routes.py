from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.schemas.master_schemas import (
    AccountTypeResponse,
    InterestRateResponse,
    InvestmentStatusResponse,
    InvestmentTenureResponse,
    InvestorRequestStatusResponse,
    KycStatusResponse,
    PaymentMethodResponse,
    PaymentStatusResponse,
    RoleResponse,
    SettlementStatusResponse,
    StateResponse,
    UserStatusResponse,
    BranchResponse,
    AllMastersResponse,
)

from app.services.master_service import (
    get_account_types,
    get_interest_rates,
    get_investment_statuses,
    get_investment_tenures,
    get_investor_request_statuses,
    get_kyc_statuses,
    get_payment_methods,
    get_payment_statuses,
    get_roles,
    get_settlement_statuses,
    get_states,
    get_user_statuses,
    get_branches,
    get_all_masters,
)

from app.database import get_db


router = APIRouter(
    prefix="/masters",
    tags=["Masters"],
)


@router.get(
    "/account-types",
    response_model=list[AccountTypeResponse],
)
def account_types(
    db: Session = Depends(get_db),
):
    return get_account_types(db)


@router.get(
    "/interest-rates",
    response_model=list[InterestRateResponse],
)
def interest_rates(
    db: Session = Depends(get_db),
):
    return get_interest_rates(db)


@router.get(
    "/investment-statuses",
    response_model=list[InvestmentStatusResponse],
)
def investment_statuses(
    db: Session = Depends(get_db),
):
    return get_investment_statuses(db)


@router.get(
    "/investment-tenures",
    response_model=list[InvestmentTenureResponse],
)
def investment_tenures(
    db: Session = Depends(get_db),
):
    return get_investment_tenures(db)


@router.get(
    "/investor-request-statuses",
    response_model=list[InvestorRequestStatusResponse],
)
def investor_request_statuses(
    db: Session = Depends(get_db),
):
    return get_investor_request_statuses(db)


@router.get(
    "/kyc-statuses",
    response_model=list[KycStatusResponse],
)
def kyc_statuses(
    db: Session = Depends(get_db),
):
    return get_kyc_statuses(db)


@router.get(
    "/payment-methods",
    response_model=list[PaymentMethodResponse],
)
def payment_methods(
    db: Session = Depends(get_db),
):
    return get_payment_methods(db)


@router.get(
    "/payment-statuses",
    response_model=list[PaymentStatusResponse],
)
def payment_statuses(
    db: Session = Depends(get_db),
):
    return get_payment_statuses(db)


@router.get(
    "/roles",
    response_model=list[RoleResponse],
)
def roles(
    db: Session = Depends(get_db),
):
    return get_roles(db)


@router.get(
    "/settlement-statuses",
    response_model=list[SettlementStatusResponse],
)
def settlement_statuses(
    db: Session = Depends(get_db),
):
    return get_settlement_statuses(db)


@router.get(
    "/states",
    response_model=list[StateResponse],
)
def states(
    db: Session = Depends(get_db),
):
    return get_states(db)


@router.get(
    "/user-statuses",
    response_model=list[UserStatusResponse],
)
def user_statuses(
    db: Session = Depends(get_db),
):
    return get_user_statuses(db)


@router.get(
    "/branches",
    response_model=list[BranchResponse],
)
def branches(
    state_id: int | None = Query(
        default=None
    ),
    db: Session = Depends(get_db),
):
    return get_branches(
        db=db,
        state_id=state_id,
    )


@router.get(
    "/all",
    response_model=AllMastersResponse,
)
def all_masters(
    db: Session = Depends(get_db),
):
    return get_all_masters(db)