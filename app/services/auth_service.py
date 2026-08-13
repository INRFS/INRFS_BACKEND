from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.generated_models import (
    MasterKycStatus,
    MasterRole,
    MasterUserStatus,
    TnApplicationUser,
    TnInvestorRegistration,
    TnLoginHistory,
)

from app.schemas.auth_schema import (
    InvestorRegisterRequest,
    StaffRegisterRequest,
)

from app.utils.security import (
    hash_password,
    verify_password,
)

from app.utils.auth_utils import (
    create_access_token,
)


def get_role(
    db: Session,
    role_name: str,
):
    role = (
        db.query(MasterRole)
        .filter(
            func.upper(MasterRole.role_name)
            == role_name.upper(),
            MasterRole.is_active.is_(True),
        )
        .first()
    )

    if not role:
        raise HTTPException(
            status_code=500,
            detail=(
                f"Role '{role_name}' "
                "is not configured in master_role"
            ),
        )

    return role


def get_active_user_status(
    db: Session,
):
    user_status = (
        db.query(MasterUserStatus)
        .filter(
            func.upper(MasterUserStatus.status_name)
            == "ACTIVE",
            MasterUserStatus.is_active.is_(True),
        )
        .first()
    )

    if not user_status:
        raise HTTPException(
            status_code=500,
            detail=(
                "ACTIVE status is not configured "
                "in master_user_status"
            ),
        )

    return user_status


def get_pending_kyc_status(
    db: Session,
):
    kyc_status = (
        db.query(MasterKycStatus)
        .filter(
            func.upper(
                MasterKycStatus.kyc_status_name
            )
            == "PENDING",
            MasterKycStatus.is_active.is_(True),
        )
        .first()
    )

    if not kyc_status:
        raise HTTPException(
            status_code=500,
            detail=(
                "PENDING KYC status is not configured "
                "in master_kyc_status"
            ),
        )

    return kyc_status


def check_existing_user(
    db: Session,
    mobile: str,
    email: str | None = None,
    username: str | None = None,
):
    mobile_exists = (
        db.query(TnApplicationUser)
        .filter(
            TnApplicationUser.mobile == mobile
        )
        .first()
    )

    if mobile_exists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Mobile number already exists",
        )

    if email:
        email_exists = (
            db.query(TnApplicationUser)
            .filter(
                func.lower(TnApplicationUser.email)
                == email.lower()
            )
            .first()
        )

        if email_exists:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already exists",
            )

    if username:
        username_exists = (
            db.query(TnApplicationUser)
            .filter(
                func.lower(TnApplicationUser.username)
                == username.lower()
            )
            .first()
        )

        if username_exists:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already exists",
            )


def register_investor(
    db: Session,
    data: InvestorRegisterRequest,
):
    try:
        check_existing_user(
            db=db,
            mobile=data.mobile,
            email=data.email,
        )

        role = get_role(
            db,
            "INVESTOR",
        )

        user_status = get_active_user_status(db)

        kyc_status = get_pending_kyc_status(db)

        investor_exists = (
            db.query(TnInvestorRegistration)
            .filter(
                TnInvestorRegistration.aadhaar_number
                == data.aadhaar_number
            )
            .first()
        )

        if investor_exists:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Investor with this "
                    "Aadhaar already exists"
                ),
            )

        user = TnApplicationUser(
            role_id=role.id,
            user_status_id=user_status.id,
            full_name=data.full_name,
            mobile=data.mobile,
            email=data.email,
            username=None,
            password=hash_password(data.password),
            failed_login_attempts=0,
            is_active=True,
            created_date=datetime.utcnow(),
        )

        db.add(user)
        db.flush()

        investor = TnInvestorRegistration(
            user_id=user.id,
            date_of_birth=data.date_of_birth,
            aadhaar_number=data.aadhaar_number,
            address=data.address,
            city=data.city,
            state_id=data.state_id,
            pincode=data.pincode,
            branch_id=data.branch_id,
            kyc_status_id=kyc_status.id,
            investor_id=None,
            is_active=True,
            created_by=user.id,
            created_date=datetime.utcnow(),
        )

        db.add(investor)
        db.flush()

        investor.investor_id = (
            f"INV{investor.id:06d}"
        )

        user.username = investor.investor_id

        db.commit()

        db.refresh(user)
        db.refresh(investor)

        return user, investor

    except HTTPException:
        db.rollback()
        raise

    except Exception as exc:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=(
                "Investor registration failed: "
                f"{str(exc)}"
            ),
        )


def register_staff(
    db: Session,
    data: StaffRegisterRequest,
    role_name: str,
    created_by: int | None = None,
):
    try:
        check_existing_user(
            db=db,
            mobile=data.mobile,
            email=data.email,
            username=data.username,
        )

        role = get_role(
            db,
            role_name,
        )

        user_status = get_active_user_status(db)

        user = TnApplicationUser(
            role_id=role.id,
            user_status_id=user_status.id,
            full_name=data.full_name,
            mobile=data.mobile,
            email=data.email,
            username=data.username,
            password=hash_password(data.password),
            failed_login_attempts=0,
            is_active=True,
            created_by=created_by,
            created_date=datetime.utcnow(),
        )

        db.add(user)

        db.commit()

        db.refresh(user)

        return user

    except HTTPException:
        db.rollback()
        raise

    except Exception as exc:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=(
                "Staff registration failed: "
                f"{str(exc)}"
            ),
        )


def create_login_history(
    db: Session,
    user: TnApplicationUser,
    login_type: str,
    ip_address: str | None = None,
):
    login_history = TnLoginHistory(
        user_id=user.id,
        login_date=datetime.utcnow(),
        login_type=login_type,
        ip_address=ip_address,
        created_by=user.id,
        created_date=datetime.utcnow(),
    )

    db.add(login_history)


def investor_login(
    db: Session,
    investor_id: str,
    password: str,
    ip_address: str | None = None,
):
    investor = (
        db.query(TnInvestorRegistration)
        .filter(
            func.upper(
                TnInvestorRegistration.investor_id
            )
            == investor_id.upper()
        )
        .first()
    )

    if not investor:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid investor ID or password",
        )

    user = (
        db.query(TnApplicationUser)
        .filter(
            TnApplicationUser.id
            == investor.user_id
        )
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Investor account not found",
        )

    if not user.role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Investor role is not configured",
        )

    if user.role.role_name.upper() != "INVESTOR":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid investor account",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Investor account is inactive",
        )

    if not investor.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Investor registration is inactive",
        )

    if not investor.kyc_status:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Investor approval status is not configured",
        )

    kyc_status = (
        investor.kyc_status.kyc_status_name or ""
    ).strip().upper()

    if kyc_status not in (
        "APPROVED",
        "VERIFIED",
    ):
        if kyc_status == "PENDING":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "Your account is pending "
                    "admin approval."
                ),
            )

        if kyc_status == "REJECTED":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "Your investor application "
                    "has been rejected."
                ),
            )

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Your account is not approved "
                "for login."
            ),
        )

    if not user.password:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password is not configured",
        )

    try:
        password_valid = verify_password(
            password,
            user.password,
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password verification failed",
        )

    if not password_valid:
        user.failed_login_attempts = (
            (user.failed_login_attempts or 0) + 1
        )

        db.commit()

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid investor ID or password",
        )

    user.failed_login_attempts = 0
    user.last_login_date = datetime.utcnow()

    create_login_history(
        db=db,
        user=user,
        login_type="INVESTOR",
        ip_address=ip_address,
    )

    db.commit()

    token = create_access_token(
        user_id=user.id,
        login_id=investor.investor_id,
        role="INVESTOR",
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user.id,
        "login_id": investor.investor_id,
        "full_name": user.full_name,
        "role": "INVESTOR",
    }


def admin_login(
    db: Session,
    username: str,
    password: str,
    ip_address: str | None = None,
):
    user = (
        db.query(TnApplicationUser)
        .join(MasterRole)
        .filter(
            func.lower(
                TnApplicationUser.username
            )
            == username.lower(),
            func.upper(
                MasterRole.role_name
            )
            == "ADMIN",
        )
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin username or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin account is inactive",
        )

    if not user.password:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password is not configured",
        )

    try:
        password_valid = verify_password(
            password,
            user.password,
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password verification failed",
        )

    if not password_valid:
        user.failed_login_attempts = (
            (user.failed_login_attempts or 0) + 1
        )

        db.commit()

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin username or password",
        )

    user.failed_login_attempts = 0
    user.last_login_date = datetime.utcnow()

    create_login_history(
        db=db,
        user=user,
        login_type="ADMIN",
        ip_address=ip_address,
    )

    db.commit()

    token = create_access_token(
        user_id=user.id,
        login_id=user.username,
        role="ADMIN",
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user.id,
        "login_id": user.username,
        "full_name": user.full_name,
        "role": "ADMIN",
    }


def superadmin_login(
    db: Session,
    username: str,
    password: str,
    ip_address: str | None = None,
):
    user = (
        db.query(TnApplicationUser)
        .join(MasterRole)
        .filter(
            func.lower(
                TnApplicationUser.username
            )
            == username.lower(),
            func.upper(
                MasterRole.role_name
            )
            == "SUPERADMIN",
        )
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=(
                "Invalid superadmin "
                "username or password"
            ),
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superadmin account is inactive",
        )

    if not user.password:
        raise HTTPException(
            status_code=500,
            detail="Password is not configured",
        )

    try:
        password_valid = verify_password(
            password,
            user.password,
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password verification failed",
        )

    if not password_valid:
        user.failed_login_attempts = (
            (user.failed_login_attempts or 0) + 1
        )

        db.commit()

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=(
                "Invalid superadmin "
                "username or password"
            ),
        )

    user.failed_login_attempts = 0
    user.last_login_date = datetime.utcnow()

    create_login_history(
        db=db,
        user=user,
        login_type="SUPERADMIN",
        ip_address=ip_address,
    )

    db.commit()

    token = create_access_token(
        user_id=user.id,
        login_id=user.username,
        role="SUPERADMIN",
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user.id,
        "login_id": user.username,
        "full_name": user.full_name,
        "role": "SUPERADMIN",
    }