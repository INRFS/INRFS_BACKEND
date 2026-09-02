from datetime import datetime
from typing import Optional

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

from app.services.email_service import send_welcome_email
from app.services.email_otp_service import (
    is_email_verified,
    clear_email_otp,
)


def get_role(
    db: Session,
    role_name: str,
):

    normalized_role_name = (
        role_name
        .replace(" ", "")
        .strip()
        .upper()
    )

    role = (
        db.query(MasterRole)
        .filter(
            func.replace(
                func.upper(
                    MasterRole.role_name
                ),
                " ",
                "",
            )
            == normalized_role_name,
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
            func.upper(
                MasterUserStatus.status_name
            )
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
    email: Optional[str] = None,
    username: Optional[str] = None,
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
                func.lower(
                    TnApplicationUser.email
                )
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
                func.lower(
                    TnApplicationUser.username
                )
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

        if data.email:
            if not is_email_verified(
                db=db,
                email=str(data.email),
            ):
                raise HTTPException(
                    status_code=400,
                    detail="Please verify your email with OTP before registration.",
                )

        role = get_role(
            db,
            "INVESTOR",
        )

        user_status = get_active_user_status(
            db
        )

        kyc_status = get_pending_kyc_status(
            db
        )

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
            password=hash_password(
                data.password
            ),
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

        if data.email:
            clear_email_otp(
                db=db,
                email=str(data.email),
            )
            db.commit()

        send_welcome_email(
            email=user.email,
            name=user.full_name,
            username=user.username,
            password=data.password,
            role=role.role_name,
        )

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
    created_by: Optional[int] = None,
    branch_id: Optional[int] = None,
):

    try:

        username = data.username.strip()

        normalized_role_name = (
            role_name
            .replace(" ", "")
            .strip()
            .upper()
        )

        check_existing_user(
            db=db,
            mobile=data.mobile,
            email=data.email,
            username=username,
        )

        role = get_role(
            db,
            role_name,
        )

        user_status = get_active_user_status(
            db
        )

        if normalized_role_name == "ADMIN":

            if branch_id is None:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Branch is required "
                        "for Admin"
                    ),
                )

            branch_id = int(branch_id)

        elif normalized_role_name == "SUPERADMIN":

            branch_id = (
                int(branch_id)
                if branch_id is not None
                else None
            )

        user = TnApplicationUser(
            role_id=role.id,
            user_status_id=user_status.id,
            full_name=data.full_name.strip(),
            mobile=data.mobile.strip(),
            email=data.email,
            username=username,
            password=hash_password(
                data.password
            ),
            branch_id=branch_id,
            failed_login_attempts=0,
            is_active=True,
            created_by=created_by,
            created_date=datetime.utcnow(),
        )

        db.add(user)
        db.flush()

        if (
            created_by is None
            and normalized_role_name == "SUPERADMIN"
        ):
            user.created_by = user.id
            db.flush()

        db.commit()

        db.refresh(user)

        send_welcome_email(
            email=user.email,
            name=user.full_name,
            username=user.username,
            password=data.password,
            role=role.role_name,
        )

        return user

    except HTTPException:
        db.rollback()
        raise

    except Exception as exc:

        db.rollback()

        print(
            "STAFF REGISTRATION ERROR:",
            repr(exc),
        )

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
    ip_address: Optional[str] = None,
):

    try:

        login_history = TnLoginHistory(
            user_id=user.id,
            login_date=datetime.utcnow(),
            login_type=login_type,
            ip_address=ip_address,
            created_by=user.id,
            created_date=datetime.utcnow(),
        )

        db.add(login_history)
        db.flush()

        return True

    except Exception as exc:

        print(
            "LOGIN HISTORY ERROR:",
            repr(exc),
        )

        db.rollback()

        return False


def investor_login(
    db: Session,
    investor_id: str,
    password: str,
    ip_address: Optional[str] = None,
):

    investor_id = investor_id.strip()

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

    if (
        user.role.role_name.upper()
        != "INVESTOR"
    ):
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
            detail=(
                "Investor approval status "
                "is not configured"
            ),
        )

    kyc_status = (
        investor.kyc_status.kyc_status_name
        or ""
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
            status_code=500,
            detail="Password is not configured",
        )

    try:

        password_valid = verify_password(
            password,
            user.password,
        )

    except Exception as exc:

        print(
            "INVESTOR PASSWORD ERROR:",
            repr(exc),
        )

        raise HTTPException(
            status_code=500,
            detail="Password verification failed",
        )

    if not password_valid:

        user.failed_login_attempts = (
            (user.failed_login_attempts or 0)
            + 1
        )

        db.commit()

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid investor ID or password",
        )

    user.failed_login_attempts = 0
    user.last_login_date = datetime.utcnow()

    db.commit()

    try:

        create_login_history(
            db=db,
            user=user,
            login_type="INVESTOR",
            ip_address=ip_address,
        )

        db.commit()

    except Exception:

        db.rollback()

        user.failed_login_attempts = 0
        user.last_login_date = datetime.utcnow()

        db.commit()

    token = create_access_token(
        user_id=user.id,
        login_id=investor.investor_id,
        role="INVESTOR",
        branch_id=investor.branch_id,
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user.id,
        "login_id": investor.investor_id,
        "full_name": user.full_name,
        "role": "INVESTOR",
        "branch_id": investor.branch_id,
    }


def admin_login(
    db: Session,
    username: str,
    password: str,
    ip_address: Optional[str] = None,
):

    username = username.strip()

    user = (
        db.query(TnApplicationUser)
        .join(
            MasterRole,
            TnApplicationUser.role_id
            == MasterRole.id,
        )
        .filter(
            func.lower(
                TnApplicationUser.username
            )
            == username.lower(),
            func.replace(
                func.upper(
                    func.trim(
                        MasterRole.role_name
                    )
                ),
                " ",
                "",
            )
            == "ADMIN",
        )
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=401,
            detail=(
                "Invalid admin username "
                "or password"
            ),
        )

    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="Admin account is inactive",
        )

    if not user.password:
        raise HTTPException(
            status_code=500,
            detail="Password is not configured",
        )

    password_valid = verify_password(
        password,
        user.password,
    )

    if not password_valid:

        user.failed_login_attempts = (
            (user.failed_login_attempts or 0)
            + 1
        )

        db.commit()

        raise HTTPException(
            status_code=401,
            detail=(
                "Invalid admin username "
                "or password"
            ),
        )

    branch_id = getattr(
        user,
        "branch_id",
        None,
    )

    if branch_id is None:
        raise HTTPException(
            status_code=403,
            detail=(
                "Admin account is not assigned "
                "to a branch"
            ),
        )

    user.failed_login_attempts = 0
    user.last_login_date = datetime.utcnow()

    db.commit()

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
        branch_id=branch_id,
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user.id,
        "login_id": user.username,
        "full_name": user.full_name,
        "role": "ADMIN",
        "branch_id": branch_id,
    }


def superadmin_login(
    db: Session,
    username: str,
    password: str,
    ip_address: Optional[str] = None,
):

    username = username.strip()

    if not username:
        raise HTTPException(
            status_code=400,
            detail="Username is required",
        )

    if not password:
        raise HTTPException(
            status_code=400,
            detail="Password is required",
        )

    user = (
        db.query(TnApplicationUser)
        .join(
            MasterRole,
            TnApplicationUser.role_id
            == MasterRole.id,
        )
        .filter(
            func.lower(
                TnApplicationUser.username
            )
            == username.lower(),
            func.replace(
                func.upper(
                    func.trim(
                        MasterRole.role_name
                    )
                ),
                " ",
                "",
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

    if not user.role:
        raise HTTPException(
            status_code=500,
            detail=(
                "Superadmin role is not configured"
            ),
        )

    normalized_role = (
        (user.role.role_name or "")
        .replace(" ", "")
        .strip()
        .upper()
    )

    if normalized_role != "SUPERADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "This account is not a "
                "Super Admin account"
            ),
        )

    if user.is_active is not True:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superadmin account is inactive",
        )

    if not user.password:
        raise HTTPException(
            status_code=500,
            detail="Password is not configured",
        )

    password_valid = verify_password(
        password,
        user.password,
    )

    if not password_valid:

        user.failed_login_attempts = (
            (user.failed_login_attempts or 0)
            + 1
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

    db.commit()

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
        branch_id=None,
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user.id,
        "login_id": user.username,
        "full_name": user.full_name,
        "role": "SUPERADMIN",
        "branch_id": None,
    }