from typing import Optional

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
)

from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)

from pydantic import BaseModel

from sqlalchemy.orm import Session

from app.database import get_db

from app.utils.auth_utils import (
    decode_access_token,
)

from app.services.superadmin.payment_service import (
    get_payment_queue,
    get_payment_details,
    approve_payment,
    mark_payment_paid,
    reject_payment,
    get_pending_tenure_extensions,
    get_all_tenure_extensions_for_superadmin,
    get_tenure_extension_details,
    approve_tenure_extension,
    reject_tenure_extension,
    mark_tenure_extension_paid,
)

from app.services.superadmin.payment_service import (
    get_superadmin_preclose_requests,
    get_superadmin_preclose_request_details,
    get_superadmin_tenure_timeout_settlements,
    get_superadmin_tenure_timeout_settlement_details,
)


router = APIRouter(
    tags=["Super Admin"],
)


security = HTTPBearer()



def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(
        security
    ),
):
    token = credentials.credentials

    payload = decode_access_token(token)

    if not payload:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token.",
        )

    return payload


def get_user_id(
    current_user: dict,
) -> int:

    user_id = (
        current_user.get("user_id")
        or current_user.get("id")
        or current_user.get("sub")
    )

    if user_id is None:
        raise HTTPException(
            status_code=401,
            detail="User ID not found in token.",
        )

    try:
        return int(user_id)

    except (
        TypeError,
        ValueError,
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid user ID.",
        )


def get_role_name(
    current_user: dict,
) -> str:

    role = current_user.get("role")

    if isinstance(role, dict):
        role = (
            role.get("role_name")
            or role.get("name")
            or role.get("role")
        )

    if role is None:
        role = current_user.get(
            "role_name",
            "",
        )

    return str(
        role
    ).strip().upper()


def require_superadmin(
    current_user: dict = Depends(
        get_current_user
    ),
):
    role = get_role_name(
        current_user
    )

    allowed_roles = {
        "SUPERADMIN",
        "SUPER ADMIN",
        "SUPER_ADMIN",
    }

    if role not in allowed_roles:
        raise HTTPException(
            status_code=403,
            detail="Super Admin access required.",
        )

    return current_user



class PaymentAction(BaseModel):
    source_id: int
    payment_type: str


class RejectPaymentAction(BaseModel):
    source_id: int
    payment_type: str
    rejection_reason: str


class TenureApprovalAction(BaseModel):
    remarks: Optional[str] = None


class TenureRejectAction(BaseModel):
    remarks: str



@router.get(
    "/superadmin/payments"
)
def payment_queue(
    payment_type: Optional[str] = Query(
        default="All"
    ),
    limit: int = Query(
        default=100,
        ge=1,
        le=500,
    ),
    offset: int = Query(
        default=0,
        ge=0,
    ),
    db: Session = Depends(get_db),
    current_user: dict = Depends(
        require_superadmin
    ),
):
    try:

        payments = get_payment_queue(
            db=db,
            payment_type=payment_type or "All",
            limit=limit,
            offset=offset,
        )

        return {
            "success": True,
            "data": payments,
            "count": len(payments),
        }

    except Exception as exc:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )



@router.get(
    "/superadmin/tenure-extensions"
)
def get_superadmin_tenure_extensions_route(
    branch_id: Optional[int] = Query(
        default=None
    ),
    limit: int = Query(
        default=100,
        ge=1,
        le=500,
    ),
    offset: int = Query(
        default=0,
        ge=0,
    ),
    db: Session = Depends(get_db),
    current_user: dict = Depends(
        require_superadmin
    ),
):
    try:

        rows = get_all_tenure_extensions_for_superadmin(
            db=db,
            branch_id=branch_id,
            limit=limit,
            offset=offset,
        )

        return {
            "success": True,
            "data": rows,
            "count": len(rows),
        }

    except Exception as exc:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )



@router.get(
    "/superadmin/payments/{source_id}"
)
def payment_details(
    source_id: int,
    payment_type: str = Query(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(
        require_superadmin
    ),
):
    try:

        payment = get_payment_details(
            db=db,
            source_id=source_id,
            payment_type=payment_type,
        )

        if not payment:
            raise HTTPException(
                status_code=404,
                detail="Payment not found.",
            )

        return {
            "success": True,
            "data": payment,
        }

    except HTTPException:
        raise

    except Exception as exc:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )



@router.post(
    "/superadmin/payments/approve"
)
def approve_payment_route(
    payload: PaymentAction,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_superadmin),
):
    try:
        user_id = get_user_id(current_user)

        result = approve_payment(
            db=db,
            source_id=payload.source_id,
            payment_type=payload.payment_type,
            approved_by=user_id,
        )

        return {
            "success": True,
            "message": "Payment approved successfully.",
            "data": result,
        }

    except HTTPException:
        db.rollback()
        raise

    except ValueError as exc:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )


@router.post(
    "/superadmin/payments/mark-paid"
)
def mark_payment_paid_route(
    payload: PaymentAction,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_superadmin),
):
    try:
        user_id = get_user_id(current_user)

        result = mark_payment_paid(
            db=db,
            source_id=payload.source_id,
            payment_type=payload.payment_type,
            paid_by=user_id,
        )

        return {
            "success": True,
            "message": "Payment marked as paid successfully.",
            "data": result,
        }

    except HTTPException:
        db.rollback()
        raise

    except ValueError as exc:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )


@router.post(
    "/superadmin/payments/reject"
)
def reject_payment_route(
    payload: RejectPaymentAction,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_superadmin),
):
    try:
        reason = (payload.rejection_reason or "").strip()

        if not reason:
            raise HTTPException(
                status_code=400,
                detail="Rejection reason is required.",
            )

        user_id = get_user_id(current_user)

        result = reject_payment(
            db=db,
            source_id=payload.source_id,
            payment_type=payload.payment_type,
            rejected_by=user_id,
            rejection_reason=reason,
        )

        return {
            "success": True,
            "message": "Payment rejected successfully.",
            "data": result,
        }

    except HTTPException:
        db.rollback()
        raise

    except ValueError as exc:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )


@router.get(
    "/superadmin/tenure-extensions/{request_id}"
)
def get_tenure_extension_details_route(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(
        require_superadmin
    ),
):
    try:

        row = get_tenure_extension_details(
            db=db,
            request_id=request_id,
        )

        if not row:
            raise HTTPException(
                status_code=404,
                detail="Tenure extension request not found.",
            )

        return {
            "success": True,
            "data": row,
        }

    except HTTPException:
        raise

    except Exception as exc:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )



@router.put(
    "/superadmin/tenure-extensions/{request_id}/approve"
)
def approve_tenure_extension_route(
    request_id: int,
    payload: TenureApprovalAction,
    db: Session = Depends(get_db),
    current_user: dict = Depends(
        require_superadmin
    ),
):
    try:

        user_id = get_user_id(
            current_user
        )

        result = approve_tenure_extension(
            db=db,
            request_id=request_id,
            approved_by=user_id,
            remarks=payload.remarks,
        )

        if not result:
            raise HTTPException(
                status_code=500,
                detail="No response from tenure approval function.",
            )

        if result.get("success") is False:
            raise HTTPException(
                status_code=400,
                detail=result.get(
                    "message",
                    "Unable to approve tenure extension.",
                ),
            )

        return {
            "success": True,
            "message": result.get(
                "message",
                "Tenure extension approved successfully.",
            ),
            "data": result,
        }

    except HTTPException:
        db.rollback()
        raise

    except ValueError as exc:

        db.rollback()

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except Exception as exc:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )



@router.put(
    "/superadmin/tenure-extensions/{request_id}/mark-paid"
)
def mark_tenure_extension_paid_route(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(
        require_superadmin
    ),
):
    try:

        user_id = get_user_id(
            current_user
        )

        result = mark_tenure_extension_paid(
            db=db,
            request_id=request_id,
            paid_by=user_id,
        )

        return {
            "success": True,
            "message": "Tenure extension payment marked as paid successfully.",
            "data": result,
        }

    except ValueError as exc:

        db.rollback()

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except Exception as exc:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )



@router.put(
    "/superadmin/tenure-extensions/{request_id}/reject"
)
def reject_tenure_extension_route(
    request_id: int,
    payload: TenureRejectAction,
    db: Session = Depends(get_db),
    current_user: dict = Depends(
        require_superadmin
    ),
):
    try:

        remarks = (
            payload.remarks or ""
        ).strip()

        if not remarks:
            raise HTTPException(
                status_code=400,
                detail="Rejection reason is required.",
            )

        user_id = get_user_id(
            current_user
        )

        result = reject_tenure_extension(
            db=db,
            request_id=request_id,
            rejected_by=user_id,
            remarks=remarks,
        )

        if not result:
            raise HTTPException(
                status_code=500,
                detail="No response from tenure rejection function.",
            )

        if result.get("success") is False:
            raise HTTPException(
                status_code=400,
                detail=result.get(
                    "message",
                    "Unable to reject tenure extension.",
                ),
            )

        return {
            "success": True,
            "message": result.get(
                "message",
                "Tenure extension request rejected successfully.",
            ),
            "data": result,
        }

    except HTTPException:
        db.rollback()
        raise

    except ValueError as exc:

        db.rollback()

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except Exception as exc:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )

@router.get("/superadmin/settlements/preclose")
def get_superadmin_preclose_settlements_route(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_superadmin),
):
    try:
        rows = get_superadmin_preclose_requests(
            db=db,
            limit=limit,
            offset=offset,
        )
        return {
            "success": True,
            "data": rows,
            "count": len(rows),
        }
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )


@router.get("/superadmin/settlements/preclose/{request_id}")
def get_superadmin_preclose_details_route(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_superadmin),
):
    try:
        row = get_superadmin_preclose_request_details(
            db=db,
            request_id=request_id,
        )
        if not row:
            raise HTTPException(
                status_code=404,
                detail="Pre-close request not found.",
            )
        return {
            "success": True,
            "data": row,
        }
    except HTTPException:
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )


@router.get("/superadmin/settlements/tenure-timeout")
def get_superadmin_tenure_timeout_settlements_route(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_superadmin),
):
    try:
        rows = get_superadmin_tenure_timeout_settlements(
            db=db,
            limit=limit,
            offset=offset,
        )
        return {
            "success": True,
            "data": rows,
            "count": len(rows),
        }
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )


@router.get("/superadmin/settlements/tenure-timeout/{settlement_id}")
def get_superadmin_tenure_timeout_details_route(
    settlement_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_superadmin),
):
    try:
        row = get_superadmin_tenure_timeout_settlement_details(
            db=db,
            settlement_id=settlement_id,
        )
        if not row:
            raise HTTPException(
                status_code=404,
                detail="Tenure timeout settlement not found.",
            )
        return {
            "success": True,
            "data": row,
        }
    except HTTPException:
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )
