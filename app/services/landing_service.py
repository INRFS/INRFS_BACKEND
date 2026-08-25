from __future__ import annotations

from typing import Any, Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session


def _fetch_one(
    db: Session,
    sql: str,
    params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    result = db.execute(
        text(sql),
        params or {},
    )
    row = result.fetchone()

    if not row:
        return {}

    return dict(row._mapping)


def _safe_query(
    db: Session,
    sql: str,
    params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    try:
        return _fetch_one(
            db=db,
            sql=sql,
            params=params,
        )
    except Exception:
        db.rollback()
        return {}


def _safe_float(
    value: Any,
    default: float = 0.0,
) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return default


def _format_currency_short(
    value: float,
) -> str:
    value = max(value, 0)

    crore = 10_000_000
    lakh = 100_000

    if value >= crore:
        number = value / crore

        if number.is_integer():
            return f"₹{int(number):,}Cr+"

        return f"₹{number:,.1f}Cr+"

    if value >= lakh:
        number = value / lakh

        if number.is_integer():
            return f"₹{int(number):,}L+"

        return f"₹{number:,.1f}L+"

    return f"₹{value:,.0f}"


def _format_currency_full(
    value: float,
) -> str:
    return f"₹{value:,.0f}"


def get_public_home_stats(
    db: Session,
) -> Dict[str, Any]:
    """
    Dynamic public homepage statistics.

    All values are read from the INRFS database.
    No authentication is required by the route using this service.
    """

    # Total invested principal.
    # Rejected investments are excluded.
    aum_row = _safe_query(
        db,
        """
        SELECT
            COALESCE(
                SUM(i.investment_amount),
                0
            ) AS total_aum
        FROM public.tn_investment i
        WHERE COALESCE(
            i.investment_status_id,
            0
        ) <> 3
        """,
    )

    # Unique investors with a non-rejected investment.
    investor_row = _safe_query(
        db,
        """
        SELECT
            COUNT(
                DISTINCT i.investor_registration_id
            ) AS active_investors
        FROM public.tn_investment i
        WHERE i.investor_registration_id IS NOT NULL
          AND COALESCE(
              i.investment_status_id,
              0
          ) <> 3
        """,
    )

    # Maximum interest rate currently present in investments.
    rate_row = _safe_query(
        db,
        """
        SELECT
            COALESCE(
                MAX(i.interest_rate),
                0
            ) AS max_interest_rate
        FROM public.tn_investment i
        WHERE COALESCE(
            i.investment_status_id,
            0
        ) <> 3
        """,
    )

    # Interest actually paid.
    interest_row = _safe_query(
        db,
        """
        SELECT
            COALESCE(
                SUM(ins.net_interest_amount),
                0
            ) AS total_interest_paid
        FROM public.tn_interest_schedule ins
        WHERE ins.interest_paid_date IS NOT NULL
        """,
    )

    # Total bonds created/issued.
    bond_row = _safe_query(
        db,
        """
        SELECT
            COUNT(*) AS bonds_issued
        FROM public.tn_bond
        """,
    )

    # Active branch offices.
    branch_row = _safe_query(
        db,
        """
        SELECT
            COUNT(*) AS branch_offices
        FROM public.master_branch
        WHERE is_active = TRUE
        """,
    )

    # Active investments.
    active_bond_row = _safe_query(
        db,
        """
        SELECT
            COUNT(*) AS active_bonds
        FROM public.tn_investment i
        WHERE COALESCE(
            i.investment_status_id,
            0
        ) = 2
        """,
    )

    # Earliest unpaid interest amount.
    # This query is intentionally guarded because older DB versions
    # may not have the same schedule-date column.
    next_payout_row = _safe_query(
        db,
        """
        SELECT
            COALESCE(
                ins.net_interest_amount,
                0
            ) AS next_payout
        FROM public.tn_interest_schedule ins
        JOIN public.tn_investment i
            ON i.id = ins.investment_id
        WHERE ins.interest_paid_date IS NULL
          AND COALESCE(
              i.investment_status_id,
              0
          ) = 2
        ORDER BY ins.id
        LIMIT 1
        """,
    )

    # Featured investment/bond.
    # Uses fields already confirmed in the current investment API.
    featured_row = _safe_query(
        db,
        """
        SELECT
            COALESCE(
                NULLIF(i.bond_id, ''),
                i.investment_id
            ) AS bond_code,
            COALESCE(
                i.interest_rate,
                0
            ) AS interest_rate,
            i.investment_status_id,
            i.tenure_months
        FROM public.tn_investment i
        WHERE COALESCE(
            i.investment_status_id,
            0
        ) = 2
        ORDER BY
            i.investment_amount DESC,
            i.id DESC
        LIMIT 1
        """,
    )

    total_aum = _safe_float(
        aum_row.get("total_aum")
    )

    active_investors = int(
        _safe_float(
            investor_row.get(
                "active_investors"
            )
        )
    )

    max_interest_rate = _safe_float(
        rate_row.get(
            "max_interest_rate"
        )
    )

    total_interest_paid = _safe_float(
        interest_row.get(
            "total_interest_paid"
        )
    )

    bonds_issued = int(
        _safe_float(
            bond_row.get("bonds_issued")
        )
    )

    branch_offices = int(
        _safe_float(
            branch_row.get(
                "branch_offices"
            )
        )
    )

    active_bonds = int(
        _safe_float(
            active_bond_row.get(
                "active_bonds"
            )
        )
    )

    next_payout = _safe_float(
        next_payout_row.get(
            "next_payout"
        )
    )

    featured_rate = _safe_float(
        featured_row.get(
            "interest_rate"
        )
    )

    featured_status_id = (
        featured_row.get(
            "investment_status_id"
        )
    )

    featured_status = (
        "Active"
        if featured_status_id == 2
        else "Available"
    )

    featured_bond_code = (
        featured_row.get(
            "bond_code"
        )
        or "INRFS-INVESTMENT"
    )

    featured_tenure = int(
        _safe_float(
            featured_row.get(
                "tenure_months"
            )
        )
    )

    return {
        "hero": {
            "total_aum": total_aum,
            "total_aum_label": (
                _format_currency_short(
                    total_aum
                )
            ),
            "active_investors": active_investors,
            "active_investors_label": (
                f"{active_investors:,}+"
                if active_investors
                else "0"
            ),
            "max_interest_rate": max_interest_rate,
            "max_interest_rate_label": (
                f"{max_interest_rate:g}%"
            ),
            "approval_time_hours": 48,
            "approval_time_label": "48hrs",
            "total_invested_label": (
                _format_currency_full(
                    total_aum
                )
            ),
            "interest_earned_label": (
                _format_currency_full(
                    total_interest_paid
                )
            ),
            "active_bonds": active_bonds,
            "next_payout_label": (
                _format_currency_full(
                    next_payout
                )
            ),
            "featured_bond": {
                "id": str(
                    featured_bond_code
                ),
                "title": (
                    (
                        f"Fixed Deposit — "
                        f"{featured_rate:g}% p.a."
                    )
                    if featured_rate
                    else "Fixed Deposit"
                ),
                "status": featured_status,
                "interest_rate": featured_rate,
                "tenure_months": featured_tenure,
            },
        },
        "benefits": {
            "total_returns_paid": (
                total_interest_paid
            ),
            "total_returns_paid_label": (
                _format_currency_short(
                    total_interest_paid
                )
            ),
            "active_investors": active_investors,
            "bonds_issued": bonds_issued,
            "branch_offices": branch_offices,
        },
    }