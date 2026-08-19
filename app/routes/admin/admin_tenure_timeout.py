from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_admin_or_superadmin


router = APIRouter(
    prefix="/admin/settlements",
    tags=["Admin Settlements"],
)


def rows_to_dicts(result):
    return [
        dict(row)
        for row in result.mappings().all()
    ]


def get_current_admin_id(current_user):
    if current_user is None:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
        )

    if hasattr(current_user, "id"):
        return int(current_user.id)

    if isinstance(current_user, dict):
        user_id = (
            current_user.get("id")
            or current_user.get("user_id")
        )

        if user_id:
            return int(user_id)

    user_id = getattr(
        current_user,
        "user_id",
        None,
    )

    if user_id:
        return int(user_id)

    raise HTTPException(
        status_code=401,
        detail="Invalid authentication token",
    )


def get_role_name(current_user):
    role = getattr(
        current_user,
        "role",
        None,
    )

    if isinstance(role, str):
        return role.strip().upper()

    if role is not None:
        role_name = getattr(
            role,
            "role_name",
            None,
        )

        if role_name:
            return str(
                role_name
            ).strip().upper()

    role_name = getattr(
        current_user,
        "role_name",
        None,
    )

    if role_name:
        return str(
            role_name
        ).strip().upper()

    return ""


def get_admin_branch_id(current_user):
    role_name = get_role_name(
        current_user
    )

    if role_name == "SUPERADMIN":
        return None

    if role_name != "ADMIN":
        raise HTTPException(
            status_code=403,
            detail="Admin access required.",
        )

    branch_id = getattr(
        current_user,
        "branch_id",
        None,
    )

    if branch_id is None:
        raise HTTPException(
            status_code=403,
            detail="Admin branch is not assigned.",
        )

    try:
        branch_id = int(branch_id)

    except (
        TypeError,
        ValueError,
    ):
        raise HTTPException(
            status_code=403,
            detail="Invalid admin branch.",
        )

    if branch_id <= 0:
        raise HTTPException(
            status_code=403,
            detail="Invalid admin branch.",
        )

    return branch_id


def create_due_tenure_timeout_settlements(
    db: Session,
    admin_id: int,
    branch_id=None,
):
    if branch_id is None:
        investments_result = db.execute(
            text(
                """
                SELECT
                    i.id

                FROM public.tn_investment i

                WHERE
                    i.maturity_date IS NOT NULL
                    AND i.maturity_date <= CURRENT_DATE

                    AND NOT EXISTS (
                        SELECT 1
                        FROM public.tn_settlement s

                        WHERE
                            s.investment_id = i.id
                            AND s.settlement_type =
                                'TENURE_TIMEOUT'
                    )

                ORDER BY i.id
                """
            )
        )

    else:
        investments_result = db.execute(
            text(
                """
                SELECT
                    i.id

                FROM public.tn_investment i

                INNER JOIN public.tn_investor_registration ir
                    ON ir.id =
                       i.investor_registration_id

                WHERE
                    i.maturity_date IS NOT NULL
                    AND i.maturity_date <= CURRENT_DATE

                    AND ir.branch_id =
                        :branch_id

                    AND NOT EXISTS (
                        SELECT 1
                        FROM public.tn_settlement s

                        WHERE
                            s.investment_id = i.id
                            AND s.settlement_type =
                                'TENURE_TIMEOUT'
                    )

                ORDER BY i.id
                """
            ),
            {
                "branch_id": branch_id,
            },
        )

    investment_ids = [
        row[0]
        for row in investments_result.fetchall()
    ]

    created_count = 0

    for investment_id in investment_ids:
        try:
            result = db.execute(
                text(
                    """
                    SELECT *
                    FROM public.fn_create_tenure_timeout_settlement(
                        :p_investment_id,
                        :p_created_by
                    )
                    """
                ),
                {
                    "p_investment_id": investment_id,
                    "p_created_by": admin_id,
                },
            )

            result.fetchall()

            created_count += 1

        except Exception as exc:
            print(
                f"Failed to create tenure timeout settlement "
                f"for investment {investment_id}: {exc}"
            )

    db.commit()

    return created_count


@router.get("/tenure-timeout")
def get_tenure_timeout_settlements(
    limit: int = Query(
        100,
        ge=1,
        le=500,
    ),
    offset: int = Query(
        0,
        ge=0,
    ),
    db: Session = Depends(get_db),
    current_user=Depends(
        require_admin_or_superadmin
    ),
):
    admin_id = get_current_admin_id(
        current_user
    )

    branch_id = get_admin_branch_id(
        current_user
    )

    try:
        create_due_tenure_timeout_settlements(
            db=db,
            admin_id=admin_id,
            branch_id=branch_id,
        )

        result = db.execute(
            text(
                """
                SELECT
                    s.id AS settlement_id,
                    s.investment_id,
                    s.settlement_type,

                    s.principal_amount,
                    s.interest_amount,
                    s.penalty_amount,
                    s.gst_amount,
                    s.net_settlement_amount,

                    s.settlement_status_id,

                    ms.status_name,

                    s.approved_by,
                    s.approved_date,

                    s.paid_by,
                    s.paid_date,

                    s.remarks,

                    s.created_by,
                    s.created_date,

                    s.modified_by,
                    s.modified_date,

                    i.investment_id AS investment_code,
                    i.investment_amount,
                    i.expected_interest_amount,
                    i.investment_date,
                    i.maturity_date,

                    b.bond_id AS bond_number,

                    ir.id AS investor_registration_id,
                    ir.investor_id,

                    u.full_name AS investor_name,

                    br.branch_name,
                    br.city_name

                FROM public.tn_settlement s

                LEFT JOIN public.master_settlement_status ms
                    ON ms.id =
                       s.settlement_status_id

                LEFT JOIN public.tn_investment i
                    ON i.id =
                       s.investment_id

                LEFT JOIN public.tn_bond b
                    ON b.investment_id =
                       i.id

                LEFT JOIN public.tn_investor_registration ir
                    ON ir.id =
                       i.investor_registration_id

                LEFT JOIN public.tn_application_user u
                    ON u.id =
                       ir.user_id

                LEFT JOIN public.master_branch br
                    ON br.id =
                       ir.branch_id

                WHERE
                    s.settlement_type =
                        'TENURE_TIMEOUT'

                    AND (
                        :branch_id IS NULL
                        OR ir.branch_id =
                           :branch_id
                    )

                ORDER BY
                    s.id DESC

                LIMIT :limit
                OFFSET :offset
                """
            ),
            {
                "branch_id": branch_id,
                "limit": limit,
                "offset": offset,
            },
        )

        rows = rows_to_dicts(result)

        return {
            "success": True,
            "items": rows,
            "data": rows,
            "total": len(rows),
            "limit": limit,
            "offset": offset,
        }

    except Exception as exc:
        db.rollback()

        print(
            "Failed to fetch tenure timeout settlements:",
            str(exc),
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to fetch tenure timeout settlements: "
                f"{str(exc)}"
            ),
        )


@router.get("/preclose")
def get_preclose_requests(
    limit: int = Query(
        100,
        ge=1,
        le=500,
    ),
    offset: int = Query(
        0,
        ge=0,
    ),
    db: Session = Depends(get_db),
    current_user=Depends(
        require_admin_or_superadmin
    ),
):
    branch_id = get_admin_branch_id(
        current_user
    )

    try:
        result = db.execute(
            text(
                """
                SELECT
                    pr.id AS request_id,
                    pr.investment_id,

                    pr.request_status_id,

                    prs.status_name
                        AS request_status,

                    pr.preclose_reason,
                    pr.requested_date,

                    pr.approved_by,
                    pr.approved_date,

                    pr.remarks,

                    pr.created_by,
                    pr.created_date,

                    i.investment_id
                        AS investment_code,

                    i.investment_amount,

                    i.expected_interest_amount,

                    i.investment_date,
                    i.maturity_date,

                    b.bond_id
                        AS bond_number,

                    ir.id
                        AS investor_registration_id,

                    ir.investor_id,

                    u.full_name
                        AS investor_name,

                    br.branch_name,
                    br.city_name

                FROM public.tn_preclose_request pr

                LEFT JOIN
                    public.master_investor_request_status prs
                    ON prs.id =
                       pr.request_status_id

                LEFT JOIN
                    public.tn_investment i
                    ON i.id =
                       pr.investment_id

                LEFT JOIN
                    public.tn_bond b
                    ON b.investment_id =
                       i.id

                LEFT JOIN
                    public.tn_investor_registration ir
                    ON ir.id =
                       i.investor_registration_id

                LEFT JOIN
                    public.tn_application_user u
                    ON u.id =
                       ir.user_id

                LEFT JOIN
                    public.master_branch br
                    ON br.id =
                       ir.branch_id

                WHERE LOWER(
                    COALESCE(
                        prs.status_name,
                        ''
                    )
                ) IN (
                    'pending',
                    'pending approval',
                    'submitted'
                )

                AND (
                    :branch_id IS NULL
                    OR ir.branch_id =
                       :branch_id
                )

                ORDER BY
                    pr.id DESC

                LIMIT :limit
                OFFSET :offset
                """
            ),
            {
                "branch_id": branch_id,
                "limit": limit,
                "offset": offset,
            },
        )

        rows = rows_to_dicts(result)

        return {
            "success": True,
            "items": rows,
            "data": rows,
            "total": len(rows),
            "limit": limit,
            "offset": offset,
        }

    except Exception as exc:
        db.rollback()

        print(
            "Failed to fetch pre-close requests:",
            str(exc),
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to fetch pre-close requests: "
                f"{str(exc)}"
            ),
        )


@router.get("/closed")
def get_closed_settlements(
    limit: int = Query(
        100,
        ge=1,
        le=500,
    ),
    offset: int = Query(
        0,
        ge=0,
    ),
    db: Session = Depends(get_db),
    current_user=Depends(
        require_admin_or_superadmin
    ),
):
    branch_id = get_admin_branch_id(
        current_user
    )

    try:
        result = db.execute(
            text(
                """
                SELECT
                    s.id AS settlement_id,
                    s.investment_id,
                    s.settlement_type,

                    s.principal_amount,
                    s.interest_amount,
                    s.penalty_amount,
                    s.gst_amount,
                    s.net_settlement_amount,

                    s.settlement_status_id,

                    ms.status_name,

                    s.approved_by,
                    s.approved_date,

                    s.paid_by,
                    s.paid_date,

                    s.remarks,

                    s.created_date,
                    s.modified_date,

                    i.investment_id
                        AS investment_code,

                    i.investment_amount,

                    i.investment_date,
                    i.maturity_date,

                    b.bond_id
                        AS bond_number,

                    ir.investor_id,

                    ir.id
                        AS investor_registration_id,

                    u.full_name
                        AS investor_name,

                    br.branch_name,
                    br.city_name

                FROM public.tn_settlement s

                LEFT JOIN
                    public.master_settlement_status ms
                    ON ms.id =
                       s.settlement_status_id

                LEFT JOIN
                    public.tn_investment i
                    ON i.id =
                       s.investment_id

                LEFT JOIN
                    public.tn_bond b
                    ON b.investment_id =
                       i.id

                LEFT JOIN
                    public.tn_investor_registration ir
                    ON ir.id =
                       i.investor_registration_id

                LEFT JOIN
                    public.tn_application_user u
                    ON u.id =
                       ir.user_id

                LEFT JOIN
                    public.master_branch br
                    ON br.id =
                       ir.branch_id

                WHERE LOWER(
                    COALESCE(
                        ms.status_name,
                        ''
                    )
                ) IN (
                    'approved',
                    'settled',
                    'completed',
                    'paid'
                )

                AND (
                    :branch_id IS NULL
                    OR ir.branch_id =
                       :branch_id
                )

                ORDER BY
                    s.id DESC

                LIMIT :limit
                OFFSET :offset
                """
            ),
            {
                "branch_id": branch_id,
                "limit": limit,
                "offset": offset,
            },
        )

        rows = rows_to_dicts(result)

        return {
            "success": True,
            "items": rows,
            "data": rows,
            "total": len(rows),
            "limit": limit,
            "offset": offset,
        }

    except Exception as exc:
        db.rollback()

        print(
            "Failed to fetch closed settlements:",
            str(exc),
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to fetch closed settlements: "
                f"{str(exc)}"
            ),
        )