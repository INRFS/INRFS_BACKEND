from typing import Any, Dict, List

from sqlalchemy import text
from sqlalchemy.orm import Session


def _row_to_dict(row) -> Dict[str, Any]:
    try:
        return dict(row._mapping)
    except Exception:
        return dict(row)


def _clean_value(value):
    if hasattr(value, "isoformat"):
        return value.isoformat()

    if hasattr(value, "as_tuple"):
        return float(value)

    return value


def _clean_row(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        str(key): _clean_value(value)
        for key, value in row.items()
    }


def _execute_function(
    db: Session,
    query: str,
    params: Dict[str, Any] | None = None,
) -> List[Dict[str, Any]]:
    result = db.execute(
        text(query),
        params or {},
    )

    return [
        _clean_row(_row_to_dict(row))
        for row in result.fetchall()
    ]


def _execute_one(
    db: Session,
    query: str,
    params: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    result = db.execute(
        text(query),
        params or {},
    )

    row = result.fetchone()

    if not row:
        return {}

    return _clean_row(_row_to_dict(row))


def get_admin_report_summary(
    db: Session,
) -> Dict[str, Any]:
    rows = _execute_function(
        db,
        """
        SELECT *
        FROM fn_get_admin_dashboard_summary()
        """,
    )

    if not rows:
        return {
            "total_investors": 0,
            "pending_kyc": 0,
            "active_investments": 0,
            "total_aum": 0,
            "monthly_interest_due": 0,
            "pending_approvals": 0,
            "closed_investments": 0,
            "branch_count": 0,
        }

    row = rows[0]

    def find_value(
        names,
        default=0,
    ):
        for name in names:
            if name in row:
                return row[name]

        lower_map = {
            str(key).lower(): value
            for key, value in row.items()
        }

        for name in names:
            if name.lower() in lower_map:
                return lower_map[name.lower()]

        return default

    return {
        "total_investors": find_value(
            [
                "total_investors",
                "investor_count",
                "investors",
            ]
        ),
        "pending_kyc": find_value(
            [
                "pending_kyc",
                "pending_kyc_count",
                "kyc_pending",
            ]
        ),
        "active_investments": find_value(
            [
                "active_investments",
                "active_investment_count",
            ]
        ),
        "total_aum": find_value(
            [
                "total_aum",
                "aum",
                "total_investment_amount",
            ]
        ),
        "monthly_interest_due": find_value(
            [
                "monthly_interest_due",
                "interest_due",
                "monthly_interest",
            ]
        ),
        "pending_approvals": find_value(
            [
                "pending_approvals",
                "pending_investments",
                "pending_investment_count",
            ]
        ),
        "closed_investments": find_value(
            [
                "closed_investments",
                "closed_investment_count",
            ]
        ),
        "branch_count": find_value(
            [
                "branch_count",
                "branches",
                "active_branches",
            ]
        ),
    }


def get_monthly_investment_trend(
    db: Session,
) -> List[Dict[str, Any]]:
    rows = _execute_function(
        db,
        """
        SELECT *
        FROM fn_get_admin_monthly_investment_trend()
        """,
    )

    result = []

    for row in rows:
        result.append({
            "month": (
                row.get("month")
                or row.get("month_name")
                or row.get("period")
                or ""
            ),
            "invested": (
                row.get("invested")
                or row.get("investment_amount")
                or row.get("total_invested")
                or row.get("amount")
                or 0
            ),
            "interest": (
                row.get("interest")
                or row.get("interest_amount")
                or row.get("total_interest")
                or 0
            ),
            "count": (
                row.get("count")
                or row.get("investment_count")
                or row.get("total_investments")
                or 0
            ),
        })

    return result


def get_investor_growth(
    db: Session,
) -> List[Dict[str, Any]]:
    rows = _execute_function(
        db,
        """
        SELECT *
        FROM fn_get_admin_investor_growth()
        """,
    )

    result = []

    for row in rows:
        result.append({
            "month": (
                row.get("month")
                or row.get("month_name")
                or row.get("period")
                or ""
            ),
            "count": (
                row.get("count")
                or row.get("investor_count")
                or row.get("total_investors")
                or 0
            ),
        })

    return result


def get_investment_status_distribution(
    db: Session,
) -> List[Dict[str, Any]]:
    rows = _execute_function(
        db,
        """
        SELECT
            s.status_name,
            COUNT(i.id) AS investment_count,
            COALESCE(
                SUM(i.investment_amount),
                0
            ) AS total_amount
        FROM tn_investment i
        LEFT JOIN master_investment_status s
            ON s.id = i.investment_status_id
        GROUP BY
            s.id,
            s.status_name
        ORDER BY
            s.id
        """,
    )

    return [
        {
            "status": (
                row.get("status_name")
                or "Unknown"
            ),
            "count": row.get(
                "investment_count",
                0,
            ),
            "amount": row.get(
                "total_amount",
                0,
            ),
        }
        for row in rows
    ]


def get_recent_investments(
    db: Session,
    limit: int = 10,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    rows = _execute_function(
        db,
        """
        SELECT *
        FROM fn_admin_get_all_investments(
            :p_bond_id,
            :p_limit,
            :p_offset
        )
        """,
        {
            "p_bond_id": None,
            "p_limit": limit,
            "p_offset": offset,
        },
    )

    return rows


def get_admin_report_dashboard(
    db: Session,
) -> Dict[str, Any]:
    summary = get_admin_report_summary(db)

    monthly = get_monthly_investment_trend(db)

    investor_growth = get_investor_growth(db)

    status_distribution = (
        get_investment_status_distribution(db)
    )

    recent_investments = get_recent_investments(
        db=db,
        limit=10,
        offset=0,
    )

    return {
        "summary": summary,
        "monthly_investments": monthly,
        "investor_growth": investor_growth,
        "status_distribution": status_distribution,
        "recent_investments": recent_investments,
    }