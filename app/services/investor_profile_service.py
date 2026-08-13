from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.generated_models import TnInvestorRegistration
from app.models.generated_models import TnApplicationUser
from app.models.generated_models import MasterState
from app.models.generated_models import MasterBranch
from app.schemas.investor_profile import InvestorProfileUpdate


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
            detail="User not found",
        )

    state = (
        db.query(MasterState)
        .filter(
            MasterState.id == investor.state_id
        )
        .first()
    )

    branch = (
        db.query(MasterBranch)
        .filter(
            MasterBranch.id == investor.branch_id
        )
        .first()
    )

    status = None

    if investor.kyc_status:
        status = investor.kyc_status.kyc_status_name

    return {
        "investor_id": investor.investor_id,
        "full_name": user.full_name,
        "mobile": user.mobile,
        "email": user.email,
        "date_of_birth": investor.date_of_birth,
        "aadhaar_number": investor.aadhaar_number,
        "address": investor.address,
        "city": investor.city,
        "state_id": investor.state_id,
        "state_name": state.state_name if state else None,
        "pincode": investor.pincode,
        "branch_id": investor.branch_id,
        "branch_name": branch.branch_name if branch else None,
        "status": status,
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
            detail="User not found",
        )

    update_data = data.model_dump(
        exclude_unset=True
    )

    if "mobile" in update_data:
        existing = (
            db.query(TnApplicationUser)
            .filter(
                TnApplicationUser.mobile
                == update_data["mobile"],
                TnApplicationUser.id != user_id,
            )
            .first()
        )

        if existing:
            raise HTTPException(
                status_code=400,
                detail="Mobile number already registered",
            )

    if "email" in update_data:
        existing = (
            db.query(TnApplicationUser)
            .filter(
                TnApplicationUser.email
                == update_data["email"],
                TnApplicationUser.id != user_id,
            )
            .first()
        )

        if existing:
            raise HTTPException(
                status_code=400,
                detail="Email already registered",
            )

    if "state_id" in update_data:
        state = (
            db.query(MasterState)
            .filter(
                MasterState.id
                == update_data["state_id"],
                MasterState.is_active.is_(True),
            )
            .first()
        )

        if not state:
            raise HTTPException(
                status_code=400,
                detail="Invalid state",
            )

    if "branch_id" in update_data:
        branch = (
            db.query(MasterBranch)
            .filter(
                MasterBranch.id
                == update_data["branch_id"],
                MasterBranch.is_active.is_(True),
            )
            .first()
        )

        if not branch:
            raise HTTPException(
                status_code=400,
                detail="Invalid branch",
            )

        selected_state_id = update_data.get(
            "state_id",
            investor.state_id,
        )

        if branch.state_id != selected_state_id:
            raise HTTPException(
                status_code=400,
                detail="Selected branch does not belong to selected state",
            )

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
            setattr(user, field, value)
        elif field in investor_fields:
            setattr(investor, field, value)

    db.commit()
    db.refresh(user)
    db.refresh(investor)

    return get_investor_profile(
        db,
        user_id,
    )