from sqlalchemy import text
from sqlalchemy.orm import Session


def _rows(result):
    return [dict(row._mapping) for row in result]


def _row(result):
    row = result.first()
    return dict(row._mapping) if row else None


def get_investor_dashboard(
    db: Session,
    investor_id: str,
    year: int,
):
    summary_result = db.execute(
        text("""
            SELECT *
            FROM public.fn_get_investor_dashboard_summary(
                :investor_id
            )
        """),
        {
            "investor_id": investor_id,
        },
    )

    summary = _row(summary_result)

    growth_result = db.execute(
        text("""
            SELECT *
            FROM public.fn_get_investor_dashboard_investment_growth(
                :investor_id,
                :year
            )
        """),
        {
            "investor_id": investor_id,
            "year": year,
        },
    )

    growth = _rows(growth_result)

    recent_result = db.execute(
        text("""
            SELECT *
            FROM public.fn_get_investor_dashboard_recent_investments(
                :investor_id
            )
        """),
        {
            "investor_id": investor_id,
        },
    )

    recent_investments = _rows(recent_result)

    investor_result = db.execute(
        text("""
            SELECT *
            FROM public.fn_get_investor_details(
                :investor_id
            )
        """),
        {
            "investor_id": investor_id,
        },
    )

    investor = _row(investor_result)

    portfolio_split = []

    return {
        "summary": summary,
        "growth": growth,
        "portfolio_split": portfolio_split,
        "recent_investments": recent_investments,
        "investor": investor,
    }