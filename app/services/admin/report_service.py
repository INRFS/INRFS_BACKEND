from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session


def _rows(result):
    return [
        dict(row._mapping)
        for row in result.fetchall()
    ]


def _row(result):
    row = result.fetchone()

    return (
        dict(row._mapping)
        if row
        else {}
    )


def get_admin_report_summary(
    db: Session,
    year: int,
    branch_id: int,
):
    result = db.execute(
        text(
            """
            SELECT

                COALESCE(
                    SUM(
                        CASE
                            WHEN i.investment_status_id IN (2, 3)
                            THEN i.investment_amount
                            ELSE 0
                        END
                    ),
                    0
                ) AS new_investments,

                COALESCE(
                    (
                        SELECT SUM(
                            ins.net_interest_amount
                        )
                        FROM public.tn_interest_schedule ins

                        JOIN public.tn_investment ii
                            ON ii.id = ins.investment_id

                        JOIN public.tn_investor_registration ir2
                            ON ir2.id =
                               ii.investment_registration_id

                        WHERE ir2.branch_id = :branch_id

                        AND ins.interest_paid_date IS NOT NULL

                        AND EXTRACT(
                            YEAR FROM ins.interest_paid_date
                        ) = :year
                    ),
                    0
                ) AS interest_paid,

                COALESCE(
                    (
                        SELECT SUM(
                            s.net_settlement_amount
                        )
                        FROM public.tn_settlement s

                        JOIN public.tn_investment si
                            ON si.id = s.investment_id

                        JOIN public.tn_investor_registration ir3
                            ON ir3.id =
                               si.investment_registration_id

                        WHERE ir3.branch_id = :branch_id

                        AND s.settlement_status_id = 4

                        AND s.paid_date IS NOT NULL

                        AND EXTRACT(
                            YEAR FROM s.paid_date
                        ) = :year
                    ),
                    0
                ) AS settlements

            FROM public.tn_investment i

            JOIN public.tn_investor_registration ir
                ON ir.id =
                   i.investment_registration_id

            WHERE ir.branch_id = :branch_id

            AND i.investment_status_id IN (2, 3)

            AND EXTRACT(
                YEAR FROM i.investment_date
            ) = :year
            """
        ),
        {
            "year": year,
            "branch_id": branch_id,
        },
    )

    data = _row(result)

    return {
        "new_investments": float(
            data.get("new_investments") or 0
        ),
        "interest_paid": float(
            data.get("interest_paid") or 0
        ),
        "settlements": float(
            data.get("settlements") or 0
        ),
    }


def get_monthly_investment_trend(
    db: Session,
    year: int,
    branch_id: int,
):
    result = db.execute(
        text(
            """
            SELECT
                EXTRACT(
                    MONTH FROM i.investment_date
                )::integer AS month_number,

                TO_CHAR(
                    DATE_TRUNC(
                        'month',
                        i.investment_date
                    ),
                    'Mon'
                ) AS month_name,

                COALESCE(
                    SUM(i.investment_amount),
                    0
                ) AS invested_amount,

                0::numeric AS interest_paid

            FROM public.tn_investment i

            JOIN public.tn_investor_registration ir
                ON ir.id =
                   i.investment_registration_id

            WHERE ir.branch_id = :branch_id

            AND EXTRACT(
                YEAR FROM i.investment_date
            ) = :year

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
            """
        ),
        {
            "year": year,
            "branch_id": branch_id,
        },
    )

    rows = _rows(result)

    return [
        {
            "month_number": int(
                row.get("month_number") or 0
            ),
            "month_name": row.get(
                "month_name"
            ),
            "invested_amount": float(
                row.get("invested_amount") or 0
            ),
            "interest_paid": float(
                row.get("interest_paid") or 0
            ),
        }
        for row in rows
    ]

def get_investor_growth(
    db: Session,
    year: int,
    branch_id: int,
):
    result = db.execute(
        text(
            """
            SELECT
                EXTRACT(
                    MONTH FROM month_date
                )::integer AS month_number,

                TO_CHAR(
                    month_date,
                    'Mon'
                ) AS month_name,

                investor_count

            FROM (
                SELECT
                    DATE_TRUNC(
                        'month',
                        ir.created_date
                    ) AS month_date,

                    COUNT(
                        DISTINCT ir.id
                    ) AS investor_count

                FROM public.tn_investor_registration ir

                WHERE ir.branch_id = :branch_id

                AND EXTRACT(
                    YEAR FROM ir.created_date
                ) = :year

                GROUP BY
                    DATE_TRUNC(
                        'month',
                        ir.created_date
                    )
            ) monthly

            ORDER BY
                month_date
            """
        ),
        {
            "branch_id": branch_id,
            "year": year,
        },
    )

    return [
        {
            "month_number": row.month_number,
            "month_name": row.month_name,
            "investor_count": int(
                row.investor_count or 0
            ),
        }
        for row in result
    ]

def get_investment_status_distribution(
    db: Session,
    year: int,
    branch_id: int,
):
    result = db.execute(
        text(
            """
            SELECT

                mis.id AS status_id,

                mis.status_name,

                COUNT(i.id)
                    AS investment_count,

                COALESCE(
                    SUM(i.investment_amount),
                    0
                ) AS investment_amount

            FROM public.master_investment_status mis

            LEFT JOIN public.tn_investment i
                ON i.investment_status_id =
                   mis.id

                AND EXTRACT(
                    YEAR FROM i.investment_date
                ) = :year

            LEFT JOIN public.tn_investor_registration ir
                ON ir.id =
                   i.investment_registration_id

                AND ir.branch_id =
                    :branch_id

            WHERE mis.is_active = TRUE

            GROUP BY
                mis.id,
                mis.status_name

            ORDER BY
                mis.id
            """
        ),
        {
            "year": year,
            "branch_id": branch_id,
        },
    )

    rows = _rows(result)

    return [
        {
            "status_id": int(
                row.get("status_id") or 0
            ),
            "status_name": row.get(
                "status_name"
            ),
            "investment_count": int(
                row.get("investment_count") or 0
            ),
            "investment_amount": float(
                row.get("investment_amount") or 0
            ),
        }
        for row in rows
    ]


def get_recent_investments(
    db: Session,
    branch_id: int,
    limit: int = 10,
    offset: int = 0,
):
    result = db.execute(
        text(
            """
            SELECT *
            FROM public.fn_admin_get_all_investments(
                :branch_id,
                NULL,
                :limit,
                :offset
            )
            """
        ),
        {
            "branch_id": branch_id,
            "limit": limit,
            "offset": offset,
        },
    )

    return _rows(result)


def get_pending_investments(
    db: Session,
    branch_id: int,
    limit: int = 10,
    offset: int = 0,
):
    result = db.execute(
        text(
            """
            SELECT *
            FROM public.fn_admin_get_pending_investments(
                :limit,
                :offset,
                :branch_id
            )
            """
        ),
        {
            "limit": limit,
            "offset": offset,
            "branch_id": branch_id,
        },
    )

    return _rows(result)


def get_admin_report_dashboard(
    db: Session,
    year: int,
    branch_id: int,
):
    summary = get_admin_report_summary(
        db=db,
        year=year,
        branch_id=branch_id,
    )

    monthly_investments = (
        get_monthly_investment_trend(
            db=db,
            year=year,
            branch_id=branch_id,
        )
    )

    investor_growth = get_investor_growth(
        db=db,
        year=year,
        branch_id=branch_id,
    )

    status_distribution = (
        get_investment_status_distribution(
            db=db,
            year=year,
            branch_id=branch_id,
        )
    )

    recent_investments = (
        get_recent_investments(
            db=db,
            branch_id=branch_id,
            limit=10,
            offset=0,
        )
    )

    return {
        "summary": summary,
        "monthly_investments": monthly_investments,
        "investor_growth": investor_growth,
        "status_distribution": status_distribution,
        "recent_investments": recent_investments,
    }