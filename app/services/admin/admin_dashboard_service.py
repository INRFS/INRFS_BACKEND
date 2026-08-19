from typing import Any, Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session


def get_dashboard_summary(
    db: Session,
    branch_id: Optional[int] = None,
) -> Dict[str, Any]:

    result = db.execute(
        text(
            """
            SELECT *
            FROM public.fn_get_admin_dashboard_summary(
                CAST(:branch_id AS INTEGER)
            )
            """
        ),
        {
            "branch_id": branch_id,
        },
    )

    row = result.mappings().first()

    if not row:
        return {}

    return dict(row)


def get_investor_growth(
    db: Session,
    branch_id: Optional[int] = None,
) -> List[Dict[str, Any]]:

    result = db.execute(
        text(
            """
            SELECT *
            FROM public.fn_get_admin_investor_growth(
                CAST(:branch_id AS INTEGER)
            )
            """
        ),
        {
            "branch_id": branch_id,
        },
    )

    rows = result.mappings().all()

    return [
        dict(row)
        for row in rows
    ]


def get_monthly_investment_trend(
    db: Session,
    branch_id: Optional[int] = None,
) -> List[Dict[str, Any]]:

    result = db.execute(
        text(
            """
            SELECT *
            FROM public.fn_get_admin_monthly_investment_trend(
                CAST(:branch_id AS INTEGER)
            )
            """
        ),
        {
            "branch_id": branch_id,
        },
    )

    rows = result.mappings().all()

    return [
        dict(row)
        for row in rows
    ]