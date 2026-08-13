from sqlalchemy.orm import Session

from app.models.generated_models import (
    MasterAccountType,
    MasterInterestRate,
    MasterInvestmentStatus,
    MasterInvestmentTenure,
    MasterInvestorRequestStatus,
    MasterKycStatus,
    MasterPaymentMethod,
    MasterPaymentStatus,
    MasterRole,
    MasterSettlementStatus,
    MasterState,
    MasterUserStatus,
    MasterBranch,
)


def get_account_types(db: Session):
    return (
        db.query(MasterAccountType)
        .filter(MasterAccountType.is_active.is_(True))
        .order_by(MasterAccountType.id)
        .all()
    )


def get_interest_rates(db: Session):
    return (
        db.query(MasterInterestRate)
        .filter(MasterInterestRate.is_active.is_(True))
        .order_by(MasterInterestRate.id)
        .all()
    )


def get_investment_statuses(db: Session):
    return (
        db.query(MasterInvestmentStatus)
        .filter(MasterInvestmentStatus.is_active.is_(True))
        .order_by(MasterInvestmentStatus.id)
        .all()
    )


def get_investment_tenures(db: Session):
    return (
        db.query(MasterInvestmentTenure)
        .filter(MasterInvestmentTenure.is_active.is_(True))
        .order_by(MasterInvestmentTenure.tenure_months)
        .all()
    )


def get_investor_request_statuses(db: Session):
    return (
        db.query(MasterInvestorRequestStatus)
        .filter(MasterInvestorRequestStatus.is_active.is_(True))
        .order_by(MasterInvestorRequestStatus.id)
        .all()
    )


def get_kyc_statuses(db: Session):
    return (
        db.query(MasterKycStatus)
        .filter(MasterKycStatus.is_active.is_(True))
        .order_by(MasterKycStatus.id)
        .all()
    )


def get_payment_methods(db: Session):
    return (
        db.query(MasterPaymentMethod)
        .filter(MasterPaymentMethod.is_active.is_(True))
        .order_by(MasterPaymentMethod.id)
        .all()
    )


def get_payment_statuses(db: Session):
    return (
        db.query(MasterPaymentStatus)
        .filter(MasterPaymentStatus.is_active.is_(True))
        .order_by(MasterPaymentStatus.id)
        .all()
    )


def get_roles(db: Session):
    return (
        db.query(MasterRole)
        .filter(MasterRole.is_active.is_(True))
        .order_by(MasterRole.id)
        .all()
    )


def get_settlement_statuses(db: Session):
    return (
        db.query(MasterSettlementStatus)
        .filter(MasterSettlementStatus.is_active.is_(True))
        .order_by(MasterSettlementStatus.id)
        .all()
    )


def get_states(db: Session):
    return (
        db.query(MasterState)
        .filter(MasterState.is_active.is_(True))
        .order_by(MasterState.state_name)
        .all()
    )


def get_user_statuses(db: Session):
    return (
        db.query(MasterUserStatus)
        .filter(MasterUserStatus.is_active.is_(True))
        .order_by(MasterUserStatus.id)
        .all()
    )


def get_branches(
    db: Session,
    state_id: int | None = None,
):
    query = (
        db.query(MasterBranch)
        .filter(MasterBranch.is_active.is_(True))
    )

    if state_id is not None:
        query = query.filter(
            MasterBranch.state_id == state_id
        )

    return (
        query
        .order_by(MasterBranch.branch_name)
        .all()
    )


def get_all_masters(db: Session):
    return {
        "account_types": get_account_types(db),
        "interest_rates": get_interest_rates(db),
        "investment_statuses": get_investment_statuses(db),
        "investment_tenures": get_investment_tenures(db),
        "investor_request_statuses": get_investor_request_statuses(db),
        "kyc_statuses": get_kyc_statuses(db),
        "payment_methods": get_payment_methods(db),
        "payment_statuses": get_payment_statuses(db),
        "roles": get_roles(db),
        "settlement_statuses": get_settlement_statuses(db),
        "states": get_states(db),
        "user_statuses": get_user_statuses(db),
        "branches": get_branches(db),
    }