from typing import Any, Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session


def _row_to_dict(row) -> Dict[str, Any]:
    if row is None:
        return {}

    try:
        return dict(row._mapping)
    except Exception:
        return dict(row)


def _clean_value(value):
    if value is None:
        return None

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


def _execute_all(
    db: Session,
    query: str,
    params: Optional[Dict[str, Any]] = None,
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
    params: Optional[Dict[str, Any]] = None,
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
    branch_id: Optional[int] = None,
) -> Dict[str, Any]:

    params = {}

    branch_filter = ""

    if branch_id is not None:
        branch_filter = """
            AND r.branch_id = :p_branch_id
        """

        params["p_branch_id"] = branch_id

    row = _execute_one(
        db,
        f"""
        SELECT

            COUNT(
                DISTINCT i.investor_registration_id
            ) AS total_investors,

            COUNT(
                CASE
                    WHEN LOWER(
                        COALESCE(s.status_name, '')
                    ) = 'pending'
                    THEN 1
                END
            ) AS pending_approvals,

            COUNT(
                CASE
                    WHEN LOWER(
                        COALESCE(s.status_name, '')
                    ) IN (
                        'approved',
                        'active'
                    )
                    THEN 1
                END
            ) AS active_investments,

            COALESCE(
                SUM(
                    CASE
                        WHEN LOWER(
                            COALESCE(
                                s.status_name,
                                ''
                            )
                        ) IN (
                            'approved',
                            'active'
                        )
                        THEN COALESCE(
                            i.investment_amount,
                            0
                        )
                        ELSE 0
                    END
                ),
                0
            ) AS total_aum,

            COUNT(
                CASE
                    WHEN LOWER(
                        COALESCE(
                            s.status_name,
                            ''
                        )
                    ) IN (
                        'closed',
                        'completed'
                    )
                    THEN 1
                END
            ) AS closed_investments

        FROM public.tn_investment i

        INNER JOIN public.tn_investor_registration r
            ON r.id = i.investor_registration_id

        LEFT JOIN public.master_investment_status s
            ON s.id = i.investment_status_id

        WHERE 1 = 1

        {branch_filter}
        """,
        params,
    )

    if not row:
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

    interest_params = {}

    interest_branch_filter = ""

    if branch_id is not None:
        interest_branch_filter = """
            AND r2.branch_id = :p_branch_id
        """

        interest_params["p_branch_id"] = branch_id

    interest_row = _execute_one(
        db,
        f"""
        SELECT
            COALESCE(
                SUM(
                    COALESCE(
                        ins.net_interest_amount,
                        0
                    )
                ),
                0
            ) AS monthly_interest_due

        FROM public.tn_interest_schedule ins

        INNER JOIN public.tn_investment i2
            ON i2.id = ins.investment_id

        INNER JOIN public.tn_investor_registration r2
            ON r2.id = i2.investor_registration_id

        WHERE ins.interest_due_date >= CURRENT_DATE

        {interest_branch_filter}
        """,
        interest_params,
    )

    branch_params = {}

    branch_count_filter = ""

    if branch_id is not None:
        branch_count_filter = """
            WHERE id = :p_branch_id
        """

        branch_params["p_branch_id"] = branch_id

    branch_row = _execute_one(
        db,
        f"""
        SELECT COUNT(*) AS branch_count
        FROM public.master_branch
        {branch_count_filter}
        """,
        branch_params,
    )

    return {
        "total_investors": row.get(
            "total_investors",
            0,
        ),
        "pending_kyc": 0,
        "active_investments": row.get(
            "active_investments",
            0,
        ),
        "total_aum": row.get(
            "total_aum",
            0,
        ),
        "monthly_interest_due": interest_row.get(
            "monthly_interest_due",
            0,
        ),
        "pending_approvals": row.get(
            "pending_approvals",
            0,
        ),
        "closed_investments": row.get(
            "closed_investments",
            0,
        ),
        "branch_count": branch_row.get(
            "branch_count",
            0,
        ),
    }


def get_monthly_investment_trend(
    db: Session,
    branch_id: Optional[int] = None,
) -> List[Dict[str, Any]]:

    params = {}

    branch_filter = ""

    if branch_id is not None:
        branch_filter = """
            AND r.branch_id = :p_branch_id
        """

        params["p_branch_id"] = branch_id

    rows = _execute_all(
        db,
        f"""
        SELECT

            TO_CHAR(
                DATE_TRUNC(
                    'month',
                    i.investment_date
                ),
                'Mon YYYY'
            ) AS month,

            COALESCE(
                SUM(i.investment_amount),
                0
            ) AS invested,

            COUNT(i.id) AS count

        FROM public.tn_investment i

        INNER JOIN public.tn_investor_registration r
            ON r.id = i.investor_registration_id

        WHERE i.investment_date IS NOT NULL

        {branch_filter}

        GROUP BY
            DATE_TRUNC(
                'month',
                i.investment_date
            )

        ORDER BY
            DATE_TRUNC(
                'month',
                i.investment_date
            )
        """,
        params,
    )

    return rows


def get_investor_growth(
    db: Session,
    branch_id: Optional[int] = None,
) -> List[Dict[str, Any]]:

    params = {}

    branch_filter = ""

    if branch_id is not None:
        branch_filter = """
            AND r.branch_id = :p_branch_id
        """

        params["p_branch_id"] = branch_id

    rows = _execute_all(
        db,
        f"""
        SELECT

            TO_CHAR(
                DATE_TRUNC(
                    'month',
                    r.created_date
                ),
                'Mon YYYY'
            ) AS month,

            COUNT(*) AS count

        FROM public.tn_investor_registration r

        WHERE r.created_date IS NOT NULL

        {branch_filter}

        GROUP BY
            DATE_TRUNC(
                'month',
                r.created_date
            )

        ORDER BY
            DATE_TRUNC(
                'month',
                r.created_date
            )
        """,
        params,
    )

    return rows


def get_investment_status_distribution(
    db: Session,
    branch_id: Optional[int] = None,
) -> List[Dict[str, Any]]:

    params = {}

    branch_filter = ""

    if branch_id is not None:
        branch_filter = """
            AND r.branch_id = :p_branch_id
        """

        params["p_branch_id"] = branch_id

    rows = _execute_all(
        db,
        f"""
        SELECT

            COALESCE(
                s.status_name,
                'Unknown'
            ) AS status,

            COUNT(i.id) AS count,

            COALESCE(
                SUM(
                    i.investment_amount
                ),
                0
            ) AS amount

        FROM public.tn_investment i

        INNER JOIN public.tn_investor_registration r
            ON r.id = i.investor_registration_id

        LEFT JOIN public.master_investment_status s
            ON s.id = i.investment_status_id

        WHERE 1 = 1

        {branch_filter}

        GROUP BY
            s.id,
            s.status_name

        ORDER BY
            s.id
        """,
        params,
    )

    return rows


def get_recent_investments(
    db: Session,
    branch_id: Optional[int] = None,
    limit: int = 10,
    offset: int = 0,
) -> List[Dict[str, Any]]:

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
            "p_bond_id": None,
            "p_limit": limit,
            "p_offset": offset,
        },
    )

    return [
        _clean_row(
            _row_to_dict(row)
        )
        for row in result.fetchall()
    ]


def get_admin_report_dashboard(
    db: Session,
    branch_id: Optional[int] = None,
) -> Dict[str, Any]:

    summary = get_admin_report_summary(
        db=db,
        branch_id=branch_id,
    )

    monthly = get_monthly_investment_trend(
        db=db,
        branch_id=branch_id,
    )

    investor_growth = get_investor_growth(
        db=db,
        branch_id=branch_id,
    )

    status_distribution = (
        get_investment_status_distribution(
            db=db,
            branch_id=branch_id,
        )
    )

    recent_investments = get_recent_investments(
        db=db,
        branch_id=branch_id,
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