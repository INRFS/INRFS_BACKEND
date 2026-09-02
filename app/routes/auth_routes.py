from fastapi import (
    APIRouter,
    Depends,
    Request,
    status,
)
from sqlalchemy.orm import Session

from app.database import get_db

from app.dependencies import (
    get_current_user,
    require_superadmin,
)

from app.schemas.auth_schema import (
    InvestorRegisterRequest,
    InvestorLoginRequest,
    StaffRegisterRequest,
    AdminLoginRequest,
    SuperAdminLoginRequest,
    SendEmailOtpRequest,
    VerifyEmailOtpRequest,
    TokenResponse,
    UserResponse,
)

from app.services.auth_service import (
    register_investor,
    register_staff,
    investor_login,
    admin_login,
    superadmin_login,
)

from app.services.email_otp_service import (
    send_email_otp,
    verify_email_otp,
)


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/email/send-otp",
)
def send_email_otp_api(
    data: SendEmailOtpRequest,
    db: Session = Depends(get_db),
):
    return send_email_otp(
        db=db,
        email=str(data.email),
        name=data.name,
    )


@router.post(
    "/email/verify-otp",
)
def verify_email_otp_api(
    data: VerifyEmailOtpRequest,
    db: Session = Depends(get_db),
):
    return verify_email_otp(
        db=db,
        email=str(data.email),
        otp=data.otp,
    )


@router.post(
    "/investor/register",
    status_code=status.HTTP_201_CREATED,
)
def investor_register(
    data: InvestorRegisterRequest,
    db: Session = Depends(get_db),
):

    user, investor = register_investor(
        db=db,
        data=data,
    )

    return {
        "success": True,
        "message": "Investor registered successfully",
        "investor_id": investor.investor_id,
        "user_id": user.id,
        "full_name": user.full_name,
        "branch_id": investor.branch_id,
        "kyc_status": (
            investor.kyc_status.kyc_status_name
            if investor.kyc_status
            else None
        ),
    }


@router.post(
    "/investor/login",
    response_model=TokenResponse,
)
def investor_login_api(
    data: InvestorLoginRequest,
    request: Request,
    db: Session = Depends(get_db),
):

    ip_address = (
        request.client.host
        if request.client
        else None
    )

    return investor_login(
        db=db,
        investor_id=data.investor_id,
        password=data.password,
        ip_address=ip_address,
    )


@router.post(
    "/admin/register",
    status_code=status.HTTP_201_CREATED,
)
def admin_register(
    data: StaffRegisterRequest,
    current_user=Depends(
        require_superadmin
    ),
    db: Session = Depends(get_db),
):

    user = register_staff(
        db=db,
        data=data,
        role_name="ADMIN",
        created_by=current_user.id,
        branch_id=data.branch_id,
    )

    return {
        "success": True,
        "message": "Admin registered successfully",
        "user_id": user.id,
        "username": user.username,
        "full_name": user.full_name,
        "branch_id": user.branch_id,
    }


@router.post(
    "/superadmin/register",
    status_code=status.HTTP_201_CREATED,
)
def superadmin_register(
    data: StaffRegisterRequest,
    current_user=Depends(
        require_superadmin
    ),
    db: Session = Depends(get_db),
):

    user = register_staff(
        db=db,
        data=data,
        role_name="SUPERADMIN",
        created_by=current_user.id,
        branch_id=data.branch_id,
    )

    return {
        "success": True,
        "message": "Superadmin registered successfully",
        "user_id": user.id,
        "username": user.username,
        "full_name": user.full_name,
        "branch_id": user.branch_id,
    }


@router.post(
    "/admin/login",
    response_model=TokenResponse,
)
def admin_login_api(
    data: AdminLoginRequest,
    request: Request,
    db: Session = Depends(get_db),
):

    ip_address = (
        request.client.host
        if request.client
        else None
    )

    return admin_login(
        db=db,
        username=data.username,
        password=data.password,
        ip_address=ip_address,
    )


@router.post(
    "/superadmin/login",
    response_model=TokenResponse,
)
def superadmin_login_api(
    data: SuperAdminLoginRequest,
    request: Request,
    db: Session = Depends(get_db),
):

    ip_address = (
        request.client.host
        if request.client
        else None
    )

    return superadmin_login(
        db=db,
        username=data.username,
        password=data.password,
        ip_address=ip_address,
    )


@router.get(
    "/me",
    response_model=UserResponse,
)
def get_current_user_details(
    current_user=Depends(
        get_current_user
    ),
):

    role_name = (
        current_user.role.role_name
        if current_user.role
        else ""
    )

    branch_id = getattr(
        current_user,
        "branch_id",
        None,
    )

    if role_name.upper() == "INVESTOR":

        investor = (
            current_user.tn_investor_registration_user
        )

        login_id = (
            investor.investor_id
            if investor
            else current_user.username
        )

        if investor and investor.branch_id:
            branch_id = investor.branch_id

    else:
        login_id = current_user.username

    return {
        "id": current_user.id,
        "login_id": login_id,
        "full_name": current_user.full_name,
        "mobile": current_user.mobile,
        "email": current_user.email,
        "role": role_name,
        "is_active": bool(
            current_user.is_active
        ),
        "branch_id": branch_id,
    }