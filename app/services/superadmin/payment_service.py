from typing import Optional

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session




def _normalize_payment_type(payment_type: str) -> str:
    return " ".join(str(payment_type or "All").strip().lower().replace("_", " ").split())


def _get_status_id(
    db: Session,
    table_name: str,
    status_name: str,
):
    if table_name not in {
        "master_investor_request_status",
        "master_settlement_status",
    }:
        raise ValueError("Invalid status table.")

    result = db.execute(
        text(
            f"""
            SELECT id
            FROM public.{table_name}
            WHERE LOWER(TRIM(status_name)) = LOWER(TRIM(:p_status_name))
            LIMIT 1
            """
        ),
        {"p_status_name": status_name},
    ).mappings().first()

    if not result:
        raise HTTPException(
            status_code=400,
            detail=(
                f"'{status_name}' status is not configured "
                f"in {table_name}."
            ),
        )

    return result["id"]


def _normalize_display_status(value):
    value = str(value or "").strip().lower()

    if value in {"pending", "pending super admin", "awaiting approval"}:
        return "Pending"
    if value in {"approved", "active"}:
        return "Approved"
    if value in {"rejected", "reject"}:
        return "Rejected"
    if value == "paid":
        return "Paid"

    return str(value).strip().title() if value else "Pending"


def get_payment_queue(
    db: Session,
    payment_type: str = "All",
    limit: int = 100,
    offset: int = 0,
):
    normalized = _normalize_payment_type(payment_type)

    if normalized == "all":
        monthly = get_monthly_payment_queue(
            db=db,
            limit=limit,
            offset=offset,
        )

        tenure = get_superadmin_tenure_timeout_settlements(
            db=db,
            limit=limit,
            offset=offset,
        )

        preclose = get_superadmin_preclose_requests(
            db=db,
            limit=limit,
            offset=offset,
        )

        return monthly + tenure + preclose

    if normalized in {
        "pre-close settlement",
        "preclose settlement",
        "pre-close",
        "preclose",
    }:
        return get_superadmin_preclose_requests(
            db=db,
            limit=limit,
            offset=offset,
        )

    if normalized in {
        "tenure settlement",
        "tenure timeout",
        "tenure-timeout",
        "tenure timeout settlement",
    }:
        return get_superadmin_tenure_timeout_settlements(
            db=db,
            limit=limit,
            offset=offset,
        )

    return get_monthly_payment_queue(
        db=db,
        payment_type=payment_type,
        limit=limit,
        offset=offset,
    )

def get_monthly_payment_queue(
    db: Session,
    payment_type: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
):
    result = db.execute(
        text(
            """
            SELECT *
            FROM public.fn_superadmin_get_payment_queue(
                :p_payment_type,
                :p_limit,
                :p_offset
            )
            """
        ),
        {
            "p_payment_type": payment_type,
            "p_limit": limit,
            "p_offset": offset,
        },
    )

    return [dict(row) for row in result.mappings().all()]



def get_payment_details(
    db: Session,
    source_id: int,
    payment_type: str,
):
    normalized = _normalize_payment_type(payment_type)

    if normalized in {
        "pre-close settlement",
        "preclose settlement",
        "pre-close",
        "preclose",
    }:
        return get_superadmin_preclose_request_details(
            db=db,
            request_id=source_id,
        )

    if normalized in {
        "tenure settlement",
        "tenure timeout",
        "tenure-timeout",
        "tenure timeout settlement",
    }:
        return get_superadmin_tenure_timeout_settlement_details(
            db=db,
            settlement_id=source_id,
        )

    result = db.execute(
        text(
            """
            SELECT *
            FROM public.fn_superadmin_get_payment_details(
                :p_source_id,
                :p_payment_type
            )
            """
        ),
        {
            "p_source_id": source_id,
            "p_payment_type": payment_type,
        },
    )

    row = result.mappings().first()
    return dict(row) if row else None

def approve_payment(
    db: Session,
    source_id: int,
    payment_type: str,
    approved_by: int,
):
    normalized = _normalize_payment_type(payment_type)

    try:

        # ============================================================
        # MONTHLY INTEREST
        # ============================================================
        # Super Admin approval only.
        # Admin has already moved the record to "Awaiting Approval".
        # ============================================================
        if normalized in {
            "monthly interest",
            "monthly_interest",
            "monthlyinterest",
        }:

            # Get current payment status
            current_result = db.execute(
                text(
                    """
                    SELECT
                        ins.id,
                        ins.payment_status_id,
                        ps.payment_status_name
                    FROM public.tn_interest_schedule ins
                    INNER JOIN public.master_payment_status ps
                        ON ps.id = ins.payment_status_id
                    WHERE ins.id = :p_source_id
                    FOR UPDATE
                    """
                ),
                {
                    "p_source_id": source_id,
                },
            ).mappings().first()

            if not current_result:
                raise HTTPException(
                    status_code=404,
                    detail="Monthly interest payment not found.",
                )

            current_status = str(
                current_result["payment_status_name"] or ""
            ).strip()

            # Super Admin can approve only Admin-submitted requests
            if current_status.lower() != "awaiting approval":
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Monthly interest payment must be in "
                        "'Awaiting Approval' status before Super Admin approval. "
                        f"Current status: {current_status or 'Unknown'}."
                    ),
                )

            # Find Approved status ID dynamically
            approved_status_result = db.execute(
                text(
                    """
                    SELECT id
                    FROM public.master_payment_status
                    WHERE LOWER(TRIM(payment_status_name))
                        = LOWER(TRIM('Approved'))
                    LIMIT 1
                    """
                )
            ).mappings().first()

            if not approved_status_result:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "'Approved' status is not configured "
                        "in master_payment_status."
                    ),
                )

            approved_status_id = approved_status_result["id"]

            # --------------------------------------------------------
            # FINAL SUPER ADMIN APPROVAL
            # --------------------------------------------------------
            result = db.execute(
                text(
                    """
                    UPDATE public.tn_interest_schedule
                    SET
                        payment_status_id = :p_status_id,
                        superadmin_approved_by = :p_approved_by,
                        approved_date = CURRENT_TIMESTAMP,
                        modified_by = :p_approved_by,
                        modified_date = CURRENT_TIMESTAMP
                    WHERE id = :p_source_id
                      AND payment_status_id = :p_current_status_id
                    RETURNING
                        id AS source_id,
                        payment_status_id,
                        superadmin_approved_by,
                        approved_date,
                        modified_by,
                        modified_date
                    """
                ),
                {
                    "p_status_id": approved_status_id,
                    "p_approved_by": approved_by,
                    "p_source_id": source_id,
                    "p_current_status_id": current_result[
                        "payment_status_id"
                    ],
                },
            ).mappings().first()

            if not result:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Monthly interest payment could not be approved. "
                        "The status may have changed already."
                    ),
                )

            db.commit()

            return {
                "success": True,
                "source_id": source_id,
                "payment_type": "MONTHLY_INTEREST",
                "status": "Approved",
                "approved_by": approved_by,
                "message": (
                    "Monthly interest payment approved successfully."
                ),
            }

        # ============================================================
        # PRE-CLOSE
        # ============================================================
        # DO NOT CHANGE
        # ============================================================
        if normalized in {
            "pre-close settlement",
            "preclose settlement",
            "pre-close",
            "preclose",
        }:
            return _approve_preclose(
                db=db,
                request_id=source_id,
                approved_by=approved_by,
            )

        # ============================================================
        # TENURE TIMEOUT / TENURE SETTLEMENT
        # ============================================================
        # DO NOT CHANGE
        # ============================================================
        if normalized in {
            "tenure settlement",
            "tenure timeout",
            "tenure-timeout",
            "tenure timeout settlement",
        }:
            return _approve_tenure_settlement(
                db=db,
                settlement_id=source_id,
                approved_by=approved_by,
            )

        # ============================================================
        # FALLBACK - KEEP EXISTING BEHAVIOUR
        # ============================================================
        result = db.execute(
            text(
                """
                SELECT *
                FROM public.fn_superadmin_approve_payment(
                    :p_source_id,
                    :p_payment_type,
                    :p_approved_by
                )
                """
            ),
            {
                "p_source_id": source_id,
                "p_payment_type": payment_type,
                "p_approved_by": approved_by,
            },
        )

        row = result.mappings().first()

        db.commit()

        return dict(row) if row else None

    except HTTPException:
        db.rollback()
        raise

    except Exception:
        db.rollback()
        raise

def mark_payment_paid(
    db: Session,
    source_id: int,
    payment_type: str,
    paid_by: int,
):
    normalized = _normalize_payment_type(payment_type)

    try:
        if normalized in {
            "pre-close settlement",
            "preclose settlement",
            "pre-close",
            "preclose",
        }:
            return _mark_preclose_paid(
                db=db,
                request_id=source_id,
                paid_by=paid_by,
            )

        if normalized in {
            "tenure settlement",
            "tenure timeout",
            "tenure-timeout",
            "tenure timeout settlement",
        }:
            return _mark_tenure_settlement_paid(
                db=db,
                settlement_id=source_id,
                paid_by=paid_by,
            )

        result = db.execute(
            text(
                """
                SELECT *
                FROM public.fn_superadmin_mark_payment_paid(
                    :p_source_id,
                    :p_payment_type,
                    :p_paid_by
                )
                """
            ),
            {
                "p_source_id": source_id,
                "p_payment_type": payment_type,
                "p_paid_by": paid_by,
            },
        )

        row = result.mappings().first()
        db.commit()

        return dict(row) if row else None

    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise


def reject_payment(
    db: Session,
    source_id: int,
    payment_type: str,
    rejected_by: int,
    rejection_reason: str,
):
    reason = (rejection_reason or "").strip()

    if not reason:
        raise ValueError("Rejection reason is required.")

    normalized = _normalize_payment_type(payment_type)

    try:
        if normalized in {
            "pre-close settlement",
            "preclose settlement",
            "pre-close",
            "preclose",
        }:
            return _reject_preclose(
                db=db,
                request_id=source_id,
                rejected_by=rejected_by,
                rejection_reason=reason,
            )

        if normalized in {
            "tenure settlement",
            "tenure timeout",
            "tenure-timeout",
            "tenure timeout settlement",
        }:
            return _reject_tenure_settlement(
                db=db,
                settlement_id=source_id,
                rejected_by=rejected_by,
                rejection_reason=reason,
            )

        result = db.execute(
            text(
                """
                SELECT *
                FROM public.fn_superadmin_reject_payment(
                    :p_source_id,
                    :p_payment_type,
                    :p_rejected_by,
                    :p_rejection_reason
                )
                """
            ),
            {
                "p_source_id": source_id,
                "p_payment_type": payment_type,
                "p_rejected_by": rejected_by,
                "p_rejection_reason": reason,
            },
        )

        row = result.mappings().first()
        db.commit()

        return dict(row) if row else None

    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise


def get_pending_tenure_extensions(
    db: Session,
    branch_id: Optional[int] = None,
    limit: int = 100,
    offset: int = 0,
):
    result = db.execute(
        text(
            """
            SELECT *
            FROM public.fn_admin_get_pending_tenure_extensions(
                CAST(:p_branch_id AS INTEGER),
                CAST(:p_limit AS INTEGER),
                CAST(:p_offset AS INTEGER)
            )
            """
        ),
        {
            "p_branch_id": branch_id,
            "p_limit": limit,
            "p_offset": offset,
        },
    )

    return [
        dict(row)
        for row in result.mappings().all()
    ]



def get_all_tenure_extensions_for_superadmin(
    db: Session,
    branch_id: Optional[int] = None,
    limit: int = 100,
    offset: int = 0,
):
    result = db.execute(
        text(
            """
            SELECT *
            FROM public.fn_superadmin_get_all_tenure_extensions(
                CAST(:p_branch_id AS INTEGER),
                CAST(:p_limit AS INTEGER),
                CAST(:p_offset AS INTEGER)
            )
            """
        ),
        {
            "p_branch_id": branch_id,
            "p_limit": limit,
            "p_offset": offset,
        },
    )

    return [
        dict(row)
        for row in result.mappings().all()
    ]



def get_tenure_extension_details(
    db: Session,
    request_id: int,
):
    result = db.execute(
        text(
            """
            SELECT *
            FROM public.fn_admin_get_tenure_extension_details(
                CAST(:p_request_id AS BIGINT)
            )
            """
        ),
        {
            "p_request_id": request_id,
        },
    )

    row = result.mappings().first()

    if not row:
        return None

    return dict(row)



def approve_tenure_extension(
    db: Session,
    request_id: int,
    approved_by: int,
    remarks: Optional[str] = None,
):
    try:
        result = db.execute(
            text(
                """
                SELECT
                    r.id AS request_id,
                    r.request_status_id,
                    s.status_name
                FROM public.tn_tenure_extension_request r
                INNER JOIN public.master_investor_request_status s
                    ON s.id = r.request_status_id
                WHERE r.id = :p_request_id
                  AND LOWER(TRIM(s.status_name))
                      = LOWER(TRIM('Pending super admin'))
                FOR UPDATE
                """
            ),
            {
                "p_request_id": request_id,
            },
        )

        request = result.mappings().first()

        if not request:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Tenure extension request is not in "
                    "'Pending super admin' status."
                ),
            )

        approved_status = db.execute(
            text(
                """
                SELECT id
                FROM public.master_investor_request_status
                WHERE LOWER(TRIM(status_name))
                    = LOWER(TRIM('Approved'))
                  AND COALESCE(is_active, TRUE) = TRUE
                LIMIT 1
                """
            )
        ).mappings().first()

        if not approved_status:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Approved status is not configured "
                    "in master_investor_request_status."
                ),
            )

        approved_status_id = approved_status["id"]

        db.execute(
            text(
                """
                UPDATE public.tn_tenure_extension_request
                SET
                    request_status_id = :p_status_id,
                    modified_by = :p_modified_by,
                    modified_date = CURRENT_TIMESTAMP,
                    remarks = COALESCE(
                        :p_remarks,
                        remarks
                    )
                WHERE id = :p_request_id
                  AND request_status_id = :p_current_status_id
                """
            ),
            {
                "p_status_id": approved_status_id,
                "p_modified_by": approved_by,
                "p_remarks": remarks.strip()
                if remarks
                else None,
                "p_request_id": request_id,
                "p_current_status_id": request[
                    "request_status_id"
                ],
            },
        )

        db.commit()

        return {
            "success": True,
            "request_id": request_id,
            "status": "Approved",
            "message": (
                "Tenure extension approved successfully."
            ),
        }

    except HTTPException:
        db.rollback()
        raise

    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )



def reject_tenure_extension(
    db: Session,
    request_id: int,
    rejected_by: int,
    remarks: str,
):
    reason = (remarks or "").strip()

    if not reason:
        raise ValueError(
            "Rejection reason is required."
        )

    try:
        result = db.execute(
            text(
                """
                SELECT
                    r.id AS request_id,
                    r.request_status_id,
                    s.status_name
                FROM public.tn_tenure_extension_request r
                INNER JOIN public.master_investor_request_status s
                    ON s.id = r.request_status_id
                WHERE r.id = :p_request_id
                  AND LOWER(TRIM(s.status_name))
                      = LOWER(TRIM('Pending super admin'))
                FOR UPDATE
                """
            ),
            {
                "p_request_id": request_id,
            },
        )

        request = result.mappings().first()

        if not request:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Tenure extension request is not in "
                    "'Pending super admin' status."
                ),
            )

        rejected_status = db.execute(
            text(
                """
                SELECT id
                FROM public.master_investor_request_status
                WHERE LOWER(TRIM(status_name))
                    = LOWER(TRIM('Rejected'))
                  AND COALESCE(is_active, TRUE) = TRUE
                LIMIT 1
                """
            )
        ).mappings().first()

        if not rejected_status:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Rejected status is not configured "
                    "in master_investor_request_status."
                ),
            )

        rejected_status_id = rejected_status["id"]

        db.execute(
            text(
                """
                UPDATE public.tn_tenure_extension_request
                SET
                    request_status_id = :p_status_id,
                    modified_by = :p_modified_by,
                    modified_date = CURRENT_TIMESTAMP,
                    remarks = :p_remarks
                WHERE id = :p_request_id
                  AND request_status_id = :p_current_status_id
                """
            ),
            {
                "p_status_id": rejected_status_id,
                "p_modified_by": rejected_by,
                "p_remarks": reason,
                "p_request_id": request_id,
                "p_current_status_id": request[
                    "request_status_id"
                ],
            },
        )

        db.commit()

        return {
            "success": True,
            "request_id": request_id,
            "status": "Rejected",
            "message": (
                "Tenure extension rejected successfully."
            ),
        }

    except HTTPException:
        db.rollback()
        raise

    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )



def mark_tenure_extension_paid(
    db: Session,
    request_id: int,
    paid_by: int,
):
    try:
        result = db.execute(
            text(
                """
                WITH approved_status AS (
                    SELECT id
                    FROM public.master_investor_request_status
                    WHERE LOWER(TRIM(status_name)) = 'approved'
                      AND COALESCE(is_active, TRUE) = TRUE
                    LIMIT 1
                ),
                paid_status AS (
                    SELECT id, status_name
                    FROM public.master_investor_request_status
                    WHERE LOWER(TRIM(status_name)) = 'paid'
                      AND COALESCE(is_active, TRUE) = TRUE
                    LIMIT 1
                )
                UPDATE public.tn_tenure_extension_request AS r
                SET
                    request_status_id = paid_status.id,
                    modified_by = :p_paid_by,
                    modified_date = CURRENT_TIMESTAMP
                FROM paid_status
                WHERE r.id = :p_request_id
                  AND r.request_status_id = (
                      SELECT id
                      FROM approved_status
                  )
                RETURNING
                    r.id AS request_id,
                    r.request_status_id,
                    paid_status.status_name AS status
                """
            ),
            {
                "p_request_id": request_id,
                "p_paid_by": paid_by,
            },
        )

        row = result.mappings().first()

        if not row:
            exists = db.execute(
                text(
                    """
                    SELECT
                        r.id,
                        s.status_name
                    FROM public.tn_tenure_extension_request r
                    JOIN public.master_investor_request_status s
                        ON s.id = r.request_status_id
                    WHERE r.id = :p_request_id
                    """
                ),
                {
                    "p_request_id": request_id,
                },
            ).mappings().first()

            if not exists:
                raise ValueError(
                    "Tenure extension request not found."
                )

            current_status = str(
                exists.get("status_name") or ""
            ).strip()

            if current_status.lower() == "paid":
                db.commit()

                return {
                    "request_id": request_id,
                    "status": "Paid",
                    "already_paid": True,
                }

            if current_status.lower() != "approved":
                raise ValueError(
                    "Tenure extension must be Approved "
                    "before marking it Paid. "
                    f"Current status: "
                    f"{current_status or 'Unknown'}."
                )

            raise ValueError(
                "Paid status is not configured in "
                "master_investor_request_status."
            )

        db.commit()

        return dict(row)

    except Exception:
        db.rollback()
        raise











from sqlalchemy import text
from sqlalchemy.orm import Session



def get_superadmin_preclose_requests(
    db: Session,
    limit: int = 100,
    offset: int = 0,
):
    result = db.execute(
        text(
            """
            SELECT
                pr.id AS preclose_request_id,
                pr.id AS source_id,
                u.full_name AS investor,
                r.investor_id,
                b.bond_id AS bond_number,
                mb.branch_name AS branch,

                pr.requested_date AS requested_on,
                pr.preclose_reason AS reason,

                CASE
                    WHEN LOWER(TRIM(rs.status_name))
                        IN ('pending', 'pending super admin')
                        THEN 'Pending'
                    WHEN LOWER(TRIM(rs.status_name)) = 'approved'
                        THEN 'Approved'
                    WHEN LOWER(TRIM(rs.status_name)) = 'rejected'
                        THEN 'Rejected'
                    WHEN LOWER(TRIM(rs.status_name)) = 'paid'
                        THEN 'Paid'
                    ELSE rs.status_name
                END AS status,

                CASE
                    WHEN LOWER(TRIM(rs.status_name))
                        IN ('pending', 'pending super admin')
                        THEN 'Pending'
                    ELSE rs.status_name
                END AS action,

                creator.full_name AS requested_by_name,
                approver.full_name AS approved_by_name,

                i.id AS investment_id,
                i.investment_amount,
                i.investment_date,
                i.maturity_date,
                i.expected_interest_amount,

                s.id AS settlement_id,
                COALESCE(s.principal_amount, i.investment_amount, 0)
                    AS principal_amount,
                COALESCE(s.interest_amount, i.expected_interest_amount, 0)
                    AS interest_amount,
                COALESCE(s.penalty_amount, 0) AS penalty_amount,
                COALESCE(s.gst_amount, 0) AS gst_amount,
                COALESCE(
                    s.net_settlement_amount,
                    (
                        COALESCE(s.principal_amount, i.investment_amount, 0)
                        + COALESCE(s.interest_amount, i.expected_interest_amount, 0)
                        - COALESCE(s.gst_amount, 0)
                        - COALESCE(s.penalty_amount, 0)
                    )
                ) AS net_settlement_amount,

                ss.status_name AS settlement_status

            FROM public.tn_preclose_request pr

            INNER JOIN public.tn_investment i
                ON i.id = pr.investment_id

            INNER JOIN public.tn_investor_registration r
                ON r.id = i.investor_registration_id

            INNER JOIN public.tn_application_user u
                ON u.id = r.user_id

            LEFT JOIN public.tn_application_user creator
                ON creator.id = pr.created_by

            LEFT JOIN public.tn_application_user approver
                ON approver.id = pr.approved_by

            LEFT JOIN public.master_branch mb
                ON mb.id = r.branch_id

            LEFT JOIN public.tn_bond b
                ON b.investment_id = i.id

            INNER JOIN public.master_investor_request_status rs
                ON rs.id = pr.request_status_id

            LEFT JOIN public.tn_settlement s
                ON s.investment_id = i.id
                AND UPPER(TRIM(s.settlement_type)) = 'PRECLOSE'

            LEFT JOIN public.master_settlement_status ss
                ON ss.id = s.settlement_status_id

            WHERE LOWER(TRIM(rs.status_name)) IN (
                'pending',
                'pending super admin',
                'approved',
                'rejected',
                'paid'
            )

            ORDER BY
                pr.requested_date DESC NULLS LAST,
                pr.id DESC

            LIMIT :p_limit
            OFFSET :p_offset
            """
        ),
        {
            "p_limit": limit,
            "p_offset": offset,
        },
    )

    return [dict(row) for row in result.mappings().all()]


def get_superadmin_preclose_request_details(
    db: Session,
    request_id: int,
):
    result = db.execute(
        text(
            """
            SELECT
                pr.id AS preclose_request_id,
                pr.id AS source_id,

                u.full_name AS investor,
                r.investor_id,
                b.bond_id AS bond_number,
                mb.branch_name AS branch,

                pr.requested_date AS requested_on,
                pr.preclose_reason AS reason,

                CASE
                    WHEN LOWER(TRIM(rs.status_name))
                        IN ('pending', 'pending super admin')
                        THEN 'Pending'
                    WHEN LOWER(TRIM(rs.status_name)) = 'approved'
                        THEN 'Approved'
                    WHEN LOWER(TRIM(rs.status_name)) = 'rejected'
                        THEN 'Rejected'
                    WHEN LOWER(TRIM(rs.status_name)) = 'paid'
                        THEN 'Paid'
                    ELSE rs.status_name
                END AS status,

                creator.full_name AS requested_by_name,
                approver.full_name AS approved_by_name,

                i.id AS investment_id,
                i.investment_amount,
                i.investment_date,
                i.maturity_date,
                i.expected_interest_amount,

                s.id AS settlement_id,
                COALESCE(s.principal_amount, i.investment_amount, 0)
                    AS principal_amount,
                COALESCE(s.interest_amount, i.expected_interest_amount, 0)
                    AS interest_amount,
                COALESCE(s.penalty_amount, 0) AS penalty_amount,
                COALESCE(s.gst_amount, 0) AS gst_amount,
                COALESCE(
                    s.net_settlement_amount,
                    (
                        COALESCE(s.principal_amount, i.investment_amount, 0)
                        + COALESCE(s.interest_amount, i.expected_interest_amount, 0)
                        - COALESCE(s.gst_amount, 0)
                        - COALESCE(s.penalty_amount, 0)
                    )
                ) AS net_settlement_amount,

                ss.status_name AS settlement_status

            FROM public.tn_preclose_request pr

            INNER JOIN public.tn_investment i
                ON i.id = pr.investment_id

            INNER JOIN public.tn_investor_registration r
                ON r.id = i.investor_registration_id

            INNER JOIN public.tn_application_user u
                ON u.id = r.user_id

            LEFT JOIN public.tn_application_user creator
                ON creator.id = pr.created_by

            LEFT JOIN public.tn_application_user approver
                ON approver.id = pr.approved_by

            LEFT JOIN public.master_branch mb
                ON mb.id = r.branch_id

            LEFT JOIN public.tn_bond b
                ON b.investment_id = i.id

            INNER JOIN public.master_investor_request_status rs
                ON rs.id = pr.request_status_id

            LEFT JOIN public.tn_settlement s
                ON s.investment_id = i.id
                AND UPPER(TRIM(s.settlement_type)) = 'PRECLOSE'

            LEFT JOIN public.master_settlement_status ss
                ON ss.id = s.settlement_status_id

            WHERE pr.id = :p_request_id
            """
        ),
        {"p_request_id": request_id},
    )

    row = result.mappings().first()
    return dict(row) if row else None


def get_superadmin_tenure_timeout_settlements(
    db: Session,
    limit: int = 100,
    offset: int = 0,
):
    result = db.execute(
        text(
            """
            SELECT
                s.id AS settlement_id,
                s.id AS source_id,

                u.full_name AS investor,
                r.investor_id,
                b.bond_id AS bond_number,
                mb.branch_name AS branch,

                s.created_date AS requested_on,
                s.approved_date,

                s.settlement_type,

                s.principal_amount,
                s.interest_amount,
                s.penalty_amount,
                s.gst_amount,
                s.net_settlement_amount,

                CASE
                    WHEN LOWER(TRIM(ss.status_name))
                        IN ('pending', 'pending super admin')
                        THEN 'Pending'
                    WHEN LOWER(TRIM(ss.status_name)) = 'approved'
                        THEN 'Approved'
                    WHEN LOWER(TRIM(ss.status_name)) = 'rejected'
                        THEN 'Rejected'
                    WHEN LOWER(TRIM(ss.status_name)) = 'paid'
                        THEN 'Paid'
                    ELSE ss.status_name
                END AS status,

                creator.full_name AS requested_by_name,
                approver.full_name AS approved_by_name,

                CASE
                    WHEN LOWER(TRIM(ss.status_name))
                        IN ('pending', 'pending super admin')
                        THEN 'Pending'
                    ELSE ss.status_name
                END AS action

            FROM public.tn_settlement s

            INNER JOIN public.tn_investment i
                ON i.id = s.investment_id

            INNER JOIN public.tn_investor_registration r
                ON r.id = i.investor_registration_id

            INNER JOIN public.tn_application_user u
                ON u.id = r.user_id

            LEFT JOIN public.tn_application_user creator
                ON creator.id = s.created_by

            LEFT JOIN public.tn_application_user approver
                ON approver.id = s.approved_by

            LEFT JOIN public.master_branch mb
                ON mb.id = r.branch_id

            INNER JOIN public.master_settlement_status ss
                ON ss.id = s.settlement_status_id

            LEFT JOIN public.tn_bond b
                ON b.investment_id = i.id

            WHERE UPPER(TRIM(s.settlement_type)) = 'TENURE_TIMEOUT'
              AND LOWER(TRIM(ss.status_name)) IN (
                  'pending',
                  'pending super admin',
                  'approved',
                  'rejected',
                  'paid'
              )

            ORDER BY
                s.created_date DESC NULLS LAST,
                s.id DESC

            LIMIT :p_limit
            OFFSET :p_offset
            """
        ),
        {
            "p_limit": limit,
            "p_offset": offset,
        },
    )

    return [dict(row) for row in result.mappings().all()]


def get_superadmin_tenure_timeout_settlement_details(
    db: Session,
    settlement_id: int,
):
    result = db.execute(
        text(
            """
            SELECT
                s.id AS settlement_id,
                s.id AS source_id,

                u.full_name AS investor,
                r.investor_id,
                b.bond_id AS bond_number,
                mb.branch_name AS branch,

                s.created_date AS requested_on,
                s.approved_date,

                s.settlement_type,

                s.principal_amount,
                s.interest_amount,
                s.penalty_amount,
                s.gst_amount,
                s.net_settlement_amount,

                CASE
                    WHEN LOWER(TRIM(ss.status_name))
                        IN ('pending', 'pending super admin')
                        THEN 'Pending'
                    WHEN LOWER(TRIM(ss.status_name)) = 'approved'
                        THEN 'Approved'
                    WHEN LOWER(TRIM(ss.status_name)) = 'rejected'
                        THEN 'Rejected'
                    WHEN LOWER(TRIM(ss.status_name)) = 'paid'
                        THEN 'Paid'
                    ELSE ss.status_name
                END AS status,

                creator.full_name AS requested_by_name,
                approver.full_name AS approved_by_name,

                i.id AS investment_id,
                i.investment_amount,
                i.investment_date,
                i.maturity_date

            FROM public.tn_settlement s

            INNER JOIN public.tn_investment i
                ON i.id = s.investment_id

            INNER JOIN public.tn_investor_registration r
                ON r.id = i.investor_registration_id

            INNER JOIN public.tn_application_user u
                ON u.id = r.user_id

            LEFT JOIN public.tn_application_user creator
                ON creator.id = s.created_by

            LEFT JOIN public.tn_application_user approver
                ON approver.id = s.approved_by

            LEFT JOIN public.master_branch mb
                ON mb.id = r.branch_id

            LEFT JOIN public.tn_bond b
                ON b.investment_id = i.id

            INNER JOIN public.master_settlement_status ss
                ON ss.id = s.settlement_status_id

            WHERE s.id = :p_settlement_id
              AND UPPER(TRIM(s.settlement_type)) = 'TENURE_TIMEOUT'
            """
        ),
        {"p_settlement_id": settlement_id},
    )

    row = result.mappings().first()
    return dict(row) if row else None

def _get_preclose_for_update(
    db: Session,
    request_id: int,
):
    request_result = db.execute(
        text(
            """
            SELECT
                pr.id,
                pr.investment_id,
                pr.request_status_id,
                rs.status_name
            FROM public.tn_preclose_request pr
            INNER JOIN public.master_investor_request_status rs
                ON rs.id = pr.request_status_id
            WHERE pr.id = :p_request_id
            FOR UPDATE OF pr
            """
        ),
        {"p_request_id": request_id},
    ).mappings().first()

    if not request_result:
        raise HTTPException(
            status_code=404,
            detail="Pre-close settlement request not found.",
        )

    current = str(
        request_result["status_name"] or ""
    ).strip().lower()

    if current not in {"pending", "pending super admin"}:
        raise HTTPException(
            status_code=400,
            detail=(
                "Pre-close settlement must be in Pending status "
                f"before this action. Current status: "
                f"{request_result['status_name']}."
            ),
        )

    settlement_result = db.execute(
        text(
            """
            SELECT
                s.id AS settlement_id,
                s.settlement_status_id
            FROM public.tn_settlement s
            WHERE s.investment_id = :p_investment_id
              AND UPPER(TRIM(s.settlement_type)) = 'PRECLOSE'
            FOR UPDATE
            """
        ),
        {
            "p_investment_id": request_result["investment_id"],
        },
    ).mappings().first()

    return {
        "id": request_result["id"],
        "investment_id": request_result["investment_id"],
        "request_status_id": request_result["request_status_id"],
        "status_name": request_result["status_name"],
        "settlement_id": (
            settlement_result["settlement_id"]
            if settlement_result
            else None
        ),
        "settlement_status_id": (
            settlement_result["settlement_status_id"]
            if settlement_result
            else None
        ),
    }

def _approve_preclose(
    db: Session,
    request_id: int,
    approved_by: int,
):
    request = _get_preclose_for_update(db, request_id)

    approved_request_status_id = _get_status_id(
        db,
        "master_investor_request_status",
        "Approved",
    )

    db.execute(
        text(
            """
            UPDATE public.tn_preclose_request
            SET
                request_status_id = :p_status_id,
                approved_by = :p_approved_by,
                approved_date = CURRENT_TIMESTAMP,
                modified_by = :p_approved_by,
                modified_date = CURRENT_TIMESTAMP
            WHERE id = :p_request_id
            """
        ),
        {
            "p_status_id": approved_request_status_id,
            "p_approved_by": approved_by,
            "p_request_id": request_id,
        },
    )

    if request["settlement_id"] is not None:
        approved_settlement_status_id = _get_status_id(
            db,
            "master_settlement_status",
            "Approved",
        )

        db.execute(
            text(
                """
                UPDATE public.tn_settlement
                SET
                    settlement_status_id = :p_status_id,
                    approved_by = :p_approved_by,
                    approved_date = CURRENT_TIMESTAMP,
                    modified_by = :p_approved_by,
                    modified_date = CURRENT_TIMESTAMP
                WHERE id = :p_settlement_id
                """
            ),
            {
                "p_status_id": approved_settlement_status_id,
                "p_approved_by": approved_by,
                "p_settlement_id": request["settlement_id"],
            },
        )

    db.commit()

    return {
        "success": True,
        "source_id": request_id,
        "status": "Approved",
        "message": "Pre-close settlement approved successfully.",
    }


def _reject_preclose(
    db: Session,
    request_id: int,
    rejected_by: int,
    rejection_reason: str,
):
    request = _get_preclose_for_update(db, request_id)

    rejected_request_status_id = _get_status_id(
        db,
        "master_investor_request_status",
        "Rejected",
    )

    db.execute(
        text(
            """
            UPDATE public.tn_preclose_request
            SET
                request_status_id = :p_status_id,
                remarks = :p_remarks,
                modified_by = :p_rejected_by,
                modified_date = CURRENT_TIMESTAMP
            WHERE id = :p_request_id
            """
        ),
        {
            "p_status_id": rejected_request_status_id,
            "p_remarks": rejection_reason,
            "p_rejected_by": rejected_by,
            "p_request_id": request_id,
        },
    )

    if request["settlement_id"] is not None:
        rejected_settlement_status_id = _get_status_id(
            db,
            "master_settlement_status",
            "Rejected",
        )

        db.execute(
            text(
                """
                UPDATE public.tn_settlement
                SET
                    settlement_status_id = :p_status_id,
                    remarks = :p_remarks,
                    modified_by = :p_rejected_by,
                    modified_date = CURRENT_TIMESTAMP
                WHERE id = :p_settlement_id
                """
            ),
            {
                "p_status_id": rejected_settlement_status_id,
                "p_remarks": rejection_reason,
                "p_rejected_by": rejected_by,
                "p_settlement_id": request["settlement_id"],
            },
        )

    db.commit()

    return {
        "success": True,
        "source_id": request_id,
        "status": "Rejected",
        "message": "Pre-close settlement rejected successfully.",
    }

def _mark_preclose_paid(
    db: Session,
    request_id: int,
    paid_by: int,
):
    request_result = db.execute(
        text(
            """
            SELECT
                pr.id,
                pr.investment_id,
                pr.request_status_id,
                rs.status_name
            FROM public.tn_preclose_request pr
            INNER JOIN public.master_investor_request_status rs
                ON rs.id = pr.request_status_id
            WHERE pr.id = :p_request_id
            FOR UPDATE OF pr
            """
        ),
        {
            "p_request_id": request_id,
        },
    ).mappings().first()

    if not request_result:
        raise HTTPException(
            status_code=404,
            detail="Pre-close settlement request not found.",
        )

    current_status = str(
        request_result["status_name"] or ""
    ).strip().lower()

    if current_status == "paid":
        db.commit()

        return {
            "success": True,
            "source_id": request_id,
            "status": "Paid",
            "already_paid": True,
            "message": "Pre-close settlement is already marked as Paid.",
        }

    if current_status != "approved":
        raise HTTPException(
            status_code=400,
            detail=(
                "Pre-close settlement must be Approved before "
                "marking it Paid. Current status: "
                f"{request_result['status_name']}."
            ),
        )

    settlement_result = db.execute(
        text(
            """
            SELECT
                s.id AS settlement_id,
                s.settlement_status_id
            FROM public.tn_settlement s
            WHERE s.investment_id = :p_investment_id
              AND UPPER(TRIM(s.settlement_type)) = 'PRECLOSE'
            FOR UPDATE
            """
        ),
        {
            "p_investment_id": request_result["investment_id"],
        },
    ).mappings().first()

    if not settlement_result:
        raise HTTPException(
            status_code=404,
            detail=(
                "Pre-close settlement record not found for "
                f"investment ID {request_result['investment_id']}."
            ),
        )

    paid_request_status_id = _get_status_id(
        db,
        "master_investor_request_status",
        "Paid",
    )

    paid_settlement_status_id = _get_status_id(
        db,
        "master_settlement_status",
        "Paid",
    )

    db.execute(
        text(
            """
            UPDATE public.tn_preclose_request
            SET
                request_status_id = :p_status_id,
                modified_by = :p_paid_by,
                modified_date = CURRENT_TIMESTAMP
            WHERE id = :p_request_id
            """
        ),
        {
            "p_status_id": paid_request_status_id,
            "p_paid_by": paid_by,
            "p_request_id": request_id,
        },
    )

    db.execute(
        text(
            """
            UPDATE public.tn_settlement
            SET
                settlement_status_id = :p_settlement_status_id,
                paid_by = :p_paid_by,
                paid_date = CURRENT_TIMESTAMP,
                modified_by = :p_paid_by,
                modified_date = CURRENT_TIMESTAMP
            WHERE id = :p_settlement_id
            """
        ),
        {
            "p_settlement_status_id": paid_settlement_status_id,
            "p_paid_by": paid_by,
            "p_settlement_id": settlement_result["settlement_id"],
        },
    )

    db.commit()

    return {
        "success": True,
        "source_id": request_id,
        "status": "Paid",
        "already_paid": False,
        "message": "Pre-close settlement marked as Paid successfully.",
    }


def _get_tenure_settlement_for_update(
    db: Session,
    settlement_id: int,
):
    result = db.execute(
        text(
            """
            SELECT
                s.id,
                s.settlement_status_id,
                ss.status_name
            FROM public.tn_settlement s
            INNER JOIN public.master_settlement_status ss
                ON ss.id = s.settlement_status_id
            WHERE s.id = :p_settlement_id
              AND UPPER(TRIM(s.settlement_type)) = 'TENURE_TIMEOUT'
            FOR UPDATE
            """
        ),
        {"p_settlement_id": settlement_id},
    ).mappings().first()

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Tenure settlement not found.",
        )

    current = str(result["status_name"] or "").strip().lower()

    if current not in {"pending", "pending super admin"}:
        raise HTTPException(
            status_code=400,
            detail=(
                "Tenure settlement must be in Pending status "
                f"before this action. Current status: "
                f"{result['status_name']}."
            ),
        )

    return result


def _approve_tenure_settlement(
    db: Session,
    settlement_id: int,
    approved_by: int,
):
    _get_tenure_settlement_for_update(db, settlement_id)

    approved_status_id = _get_status_id(
        db,
        "master_settlement_status",
        "Approved",
    )

    db.execute(
        text(
            """
            UPDATE public.tn_settlement
            SET
                settlement_status_id = :p_status_id,
                approved_by = :p_approved_by,
                approved_date = CURRENT_TIMESTAMP,
                modified_by = :p_approved_by,
                modified_date = CURRENT_TIMESTAMP
            WHERE id = :p_settlement_id
              AND UPPER(TRIM(settlement_type)) = 'TENURE_TIMEOUT'
            """
        ),
        {
            "p_status_id": approved_status_id,
            "p_approved_by": approved_by,
            "p_settlement_id": settlement_id,
        },
    )

    db.commit()

    return {
        "success": True,
        "source_id": settlement_id,
        "status": "Approved",
        "message": "Tenure settlement approved successfully.",
    }


def _reject_tenure_settlement(
    db: Session,
    settlement_id: int,
    rejected_by: int,
    rejection_reason: str,
):
    _get_tenure_settlement_for_update(db, settlement_id)

    rejected_status_id = _get_status_id(
        db,
        "master_settlement_status",
        "Rejected",
    )

    db.execute(
        text(
            """
            UPDATE public.tn_settlement
            SET
                settlement_status_id = :p_status_id,
                remarks = :p_remarks,
                modified_by = :p_rejected_by,
                modified_date = CURRENT_TIMESTAMP
            WHERE id = :p_settlement_id
              AND UPPER(TRIM(settlement_type)) = 'TENURE_TIMEOUT'
            """
        ),
        {
            "p_status_id": rejected_status_id,
            "p_remarks": rejection_reason,
            "p_rejected_by": rejected_by,
            "p_settlement_id": settlement_id,
        },
    )

    db.commit()

    return {
        "success": True,
        "source_id": settlement_id,
        "status": "Rejected",
        "message": "Tenure settlement rejected successfully.",
    }


def _mark_tenure_settlement_paid(
    db: Session,
    settlement_id: int,
    paid_by: int,
):
    result = db.execute(
        text(
            """
            SELECT
                s.id,
                ss.status_name
            FROM public.tn_settlement s
            INNER JOIN public.master_settlement_status ss
                ON ss.id = s.settlement_status_id
            WHERE s.id = :p_settlement_id
              AND UPPER(TRIM(s.settlement_type)) = 'TENURE_TIMEOUT'
            FOR UPDATE
            """
        ),
        {"p_settlement_id": settlement_id},
    ).mappings().first()

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Tenure settlement not found.",
        )

    current = str(result["status_name"] or "").strip().lower()

    if current == "paid":
        db.commit()
        return {
            "success": True,
            "source_id": settlement_id,
            "status": "Paid",
            "already_paid": True,
        }

    if current != "approved":
        raise HTTPException(
            status_code=400,
            detail=(
                "Tenure settlement must be Approved before "
                f"marking it Paid. Current status: "
                f"{result['status_name']}."
            ),
        )

    paid_status_id = _get_status_id(
        db,
        "master_settlement_status",
        "Paid",
    )

    db.execute(
        text(
            """
            UPDATE public.tn_settlement
            SET
                settlement_status_id = :p_status_id,
                paid_by = :p_paid_by,
                paid_date = CURRENT_TIMESTAMP,
                modified_by = :p_paid_by,
                modified_date = CURRENT_TIMESTAMP
            WHERE id = :p_settlement_id
              AND UPPER(TRIM(settlement_type)) = 'TENURE_TIMEOUT'
            """
        ),
        {
            "p_status_id": paid_status_id,
            "p_paid_by": paid_by,
            "p_settlement_id": settlement_id,
        },
    )

    db.commit()

    return {
        "success": True,
        "source_id": settlement_id,
        "status": "Paid",
        "message": "Tenure settlement marked as paid successfully.",
    }

