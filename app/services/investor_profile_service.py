from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.generated_models import (
    TnInvestorRegistration,
    TnApplicationUser,
    TnInvestorBankDetails,
    MasterState,
    MasterBranch,
    MasterKycStatus,
    MasterAccountType,
)

from app.schemas.investor_profile import (
    InvestorProfileUpdate,
)


def get_investor_profile(
    db: Session,
    user_id: int,
):
    investor = (
        db.query(TnInvestorRegistration)
        .filter(
            TnInvestorRegistration.user_id == user_id
        )
        .first()
    )

    if not investor:
        raise HTTPException(
            status_code=404,
            detail="Investor profile not found",
        )

    user = (
        db.query(TnApplicationUser)
        .filter(
            TnApplicationUser.id == user_id
        )
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="Application user not found",
        )

    state = None

    if investor.state_id:
        state = (
            db.query(MasterState)
            .filter(
                MasterState.id == investor.state_id
            )
            .first()
        )

    branch = None

    if investor.branch_id:
        branch = (
            db.query(MasterBranch)
            .filter(
                MasterBranch.id == investor.branch_id
            )
            .first()
        )

    status = None

    if investor.kyc_status_id:
        kyc_status = (
            db.query(MasterKycStatus)
            .filter(
                MasterKycStatus.id
                == investor.kyc_status_id
            )
            .first()
        )

        if kyc_status:
            status = kyc_status.kyc_status_name

    bank = (
        db.query(TnInvestorBankDetails)
        .filter(
            TnInvestorBankDetails.investor_id
            == investor.id
        )
        .filter(
            TnInvestorBankDetails.is_primary.is_(True)
        )
        .first()
    )

    if not bank:
        bank = (
            db.query(TnInvestorBankDetails)
            .filter(
                TnInvestorBankDetails.investor_id
                == investor.id
            )
            .first()
        )

    bank_data = None

    if bank:
        account_type_name = None

        if bank.account_type_id:
            account_type = (
                db.query(MasterAccountType)
                .filter(
                    MasterAccountType.id
                    == bank.account_type_id
                )
                .first()
            )

            if account_type:
                account_type_name = (
                    getattr(
                        account_type,
                        "account_type_name",
                        None,
                    )
                    or getattr(
                        account_type,
                        "name",
                        None,
                    )
                    or getattr(
                        account_type,
                        "account_type",
                        None,
                    )
                )

        bank_data = {
            "id": bank.id,
            "account_holder_name":
                bank.account_holder_name,
            "bank_name":
                bank.bank_name,
            "account_type_id":
                bank.account_type_id,
            "account_type":
                account_type_name,
            "account_number":
                bank.account_number,
            "ifsc_code":
                bank.ifsc_code,
            "is_primary":
                bank.is_primary,
        }

    return {
        "investor_id":
            investor.investor_id,

        "full_name":
            user.full_name,

        "mobile":
            user.mobile,

        "email":
            user.email,

        "date_of_birth":
            investor.date_of_birth,

        "aadhaar_number":
            investor.aadhaar_number,

        "address":
            investor.address,

        "city":
            investor.city,

        "state_id":
            investor.state_id,

        "state_name":
            state.state_name
            if state
            else None,

        "pincode":
            investor.pincode,

        "branch_id":
            investor.branch_id,

        "branch_name":
            branch.branch_name
            if branch
            else None,

        "status":
            status,

        "bank":
            bank_data,
    }


def update_investor_profile(
    db: Session,
    user_id: int,
    data: InvestorProfileUpdate,
):
    investor = (
        db.query(TnInvestorRegistration)
        .filter(
            TnInvestorRegistration.user_id == user_id
        )
        .first()
    )

    if not investor:
        raise HTTPException(
            status_code=404,
            detail="Investor profile not found",
        )

    user = (
        db.query(TnApplicationUser)
        .filter(
            TnApplicationUser.id == user_id
        )
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="Application user not found",
        )

    update_data = data.model_dump(
        exclude_unset=True
    )

    bank_data = update_data.pop(
        "bank",
        None,
    )

    if not update_data and bank_data is None:
        return get_investor_profile(
            db,
            user_id,
        )

    if "mobile" in update_data:
        mobile = update_data["mobile"]

        if mobile:
            existing_mobile = (
                db.query(TnApplicationUser)
                .filter(
                    TnApplicationUser.mobile
                    == mobile,
                    TnApplicationUser.id
                    != user_id,
                )
                .first()
            )

            if existing_mobile:
                raise HTTPException(
                    status_code=400,
                    detail="Mobile number already registered",
                )

    if "email" in update_data:
        email = update_data["email"]

        if email:
            existing_email = (
                db.query(TnApplicationUser)
                .filter(
                    TnApplicationUser.email
                    == email,
                    TnApplicationUser.id
                    != user_id,
                )
                .first()
            )

            if existing_email:
                raise HTTPException(
                    status_code=400,
                    detail="Email already registered",
                )

    if "state_id" in update_data:
        state_id = update_data["state_id"]

        if state_id is not None:
            state = (
                db.query(MasterState)
                .filter(
                    MasterState.id == state_id,
                    MasterState.is_active.is_(True),
                )
                .first()
            )

            if not state:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid state selected",
                )

    if "branch_id" in update_data:
        branch_id = update_data["branch_id"]

        if branch_id is not None:
            branch = (
                db.query(MasterBranch)
                .filter(
                    MasterBranch.id == branch_id,
                    MasterBranch.is_active.is_(True),
                )
                .first()
            )

            if not branch:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid branch selected",
                )

            selected_state_id = update_data.get(
                "state_id",
                investor.state_id,
            )

            if (
                selected_state_id is not None
                and branch.state_id
                != selected_state_id
            ):
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Selected branch does not "
                        "belong to selected state"
                    ),
                )

    if bank_data is not None:
        account_type_id = bank_data.get(
            "account_type_id"
        )

        if account_type_id is not None:
            account_type = (
                db.query(MasterAccountType)
                .filter(
                    MasterAccountType.id
                    == account_type_id
                )
                .first()
            )

            if not account_type:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid account type",
                )

        bank = (
            db.query(TnInvestorBankDetails)
            .filter(
                TnInvestorBankDetails.investor_id
                == investor.id
            )
            .filter(
                TnInvestorBankDetails.is_primary.is_(True)
            )
            .first()
        )

        if not bank:
            bank = (
                db.query(TnInvestorBankDetails)
                .filter(
                    TnInvestorBankDetails.investor_id
                    == investor.id
                )
                .first()
            )

        if bank:
            if (
                bank_data.get(
                    "account_holder_name"
                )
                is not None
            ):
                bank.account_holder_name = (
                    bank_data[
                        "account_holder_name"
                    ]
                )

            if (
                bank_data.get("bank_name")
                is not None
            ):
                bank.bank_name = (
                    bank_data["bank_name"]
                )

            if (
                bank_data.get(
                    "account_type_id"
                )
                is not None
            ):
                bank.account_type_id = (
                    bank_data[
                        "account_type_id"
                    ]
                )

            if (
                bank_data.get("account_number")
                is not None
            ):
                bank.account_number = (
                    bank_data[
                        "account_number"
                    ]
                )

            if (
                bank_data.get("ifsc_code")
                is not None
            ):
                bank.ifsc_code = (
                    bank_data["ifsc_code"]
                    .strip()
                    .upper()
                )

            bank.is_primary = True

        else:
            bank = TnInvestorBankDetails(
                investor_id=investor.id,
                account_holder_name=(
                    bank_data.get(
                        "account_holder_name"
                    )
                    or user.full_name
                ),
                bank_name=(
                    bank_data.get(
                        "bank_name"
                    )
                    or ""
                ),
                account_type_id=(
                    bank_data.get(
                        "account_type_id"
                    )
                ),
                account_number=(
                    bank_data.get(
                        "account_number"
                    )
                    or ""
                ),
                ifsc_code=(
                    bank_data.get(
                        "ifsc_code"
                    )
                    or ""
                ).upper(),
                is_primary=True,
                created_by=user_id,
            )

            db.add(bank)

    user_fields = {
        "full_name",
        "mobile",
        "email",
    }

    investor_fields = {
        "date_of_birth",
        "address",
        "city",
        "state_id",
        "pincode",
        "branch_id",
    }

    for field, value in update_data.items():

        if field in user_fields:
            setattr(
                user,
                field,
                value,
            )

        elif field in investor_fields:
            setattr(
                investor,
                field,
                value,
            )

    try:
        db.commit()

        db.refresh(user)
        db.refresh(investor)

    except Exception as exc:
        db.rollback()

        print(
            "Investor profile update error:",
            exc,
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to update investor profile",
        )

    return get_investor_profile(
        db,
        user_id,
    )