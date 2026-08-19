from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session


def _rows(result) -> List[Dict[str, Any]]:
    return [dict(row._mapping) for row in result]


def _row(result) -> Optional[Dict[str, Any]]:
    row = result.first()
    return dict(row._mapping) if row else None


def get_all_investments(
    db: Session,
    branch_id: Optional[int] = None,
    bond_id: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
):
    result = db.execute(
        text(
            """
            SELECT *
            FROM public.fn_admin_get_all_investments(
                CAST(:p_branch_id AS INTEGER),
                CAST(:p_bond_id AS VARCHAR),
                CAST(:p_limit AS INTEGER),
                CAST(:p_offset AS INTEGER)
            )
            """
        ),
        {
            "p_branch_id": branch_id,
            "p_bond_id": bond_id,
            "p_limit": limit,
            "p_offset": offset,
        },
    )

    data = _rows(result)

    return {
        "success": True,
        "data": data,
        "total": len(data),
    }


def get_pending_investments(
    db: Session,
    branch_id: Optional[int] = None,
    limit: int = 20,
    offset: int = 0,
):
    result = db.execute(
        text(
            """
            SELECT *
            FROM public.fn_admin_get_pending_investments(
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

    data = _rows(result)

    return {
        "success": True,
        "data": data,
        "total": len(data),
    }


def get_investment_details(
    db: Session,
    investment_id: str,
):
    result = db.execute(
        text(
            """
            SELECT *
            FROM public.fn_admin_get_investment_details(
                :p_investment_id
            )
            """
        ),
        {
            "p_investment_id": investment_id,
        },
    )

    data = _row(result)

    if not data:
        return {
            "success": False,
            "data": None,
        }

    return {
        "success": True,
        "data": data,
    }


def get_investment_bond_details(
    db: Session,
    investment_id: str,
):
    result = db.execute(
        text(
            """
            SELECT *
            FROM public.fn_admin_get_investment_bond_details(
                :p_investment_id
            )
            """
        ),
        {
            "p_investment_id": investment_id,
        },
    )

    data = _row(result)

    if not data:
        return {
            "success": False,
            "data": None,
        }

    return {
        "success": True,
        "data": data,
    }


def approve_investment(
    db: Session,
    investment_id: str,
    interest_rate: Decimal,
    approved_by: int,
    remarks: Optional[str] = None,
):
    investment = db.execute(
        text(
            """
            SELECT id
            FROM tn_investment
            WHERE investment_id = :investment_id
            LIMIT 1
            """
        ),
        {
            "investment_id": investment_id,
        },
    ).first()

    if not investment:
        raise ValueError(
            f"Investment {investment_id} not found"
        )

    numeric_investment_id = investment.id

    try:
        result = db.execute(
            text(
                """
                SELECT *
                FROM fn_approve_investment(
                    :p_id,
                    :p_interest_rate,
                    :p_approved_by,
                    :p_remarks
                )
                """
            ),
            {
                "p_id": numeric_investment_id,
                "p_interest_rate": interest_rate,
                "p_approved_by": approved_by,
                "p_remarks": remarks,
            },
        )

        function_data = _row(result)

        db.execute(
            text(
                """
                UPDATE tn_investment
                SET
                    investment_status_id = 2,
                    interest_rate = :interest_rate,
                    approved_by = :approved_by,
                    approved_date = CURRENT_TIMESTAMP,
                    remarks = :remarks
                WHERE investment_id = :investment_id
                """
            ),
            {
                "investment_id": investment_id,
                "interest_rate": interest_rate,
                "approved_by": approved_by,
                "remarks": remarks,
            },
        )

        existing_bond = db.execute(
            text(
                """
                SELECT id, bond_id
                FROM tn_bond
                WHERE investment_id = :investment_id
                LIMIT 1
                """
            ),
            {
                "investment_id": numeric_investment_id,
            },
        ).first()

        if not existing_bond:
            next_bond_id = db.execute(
                text(
                    """
                    SELECT nextval(
                        pg_get_serial_sequence(
                            'tn_bond',
                            'id'
                        )
                    ) AS id
                    """
                )
            ).scalar()

            bond_number = f"BOND{int(next_bond_id):06d}"

            db.execute(
                text(
                    """
                    INSERT INTO tn_bond (
                        id,
                        bond_id,
                        investment_id,
                        maturity_date,
                        issue_date,
                        remarks,
                        created_by,
                        created_date,
                        modified_by,
                        modified_date
                    )
                    SELECT
                        :id,
                        :bond_id,
                        id,
                        maturity_date,
                        CURRENT_TIMESTAMP,
                        :bond_remarks,
                        :created_by,
                        CURRENT_TIMESTAMP,
                        :modified_by,
                        CURRENT_TIMESTAMP
                    FROM tn_investment
                    WHERE id = :investment_pk
                    """
                ),
                {
                    "id": int(next_bond_id),
                    "bond_id": bond_number,
                    "bond_remarks": "Bond generated on investment approval",
                    "created_by": approved_by,
                    "modified_by": approved_by,
                    "investment_pk": numeric_investment_id,
                },
            )

        db.commit()

        fresh_status = db.execute(
            text(
                """
                SELECT
                    investment_id,
                    investment_status_id,
                    approved_by,
                    approved_date,
                    interest_rate,
                    remarks
                FROM tn_investment
                WHERE investment_id = :investment_id
                LIMIT 1
                """
            ),
            {
                "investment_id": investment_id,
            },
        ).first()

        fresh_data = (
            dict(fresh_status._mapping)
            if fresh_status
            else {}
        )

        if function_data:
            function_data.update(fresh_data)
            data = function_data
        else:
            data = fresh_data

        return {
            "success": True,
            "message": "Investment approved successfully",
            "data": data,
        }

    except Exception:
        db.rollback()
        raise


def reject_investment(
    db: Session,
    investment_id: str,
    rejected_by: int,
    rejection_reason: str,
    remarks: Optional[str] = None,
):
    investment = db.execute(
        text(
            """
            SELECT id
            FROM tn_investment
            WHERE investment_id = :investment_id
            LIMIT 1
            """
        ),
        {
            "investment_id": investment_id,
        },
    ).first()

    if not investment:
        raise ValueError(
            f"Investment {investment_id} not found"
        )

    numeric_investment_id = investment.id

    try:
        result = db.execute(
            text(
                """
                SELECT *
                FROM fn_admin_reject_investment(
                    :p_investment_id,
                    :p_rejected_by,
                    :p_rejection_reason,
                    :p_remarks
                )
                """
            ),
            {
                "p_investment_id": numeric_investment_id,
                "p_rejected_by": rejected_by,
                "p_rejection_reason": rejection_reason,
                "p_remarks": remarks,
            },
        )

        function_data = _row(result)

        db.execute(
            text(
                """
                UPDATE tn_investment
                SET
                    investment_status_id = 4,
                    approved_by = :rejected_by,
                    approved_date = CURRENT_TIMESTAMP,
                    remarks = :remarks
                WHERE investment_id = :investment_id
                """
            ),
            {
                "investment_id": investment_id,
                "rejected_by": rejected_by,
                "remarks": (
                    f"{remarks}\n"
                    f"Rejection reason: {rejection_reason}"
                    if remarks
                    else f"Rejection reason: {rejection_reason}"
                ),
            },
        )

        db.commit()

        fresh_status = db.execute(
            text(
                """
                SELECT
                    investment_id,
                    investment_status_id,
                    approved_by,
                    approved_date,
                    remarks
                FROM tn_investment
                WHERE investment_id = :investment_id
                LIMIT 1
                """
            ),
            {
                "investment_id": investment_id,
            },
        ).first()

        fresh_data = (
            dict(fresh_status._mapping)
            if fresh_status
            else {}
        )

        if function_data:
            function_data.update(fresh_data)
            data = function_data
        else:
            data = fresh_data

        return {
            "success": True,
            "message": "Investment rejected successfully",
            "data": data,
        }

    except Exception:
        db.rollback()
        raise


def get_pending_tenure_extensions(
    db: Session,
    branch_id: Optional[int] = None,
    limit: int = 20,
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

    data = _rows(result)

    return {
        "success": True,
        "data": data,
        "total": len(data),
    }


def get_tenure_extension_details(
    db: Session,
    request_id: int,
):
    result = db.execute(
        text(
            """
            SELECT *
            FROM fn_admin_get_tenure_extension_details(
                :p_request_id
            )
            """
        ),
        {
            "p_request_id": request_id,
        },
    )

    data = _row(result)

    if not data:
        return {
            "success": False,
            "data": None,
        }

    return {
        "success": True,
        "data": data,
    }


def approve_tenure_extension(
    db: Session,
    request_id: int,
    approved_by: int,
    remarks: Optional[str] = None,
):
    result = db.execute(
        text(
            """
            SELECT *
            FROM fn_admin_approve_tenure_extension(
                :p_request_id,
                :p_approved_by,
                :p_remarks
            )
            """
        ),
        {
            "p_request_id": request_id,
            "p_approved_by": approved_by,
            "p_remarks": remarks,
        },
    )

    data = _row(result)

    db.commit()

    return {
        "success": True,
        "message": "Tenure extension approved successfully",
        "data": data,
    }


def reject_tenure_extension(
    db: Session,
    request_id: int,
    rejected_by: int,
    remarks: Optional[str] = None,
):
    result = db.execute(
        text(
            """
            SELECT *
            FROM fn_admin_reject_tenure_extension(
                :p_request_id,
                :p_rejected_by,
                :p_remarks
            )
            """
        ),
        {
            "p_request_id": request_id,
            "p_rejected_by": rejected_by,
            "p_remarks": remarks,
        },
    )

    data = _row(result)

    db.commit()

    return {
        "success": True,
        "message": "Tenure extension rejected successfully",
        "data": data,
    }


def get_monthly_interest(
    db: Session,
    branch_id: Optional[int] = None,
    interest_due_date: Optional[date] = None,
    limit: int = 20,
    offset: int = 0,
):
    result = db.execute(
        text(
            """
            SELECT *
            FROM public.fn_admin_get_monthly_interest(
                CAST(:p_branch_id AS INTEGER),
                CAST(:p_interest_due_date AS DATE),
                CAST(:p_limit AS INTEGER),
                CAST(:p_offset AS INTEGER)
            )
            """
        ),
        {
            "p_branch_id": branch_id,
            "p_interest_due_date": interest_due_date,
            "p_limit": limit,
            "p_offset": offset,
        },
    )

    data = _rows(result)

    return {
        "success": True,
        "data": data,
        "total": len(data),
    }


def get_monthly_interest_details(
    db: Session,
    interest_schedule_id: int,
):
    result = db.execute(
        text(
            """
            SELECT *
            FROM fn_admin_get_monthly_interest_details(
                :p_interest_schedule_id
            )
            """
        ),
        {
            "p_interest_schedule_id": interest_schedule_id,
        },
    )

    data = _row(result)

    if not data:
        return {
            "success": False,
            "data": None,
        }

    return {
        "success": True,
        "data": data,
    }


def approve_monthly_interest(
    db: Session,
    interest_schedule_id: int,
    approved_by: int,
):
    result = db.execute(
        text(
            """
            SELECT *
            FROM fn_admin_approve_monthly_interest(
                :p_interest_schedule_id,
                :p_approved_by
            )
            """
        ),
        {
            "p_interest_schedule_id": interest_schedule_id,
            "p_approved_by": approved_by,
        },
    )

    data = _row(result)

    db.commit()

    return {
        "success": True,
        "message": "Monthly interest approved successfully",
        "data": data,
    }


def reject_monthly_interest(
    db: Session,
    interest_schedule_id: int,
    rejected_by: int,
    rejection_reason: str,
    remarks: Optional[str] = None,
):
    result = db.execute(
        text(
            """
            SELECT *
            FROM fn_admin_reject_monthly_interest(
                :p_interest_schedule_id,
                :p_rejected_by,
                :p_rejection_reason,
                :p_remarks
            )
            """
        ),
        {
            "p_interest_schedule_id": interest_schedule_id,
            "p_rejected_by": rejected_by,
            "p_rejection_reason": rejection_reason,
            "p_remarks": remarks,
        },
    )

    data = _row(result)

    db.commit()

    return {
        "success": True,
        "message": "Monthly interest rejected successfully",
        "data": data,
    }


def approve_all_monthly_interest(
    db: Session,
    approved_by: int,
    interest_due_date: date,
):
    result = db.execute(
        text(
            """
            SELECT *
            FROM fn_admin_approve_all_monthly_interest(
                :p_approved_by,
                :p_interest_due_date
            )
            """
        ),
        {
            "p_approved_by": approved_by,
            "p_interest_due_date": interest_due_date,
        },
    )

    data = _rows(result)

    db.commit()

    return {
        "success": True,
        "message": "Monthly interest approved successfully",
        "data": data,
    }


def create_tenure_timeout_settlement(
    db: Session,
    investment_id: int,
    created_by: int,
):
    result = db.execute(
        text(
            """
            SELECT *
            FROM fn_create_tenure_timeout_settlement(
                :p_investment_id,
                :p_created_by
            )
            """
        ),
        {
            "p_investment_id": investment_id,
            "p_created_by": created_by,
        },
    )

    data = _row(result)

    db.commit()

    return {
        "success": True,
        "message": "Tenure timeout settlement created successfully",
        "data": data,
    }