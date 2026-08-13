from typing import Any, Dict, List

from sqlalchemy import text
from sqlalchemy.orm import Session


def get_dashboard_summary(
    db: Session,
) -> Dict[str, Any]:

    result = db.execute(
        text(
            """
            SELECT *
            FROM fn_get_admin_dashboard_summary()
            """
        )
    )

    row = result.mappings().first()

    if not row:
        return {}

    return dict(row)


def get_investor_growth(
    db: Session,
) -> List[Dict[str, Any]]:

    result = db.execute(
        text(
            """
            SELECT *
            FROM fn_get_admin_investor_growth()
            """
        )
    )

    rows = result.mappings().all()

    return [dict(row) for row in rows]


def get_monthly_investment_trend(
    db: Session,
) -> List[Dict[str, Any]]:

    result = db.execute(
        text(
            """
            SELECT *
            FROM fn_get_admin_monthly_investment_trend()
            """
        )
    )

    rows = result.mappings().all()

    return [dict(row) for row in rows]