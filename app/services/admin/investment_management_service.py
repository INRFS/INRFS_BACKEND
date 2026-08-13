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
    bond_id: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
):
    result = db.execute(
        text(
            """
            SELECT *
            FROM fn_admin_get_all_investments(
                :p_bond_id,
                :p_limit,
                :p_offset
            )
            """
        ),
        {
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
    limit: int = 20,
    offset: int = 0,
):
    result = db.execute(
        text(
            """
            SELECT *
            FROM fn_admin_get_pending_investments(
                :p_limit,
                :p_offset
            )
            """
        ),
        {
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
            FROM fn_admin_get_investment_details(
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
            FROM fn_admin_get_investment_bond_details(
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
    limit: int = 20,
    offset: int = 0,
):
    result = db.execute(
        text(
            """
            SELECT *
            FROM fn_admin_get_pending_tenure_extensions(
                :p_limit,
                :p_offset
            )
            """
        ),
        {
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
    interest_due_date: Optional[date] = None,
    limit: int = 20,
    offset: int = 0,
):
    result = db.execute(
        text(
            """
            SELECT *
            FROM fn_admin_get_monthly_interest(
                :p_interest_due_date,
                :p_limit,
                :p_offset
            )
            """
        ),
        {
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
    try:
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

        settlement_data = _row(result) or {}

        investment_result = db.execute(
            text(
                """
                SELECT *
                FROM fn_admin_get_investment_details(
                    :p_investment_id
                )
                """
            ),
            {
                "p_investment_id": investment_id,
            },
        )

        investment_data = _row(investment_result) or {}

        investment_id_value = (
            investment_data.get("investment_id")
            or investment_data.get("investment_code")
            or settlement_data.get("investment_id")
        )

        bond_result = None

        if investment_id_value:
            bond_result = db.execute(
                text(
                    """
                    SELECT *
                    FROM fn_admin_get_investment_bond_details(
                        :p_investment_id
                    )
                    """
                ),
                {
                    "p_investment_id": str(investment_id_value),
                },
            )

        bond_data = _row(bond_result) if bond_result else {}

        merged = {}
        merged.update(investment_data)
        merged.update(bond_data or {})
        merged.update(settlement_data)

        def first_value(*keys, default=None):
            for key in keys:
                value = merged.get(key)
                if value is not None and value != "":
                    return value
            return default

        principal = first_value(
            "principal",
            "principal_amount",
            "investment_amount",
            "amount",
            "invested_amount",
            "investment_value",
            default=0,
        )

        interest_earned = first_value(
            "interest_earned",
            "interestEarned",
            "total_interest",
            "interest_amount",
            "earned_interest",
            "expected_interest_amount",
            default=0,
        )

        investor_name = first_value(
            "investor_name",
            "investorName",
            "full_name",
            "investor_full_name",
            "name",
            "investor",
            default="-",
        )

        investor_id = first_value(
            "investor_id",
            "investor_registration_id",
            "investor_registration_number",
            "investor_code",
            "registration_id",
            default="-",
        )

        branch_name = first_value(
            "branch_name",
            "branchName",
            "branch",
            "branch_name_text",
            "service_location_name",
            "location_name",
            default="-",
        )

        bond_number = first_value(
            "bond_number",
            "bondNumber",
            "bond_id",
            "bond",
            "bond_code",
            default="-",
        )

        matured_on = first_value(
            "matured_on",
            "maturity_date",
            "maturityDate",
            "mature_date",
            default=None,
        )

        investment_date = first_value(
            "investment_date",
            "invested_on",
            "investmentDate",
            default=None,
        )

        try:
            principal_decimal = Decimal(str(principal or 0))
        except Exception:
            principal_decimal = Decimal("0")

        try:
            interest_decimal = Decimal(str(interest_earned or 0))
        except Exception:
            interest_decimal = Decimal("0")

        gst_amount = (
            interest_decimal * Decimal("0.18")
        ).quantize(Decimal("0.01"))

        net_settlement_amount = (
            principal_decimal
            + interest_decimal
            - gst_amount
        ).quantize(Decimal("0.01"))

        merged.update(
            {
                "investment_id": investment_id_value
                or str(investment_id),
                "investor_name": investor_name,
                "investor_id": investor_id,
                "branch_name": branch_name,
                "bond_number": bond_number,
                "matured_on": matured_on,
                "investment_date": investment_date,
                "principal": principal_decimal,
                "principal_amount": principal_decimal,
                "investment_amount": principal_decimal,
                "interest_earned": interest_decimal,
                "total_interest": interest_decimal,
                "gst": gst_amount,
                "gst_amount": gst_amount,
                "net_settlement_amount": net_settlement_amount,
                "net_settlement": net_settlement_amount,
            }
        )

        db.commit()

        return {
            "success": True,
            "message": "Tenure timeout settlement created successfully",
            "data": merged,
        }

    except Exception:
        db.rollback()
        raise

    
def get_dashboard_summary(
    db: Session,
):
    result = db.execute(
        text(
            """
            SELECT *
            FROM fn_get_admin_dashboard_summary()
            """
        )
    )

    data = _row(result)

    return {
        "success": True,
        "data": data,
    }


def get_investor_growth(
    db: Session,
):
    result = db.execute(
        text(
            """
            SELECT *
            FROM fn_get_admin_investor_growth()
            """
        )
    )

    data = _rows(result)

    return {
        "success": True,
        "data": data,
    }


def get_monthly_investment_trend(
    db: Session,
):
    result = db.execute(
        text(
            """
            SELECT *
            FROM fn_get_admin_monthly_investment_trend()
            """
        )
    )

    data = _rows(result)

    return {
        "success": True,
        "data": data,
    }