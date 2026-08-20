from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP

from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.models.generated_models import (
    TnInvestment,
    TnBond,
    TnInvestorRegistration,
    MasterInvestmentTenure,
    MasterInterestRate,
    MasterInvestmentStatus,
    MasterInvestorRequestStatus,
    TnTenureExtensionRequest,
    TnPrecloseRequest,
)

from app.schemas.investment_schemas import (
    InvestmentCreate,
    InvestmentApprove,
    InvestmentReject,
)


def money(value: Decimal) -> Decimal:
    return value.quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )


def add_months(
    start_date: date,
    months: int,
) -> date:
    month = start_date.month - 1 + months
    year = start_date.year + month // 12
    month = month % 12 + 1

    days_in_month = [
        31,
        29
        if year % 4 == 0
        and (year % 100 != 0 or year % 400 == 0)
        else 28,
        31,
        30,
        31,
        30,
        31,
        31,
        30,
        31,
        30,
        31,
    ]

    day = min(
        start_date.day,
        days_in_month[month - 1],
    )

    return date(
        year,
        month,
        day,
    )


def get_current_investor(
    db: Session,
    user_id: int,
):
    investor = (
        db.query(TnInvestorRegistration)
        .filter(
            TnInvestorRegistration.user_id == user_id,
            TnInvestorRegistration.is_active.is_(True),
        )
        .first()
    )

    if not investor:
        raise HTTPException(
            status_code=404,
            detail="Investor registration not found.",
        )

    return investor


def get_tenure(
    db: Session,
    tenure_id: int,
):
    tenure = (
        db.query(MasterInvestmentTenure)
        .filter(
            MasterInvestmentTenure.id == tenure_id,
            MasterInvestmentTenure.is_active.is_(True),
        )
        .first()
    )

    if not tenure:
        raise HTTPException(
            status_code=404,
            detail="Investment tenure not found.",
        )

    return tenure


def get_active_interest_rate(
    db: Session,
):
    rate = (
        db.query(MasterInterestRate)
        .filter(
            MasterInterestRate.is_active.is_(True)
        )
        .order_by(
            MasterInterestRate.id.desc()
        )
        .first()
    )

    if not rate:
        raise HTTPException(
            status_code=404,
            detail="Active interest rate not configured.",
        )

    return Decimal(
        str(rate.monthly_interest_rate)
    )


def get_status_id(
    db: Session,
    status_names: list[str],
):
    statuses = (
        db.query(MasterInvestmentStatus)
        .filter(
            MasterInvestmentStatus.is_active.is_(True)
        )
        .all()
    )

    wanted = {
        name.strip().lower()
        for name in status_names
    }

    for status in statuses:
        if (
            status.status_name.strip().lower()
            in wanted
        ):
            return status.id

    raise HTTPException(
        status_code=500,
        detail=(
            "Required investment status is not "
            "configured in master_investment_status."
        ),
    )


def get_request_status_id(
    db: Session,
    status_names: list[str],
):
    statuses = (
        db.query(
            MasterInvestorRequestStatus
        )
        .filter(
            MasterInvestorRequestStatus.is_active.is_(
                True
            )
        )
        .all()
    )

    wanted = {
        name.strip().lower()
        for name in status_names
    }

    for status in statuses:
        if (
            status.status_name.strip().lower()
            in wanted
        ):
            return status.id

    raise HTTPException(
        status_code=500,
        detail=(
            "Required investor request status "
            "is not configured."
        ),
    )


def generate_investment_id(
    db: Session,
):
    last_investment = (
        db.query(TnInvestment)
        .order_by(
            TnInvestment.id.desc()
        )
        .first()
    )

    next_number = (
        int(last_investment.id) + 1
        if last_investment
        else 1
    )

    return f"INV{next_number:06d}"


def calculate_investment(
    db: Session,
    investment_amount: Decimal,
    tenure_id: int,
):
    tenure = get_tenure(
        db,
        tenure_id,
    )

    interest_rate = get_active_interest_rate(
        db
    )

    monthly_interest = money(
        investment_amount
        * interest_rate
        / Decimal("100")
    )

    total_interest = money(
        monthly_interest
        * Decimal(tenure.tenure_months)
    )

    maturity_amount = money(
        investment_amount
        + total_interest
    )

    today = date.today()

    maturity_date = add_months(
        today,
        tenure.tenure_months,
    )

    return {
        "investment_amount": money(
            investment_amount
        ),
        "tenure_id": tenure.id,
        "tenure_months":
            tenure.tenure_months,
        "interest_rate":
            interest_rate,
        "expected_monthly_interest":
            monthly_interest,
        "expected_interest_amount":
            total_interest,
        "maturity_amount":
            maturity_amount,
        "maturity_date":
            maturity_date,
    }


def create_investment(
    db: Session,
    user_id: int,
    data: InvestmentCreate,
):
    investor = get_current_investor(
        db,
        user_id,
    )

    calculation = calculate_investment(
        db=db,
        investment_amount=
            data.investment_amount,
        tenure_id=data.tenure_id,
    )

    pending_status_id = get_status_id(
        db,
        [
            "PENDING",
            "PENDING ADMIN REVIEW",
            "PENDING_ADMIN_REVIEW",
            "SUBMITTED",
            "PENDING APPROVAL",
        ],
    )

    investment = TnInvestment(
        investor_registration_id=
            investor.id,
        tenure_id=
            calculation["tenure_id"],
        investment_amount=
            calculation["investment_amount"],
        interest_rate=
            calculation["interest_rate"],
        expected_interest_amount=
            calculation[
                "expected_interest_amount"
            ],
        maturity_amount=
            calculation["maturity_amount"],
        investment_status_id=
            pending_status_id,
        investment_id=
            generate_investment_id(db),
        investment_date=datetime.now(),
        maturity_date=
            calculation["maturity_date"],
        created_by=user_id,
    )

    db.add(investment)
    db.commit()
    db.refresh(investment)

    return investment


def get_my_investments(
    db: Session,
    user_id: int,
):
    investor = get_current_investor(
        db,
        user_id,
    )

    return (
        db.query(TnInvestment)
        .filter(
            TnInvestment
            .investor_registration_id
            == investor.id
        )
        .order_by(
            TnInvestment
            .investment_date.desc()
        )
        .all()
    )


def get_my_investment(
    db: Session,
    user_id: int,
    investment_id: int,
):
    investor = get_current_investor(
        db,
        user_id,
    )

    investment = (
        db.query(TnInvestment)
        .filter(
            TnInvestment.id ==
                investment_id,
            TnInvestment
                .investor_registration_id
                == investor.id,
        )
        .first()
    )

    if not investment:
        raise HTTPException(
            status_code=404,
            detail="Investment not found.",
        )

    return investment


def generate_bond_id(
    db: Session,
):
    last_bond = (
        db.query(TnBond)
        .order_by(TnBond.id.desc())
        .first()
    )

    next_number = (
        int(last_bond.id) + 1
        if last_bond
        else 1
    )

    return f"BOND{next_number:06d}"


def get_my_investment_bond(
    db: Session,
    user_id: int,
    investment_id: int,
):
    investor = get_current_investor(
        db,
        user_id,
    )

    investment = (
        db.query(TnInvestment)
        .filter(
            TnInvestment.id == investment_id,
            TnInvestment
                .investor_registration_id
                == investor.id,
        )
        .first()
    )

    if not investment:
        raise HTTPException(
            status_code=404,
            detail="Investment not found.",
        )

    active_status_id = get_status_id(
        db,
        [
            "ACTIVE",
            "APPROVED",
            "APPROVED ACTIVE",
        ],
    )

    if (
        investment.investment_status_id
        != active_status_id
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "Bond certificate is available "
                "only for active investments."
            ),
        )

    bond = (
        db.query(TnBond)
        .filter(
            TnBond.investment_id
            == investment.id
        )
        .first()
    )

    if not bond:
        bond = TnBond(
            bond_id=generate_bond_id(db),
            investment_id=investment.id,
            maturity_date=
                investment.maturity_date,
            issue_date=datetime.now(),
            remarks=(
                "Bond generated for "
                "active investment"
            ),
            created_by=user_id,
            modified_by=user_id,
            modified_date=datetime.now(),
        )

        db.add(bond)
        db.commit()
        db.refresh(bond)

    user = investor.tn_application_user_user

    return {
        "success": True,
        "data": {
            "id": bond.id,
            "bond_id": bond.bond_id,
            "bond_number": bond.bond_id,
            "investment_id": investment.id,
            "investment_code":
                investment.investment_id,
            "investor_registration_id":
                investor.id,
            "investor_id":
                investor.investor_id,
            "investor_name": getattr(
                user,
                "full_name",
                None,
            ),
            "mobile": getattr(
                user,
                "mobile",
                None,
            ),
            "email": getattr(
                user,
                "email",
                None,
            ),
            "investment_amount":
                investment.investment_amount,
            "amount":
                investment.investment_amount,
            "interest_rate":
                investment.interest_rate,
            "rate":
                investment.interest_rate,
            "expected_interest_amount":
                investment.expected_interest_amount,
            "maturity_amount":
                investment.maturity_amount,
            "investment_date":
                investment.investment_date,
            "maturity_date":
                investment.maturity_date,
            "issue_date":
                bond.issue_date,
            "status": "Active",
        },
    }


get_my_bond_by_investment = (
    get_my_investment_bond
)


def get_branch_pending_investments(
    db: Session,
    branch_id: int,
):
    pending_status_id = get_status_id(
        db,
        [
            "PENDING",
            "PENDING ADMIN REVIEW",
            "PENDING_ADMIN_REVIEW",
            "SUBMITTED",
            "PENDING APPROVAL",
        ],
    )

    return (
        db.query(TnInvestment)
        .join(
            TnInvestorRegistration,
            TnInvestorRegistration.id
            ==
            TnInvestment
                .investor_registration_id,
        )
        .filter(
            TnInvestorRegistration
                .branch_id
                == branch_id,
            TnInvestment
                .investment_status_id
                == pending_status_id,
        )
        .order_by(
            TnInvestment
                .investment_date.asc()
        )
        .all()
    )


def approve_investment(
    db: Session,
    investment_id: int,
    admin_id: int,
    data: InvestmentApprove,
):
    investment = (
        db.query(TnInvestment)
        .filter(
            TnInvestment.id ==
                investment_id
        )
        .first()
    )

    if not investment:
        raise HTTPException(
            status_code=404,
            detail="Investment not found.",
        )

    statuses = (
        db.query(MasterInvestmentStatus)
        .filter(
            MasterInvestmentStatus
                .is_active.is_(True)
        )
        .all()
    )

    status_map = {
        status.status_name
            .strip()
            .lower():
            status.id
        for status in statuses
    }

    approved_status_id = None

    for name in [
        "ACTIVE",
        "APPROVED",
        "APPROVED ACTIVE",
    ]:
        if name.lower() in status_map:
            approved_status_id = (
                status_map[name.lower()]
            )
            break

    if approved_status_id is None:
        raise HTTPException(
            status_code=500,
            detail=(
                "Active investment status "
                "is not configured."
            ),
        )

    tenure = get_tenure(
        db,
        investment.tenure_id,
    )

    amount = Decimal(
        str(investment.investment_amount)
    )

    rate = Decimal(
        str(data.interest_rate)
    )

    monthly_interest = money(
        amount
        * rate
        / Decimal("100")
    )

    total_interest = money(
        monthly_interest
        * Decimal(tenure.tenure_months)
    )

    maturity_amount = money(
        amount + total_interest
    )

    investment.interest_rate = rate

    investment.expected_interest_amount = (
        total_interest
    )

    investment.maturity_amount = (
        maturity_amount
    )

    investment.investment_status_id = (
        approved_status_id
    )

    investment.approved_by = admin_id
    investment.approved_date = datetime.now()
    investment.remarks = data.remarks
    investment.modified_by = admin_id
    investment.modified_date = datetime.now()

    existing_bond = (
        db.query(TnBond)
        .filter(
            TnBond.investment_id
            == investment.id
        )
        .first()
    )

    if not existing_bond:
        bond = TnBond(
            bond_id=generate_bond_id(db),
            investment_id=investment.id,
            maturity_date=
                investment.maturity_date,
            issue_date=datetime.now(),
            remarks=(
                "Bond generated on "
                "investment approval"
            ),
            created_by=admin_id,
            modified_by=admin_id,
            modified_date=datetime.now(),
        )

        db.add(bond)

    db.commit()
    db.refresh(investment)

    return investment


def reject_investment(
    db: Session,
    investment_id: int,
    admin_id: int,
    data: InvestmentReject,
):
    investment = (
        db.query(TnInvestment)
        .filter(
            TnInvestment.id ==
                investment_id
        )
        .first()
    )

    if not investment:
        raise HTTPException(
            status_code=404,
            detail="Investment not found.",
        )

    rejected_status_id = get_status_id(
        db,
        [
            "REJECTED",
            "REJECT",
            "DECLINED",
        ],
    )

    investment.investment_status_id = (
        rejected_status_id
    )

    investment.remarks = data.remarks
    investment.modified_by = admin_id
    investment.modified_date = datetime.now()

    db.commit()
    db.refresh(investment)

    return investment


def request_tenure_extension(
    db: Session,
    user_id: int,
    investment_id: int,
    extension_months: int,
    remarks: str | None = None,
):
    investor = get_current_investor(
        db,
        user_id,
    )

    investment = (
        db.query(TnInvestment)
        .filter(
            TnInvestment.id ==
                investment_id,
            TnInvestment
                .investor_registration_id
                == investor.id,
        )
        .first()
    )

    if not investment:
        raise HTTPException(
            status_code=404,
            detail="Investment not found.",
        )

    active_status_id = get_status_id(
        db,
        [
            "ACTIVE",
            "APPROVED",
            "APPROVED ACTIVE",
        ],
    )

    if (
        investment.investment_status_id
        != active_status_id
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "Tenure extension can be "
                "requested only for active "
                "investments."
            ),
        )

    existing_request = (
        db.query(TnTenureExtensionRequest)
        .filter(
            TnTenureExtensionRequest
                .investment_id
                == investment.id,
            TnTenureExtensionRequest
                .request_status_id
                ==
                get_request_status_id(
                    db,
                    [
                        "PENDING",
                        "PENDING APPROVAL",
                        "SUBMITTED",
                    ],
                ),
        )
        .first()
    )

    if existing_request:
        raise HTTPException(
            status_code=400,
            detail=(
                "A tenure extension request "
                "is already pending."
            ),
        )

    current_tenure = get_tenure(
        db,
        investment.tenure_id,
    )

    requested_total_months = (
        current_tenure.tenure_months
        + extension_months
    )

    requested_tenure = (
        db.query(MasterInvestmentTenure)
        .filter(
            MasterInvestmentTenure
                .tenure_months
                == requested_total_months,
            MasterInvestmentTenure
                .is_active.is_(True),
        )
        .first()
    )

    if not requested_tenure:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Investment tenure for "
                f"{requested_total_months} months "
                f"is not configured."
            ),
        )

    pending_request_status_id = (
        get_request_status_id(
            db,
            [
                "PENDING",
                "PENDING APPROVAL",
                "SUBMITTED",
            ],
        )
    )

    request = TnTenureExtensionRequest(
        investment_id=investment.id,
        current_tenure_id=
            current_tenure.id,
        requested_tenure_id=
            requested_tenure.id,
        request_status_id=
            pending_request_status_id,
        requested_date=datetime.now(),
        remarks=remarks,
        created_by=user_id,
    )

    db.add(request)
    db.commit()
    db.refresh(request)

    return {
        "success": True,
        "message": (
            "Tenure extension request "
            "submitted successfully."
        ),
        "data": {
            "id": request.id,
            "investment_id":
                request.investment_id,
            "current_tenure_id":
                request.current_tenure_id,
            "current_tenure_months":
                current_tenure.tenure_months,
            "requested_tenure_id":
                request.requested_tenure_id,
            "requested_tenure_months":
                requested_tenure.tenure_months,
            "extension_months":
                extension_months,
            "request_status_id":
                request.request_status_id,
            "requested_date":
                request.requested_date,
            "remarks":
                request.remarks,
        },
    }


def request_preclose(
    db: Session,
    user_id: int,
    investment_id: int,
    reason: str,
):
    investor = get_current_investor(
        db,
        user_id,
    )

    investment = (
        db.query(TnInvestment)
        .filter(
            TnInvestment.id ==
                investment_id,
            TnInvestment
                .investor_registration_id
                == investor.id,
        )
        .first()
    )

    if not investment:
        raise HTTPException(
            status_code=404,
            detail="Investment not found.",
        )

    active_status_id = get_status_id(
        db,
        [
            "ACTIVE",
            "APPROVED",
            "APPROVED ACTIVE",
        ],
    )

    if (
        investment.investment_status_id
        != active_status_id
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "Pre-close can be requested "
                "only for active investments."
            ),
        )

    pending_status_id = (
        get_request_status_id(
            db,
            [
                "PENDING",
                "PENDING APPROVAL",
                "SUBMITTED",
            ],
        )
    )

    existing_request = (
        db.query(TnPrecloseRequest)
        .filter(
            TnPrecloseRequest
                .investment_id
                == investment.id,
            TnPrecloseRequest
                .request_status_id
                == pending_status_id,
        )
        .first()
    )

    if existing_request:
        raise HTTPException(
            status_code=400,
            detail=(
                "A pre-close request "
                "is already pending."
            ),
        )

    request = TnPrecloseRequest(
        investment_id=investment.id,
        request_status_id=
            pending_status_id,
        preclose_reason=reason.strip(),
        requested_date=datetime.now(),
        created_by=user_id,
    )

    db.add(request)
    db.commit()
    db.refresh(request)

    return {
        "success": True,
        "message": (
            "Pre-close request "
            "submitted successfully."
        ),
        "data": {
            "id": request.id,
            "investment_id":
                request.investment_id,
            "request_status_id":
                request.request_status_id,
            "preclose_reason":
                request.preclose_reason,
            "requested_date":
                request.requested_date,
        },
    }