from typing import Any, Dict, List, Optional

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models.generated_models import TnInvestorRegistration


def _rows(result) -> List[Dict[str, Any]]:
    return [dict(row._mapping) for row in result]


def _row(result) -> Optional[Dict[str, Any]]:
    row = result.first()
    return dict(row._mapping) if row else None


def _pick(data: Dict[str, Any], *keys):
    for key in keys:
        if key in data:
            value = data.get(key)
            if value is not None and value != "":
                return value

    lowered = {
        str(key).lower(): value
        for key, value in data.items()
    }

    for key in keys:
        value = lowered.get(str(key).lower())
        if value is not None and value != "":
            return value

    return None


def _load_registration_map(db: Session):
    registrations = (
        db.query(TnInvestorRegistration)
        .all()
    )

    by_id = {}
    by_investor_id = {}
    by_user_id = {}

    for registration in registrations:
        by_id[int(registration.id)] = registration

        if registration.investor_id:
            by_investor_id[
                str(registration.investor_id).upper()
            ] = registration

        if registration.user_id is not None:
            by_user_id[
                int(registration.user_id)
            ] = registration

    return (
        by_id,
        by_investor_id,
        by_user_id,
    )


def _find_registration(
    db: Session,
    investor_id: str,
):
    investor_id = str(investor_id).strip()

    if not investor_id:
        return None

    by_id, by_investor_id, by_user_id = (
        _load_registration_map(db)
    )

    registration = None

    if investor_id.upper() in by_investor_id:
        registration = by_investor_id[
            investor_id.upper()
        ]

    if registration is None:
        try:
            numeric_id = int(investor_id)

            registration = by_user_id.get(
                numeric_id
            )

            if registration is None:
                registration = by_id.get(
                    numeric_id
                )

        except (TypeError, ValueError):
            pass

    return registration


def _enrich_investor_rows(
    db: Session,
    rows: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    by_id, by_investor_id, by_user_id = (
        _load_registration_map(db)
    )

    enriched = []

    for row in rows:
        item = dict(row)

        registration_id = _pick(
            item,
            "investor_registration_id",
            "registration_id",
            "investorRegistrationId",
            "id",
        )

        investor_id = _pick(
            item,
            "investor_id",
            "investorId",
            "login_id",
        )

        user_id = _pick(
            item,
            "user_id",
            "userId",
        )

        branch_id = _pick(
            item,
            "branch_id",
            "branchId",
        )

        registration = None

        if registration_id is not None:
            try:
                registration = by_id.get(
                    int(registration_id)
                )
            except (TypeError, ValueError):
                registration = None

        if registration is None and investor_id:
            registration = by_investor_id.get(
                str(investor_id).upper()
            )

        if registration is None and user_id is not None:
            try:
                registration = by_user_id.get(
                    int(user_id)
                )
            except (TypeError, ValueError):
                registration = None

        if registration:
            registration_id = registration.id
            investor_id = registration.investor_id
            user_id = registration.user_id

            if registration.branch_id is not None:
                branch_id = registration.branch_id

        if registration_id is not None:
            try:
                item[
                    "investor_registration_id"
                ] = int(registration_id)

                item[
                    "registration_id"
                ] = int(registration_id)

                item[
                    "investorRegistrationId"
                ] = int(registration_id)

            except (TypeError, ValueError):
                pass

        if investor_id:
            item["investor_id"] = str(
                investor_id
            )

            item["investorId"] = str(
                investor_id
            )

        if user_id is not None:
            try:
                item["user_id"] = int(
                    user_id
                )

                item["userId"] = int(
                    user_id
                )

            except (TypeError, ValueError):
                pass

        if branch_id is not None:
            try:
                item["branch_id"] = int(
                    branch_id
                )

                item["branchId"] = int(
                    branch_id
                )

            except (TypeError, ValueError):
                pass

        if registration:
            item[
                "_approval_investor_id"
            ] = str(
                registration.investor_id
            )

            item[
                "_registration_user_id"
            ] = (
                int(registration.user_id)
                if registration.user_id is not None
                else None
            )

            item[
                "_registration_id"
            ] = int(registration.id)

        enriched.append(item)

    return enriched

def get_investor_management(
    db: Session,
    status_name: Optional[str] = None,
    kyc_status_name: Optional[str] = None,
    search_text: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    current_user=None,
    branch_id: Optional[int] = None,
):
    result = db.execute(
        text(
            """
            SELECT *
            FROM public.fn_get_investor_management(
                :p_status_name,
                :p_kyc_status_name,
                :p_search_text,
                :p_limit,
                :p_offset,
                :p_branch_id
            )
            """
        ),
        {
            "p_status_name": status_name,
            "p_kyc_status_name": kyc_status_name,
            "p_search_text": search_text,
            "p_limit": limit,
            "p_offset": offset,
            "p_branch_id": branch_id,
        },
    )

    data = _rows(result)

    data = _enrich_investor_rows(
        db=db,
        rows=data,
    )

    return {
        "success": True,
        "data": data,
        "total": len(data),
    }

def get_investor_details(
    db: Session,
    investor_registration_id: int,
    branch_id: Optional[int] = None,
):
    registration = (
        db.query(TnInvestorRegistration)
        .filter(
            TnInvestorRegistration.id
            == investor_registration_id
        )
        .first()
    )

    if not registration:
        raise HTTPException(
            status_code=404,
            detail="Investor not found",
        )

    if (
        branch_id is not None
        and registration.branch_id is not None
        and int(registration.branch_id) != int(branch_id)
    ):
        raise HTTPException(
            status_code=403,
            detail="Investor does not belong to this branch",
        )

    result = db.execute(
        text(
            """
            SELECT *
            FROM fn_admin_get_investor_details(
                :p_investor_registration_id
            )
            """
        ),
        {
            "p_investor_registration_id":
                investor_registration_id,
        },
    )

    data = _row(result)

    if not data:
        raise HTTPException(
            status_code=404,
            detail="Investor details not found",
        )

    if registration:
        data[
            "investor_registration_id"
        ] = registration.id

        data[
            "registration_id"
        ] = registration.id

        data[
            "investor_id"
        ] = registration.investor_id

        data[
            "user_id"
        ] = registration.user_id

        data[
            "branch_id"
        ] = registration.branch_id

    return {
        "success": True,
        "data": data,
    }

def approve_investor_kyc(
    db: Session,
    investor_id: str,
    branch_id: int,
    approved_by: int,
    remarks: Optional[str] = None,
):
    investor_id = str(investor_id).strip()

    if not investor_id:
        raise HTTPException(
            status_code=400,
            detail="Investor ID is required.",
        )

    if not branch_id:
        raise HTTPException(
            status_code=400,
            detail="Branch ID is required.",
        )

    registration = _find_registration(
        db=db,
        investor_id=investor_id,
    )

    if registration is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "Investor registration not found "
                f"for ID: {investor_id}"
            ),
        )

    actual_investor_id = registration.investor_id

    actual_branch_id = (
        registration.branch_id
        if registration.branch_id is not None
        else branch_id
    )

    if not actual_investor_id:
        raise HTTPException(
            status_code=400,
            detail=(
                "Investor ID is missing "
                "in investor registration."
            ),
        )

    if not actual_branch_id:
        raise HTTPException(
            status_code=400,
            detail="Branch ID is missing.",
        )

    try:
        result = db.execute(
            text(
                """
                SELECT *
                FROM fn_approve_investor_kyc(
                    :p_investor_id,
                    :p_branch_id,
                    :p_approved_by,
                    :p_remarks
                )
                """
            ),
            {
                "p_investor_id": str(actual_investor_id),
                "p_branch_id": int(actual_branch_id),
                "p_approved_by": int(approved_by),
                "p_remarks": remarks,
            },
        )

        data = _row(result)

        if not data:
            db.rollback()

            raise HTTPException(
                status_code=500,
                detail=(
                    "No response received from "
                    "investor KYC approval function."
                ),
            )

        function_status = str(
            _pick(
                data,
                "o_status",
                "status",
            )
            or ""
        ).strip().upper()

        function_message = str(
            _pick(
                data,
                "o_message",
                "message",
            )
            or ""
        ).strip()

        success_message = function_message.lower()

        approval_succeeded = (
            function_status == "SUCCESS"
            or (
                "kyc approved successfully"
                in success_message
            )
            or (
                "approved successfully"
                in success_message
            )
            or (
                "now active"
                in success_message
            )
        )

        if not approval_succeeded:
            db.rollback()

            raise HTTPException(
                status_code=400,
                detail=(
                    function_message
                    or "Investor KYC approval failed."
                ),
            )

        db.commit()

        return {
            "success": True,
            "message": (
                function_message
                or "Investor KYC approved successfully."
            ),
            "data": {
                **data,
                "investor_registration_id": int(
                    registration.id
                ),
                "registration_id": int(
                    registration.id
                ),
                "investor_id": str(
                    registration.investor_id
                ),
                "user_id": (
                    int(registration.user_id)
                    if registration.user_id is not None
                    else None
                ),
                "branch_id": (
                    int(registration.branch_id)
                    if registration.branch_id is not None
                    else int(actual_branch_id)
                ),
            },
        }

    except HTTPException:
        raise

    except Exception as exc:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )
def reject_investor_kyc(
    db: Session,
    investor_id: str,
    rejection_reason: str,
    rejected_by: int,
    remarks: Optional[str] = None,
    branch_id: Optional[int] = None,
):
    investor_id = str(
        investor_id
    ).strip()

    if not investor_id:
        raise HTTPException(
            status_code=400,
            detail="Investor ID is required.",
        )

    registration = _find_registration(
        db=db,
        investor_id=investor_id,
    )

    if registration is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "Investor registration not found "
                f"for ID: {investor_id}"
            ),
        )

    if (
        branch_id is not None
        and registration.branch_id is not None
        and int(registration.branch_id) != int(branch_id)
    ):
        raise HTTPException(
            status_code=403,
            detail="Investor does not belong to this branch",
        )

    actual_investor_id = (
        registration.investor_id
    )

    if not actual_investor_id:
        raise HTTPException(
            status_code=400,
            detail=(
                "Investor ID is missing "
                "in investor registration."
            ),
        )

    try:
        result = db.execute(
            text(
                """
                SELECT *
                FROM fn_reject_investor_kyc(
                    :p_investor_id,
                    :p_rejection_reason,
                    :p_rejected_by,
                    :p_remarks
                )
                """
            ),
            {
                "p_investor_id":
                    str(actual_investor_id),
                "p_rejection_reason":
                    rejection_reason,
                "p_rejected_by":
                    int(rejected_by),
                "p_remarks":
                    remarks,
            },
        )

        data = _row(result)

        if not data:
            db.rollback()

            raise HTTPException(
                status_code=500,
                detail=(
                    "No response received from "
                    "investor rejection function."
                ),
            )

        function_status = str(
            _pick(
                data,
                "o_status",
                "status",
            )
            or ""
        ).upper()

        function_message = _pick(
            data,
            "o_message",
            "message",
        )

        if function_status != "SUCCESS":
            db.rollback()

            raise HTTPException(
                status_code=400,
                detail=(
                    function_message
                    or "Investor rejection failed."
                ),
            )

        db.commit()

        return {
            "success": True,
            "message": (
                function_message
                or "Investor rejected successfully."
            ),
            "data": {
                **data,
                "investor_registration_id":
                    registration.id,
                "registration_id":
                    registration.id,
                "investor_id":
                    registration.investor_id,
                "user_id":
                    registration.user_id,
                "branch_id":
                    registration.branch_id,
            },
        }

    except HTTPException:
        raise

    except Exception as exc:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )