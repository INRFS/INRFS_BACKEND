from sqlalchemy import text
from sqlalchemy.orm import Session


def _fetch_all(
    db: Session,
    function_name: str,
    params: dict | None = None,
):
    params = params or {}

    if params:
        placeholders = ", ".join(
            f":{key}" for key in params
        )

        query = text(
            f"""
            SELECT *
            FROM public.{function_name}({placeholders})
            """
        )
    else:
        query = text(
            f"""
            SELECT *
            FROM public.{function_name}()
            """
        )

    result = db.execute(
        query,
        params,
    )

    return [
        dict(row)
        for row in result.mappings().all()
    ]


def _fetch_one(
    db: Session,
    function_name: str,
    params: dict | None = None,
):
    rows = _fetch_all(
        db=db,
        function_name=function_name,
        params=params,
    )

    if not rows:
        return {}

    return rows[0]


def get_superadmin_dashboard(
    db: Session,
):
    summary = _fetch_one(
        db,
        "fn_superadmin_get_dashboard_summary",
    )

    investment_summary = _fetch_one(
        db,
        "fn_superadmin_get_investment_summary",
    )

    investor_summary = _fetch_one(
        db,
        "fn_superadmin_get_investor_summary",
    )

    branch_performance = _fetch_all(
        db,
        "fn_superadmin_get_branch_performance",
    )

    investment_performance = _fetch_all(
        db,
        "fn_superadmin_get_investment_performance",
    )

    investment_status = _fetch_all(
        db,
        "fn_superadmin_get_investment_status",
    )

    investor_growth = _fetch_all(
        db,
        "fn_superadmin_get_investor_growth",
    )

    return {
        "summary": summary,
        "investment_summary": investment_summary,
        "investor_summary": investor_summary,
        "branch_performance": branch_performance,
        "investment_performance": investment_performance,
        "investment_status": investment_status,
        "investor_growth": investor_growth,
    }


def get_superadmin_branches(
    db: Session,
    search: str | None = None,
    limit: int = 10,
    offset: int = 0,
):
    return _fetch_all(
        db,
        "fn_superadmin_get_branches",
        {
            "p_search": search,
            "p_limit": limit,
            "p_offset": offset,
        },
    )


def get_superadmin_branch_details(
    db: Session,
    branch_id: int,
):
    return _fetch_one(
        db,
        "fn_superadmin_get_branch_details",
        {
            "p_branch_id": branch_id,
        },
    )


def get_superadmin_admins(
    db: Session,
    search: str | None = None,
):
    return _fetch_all(
        db,
        "fn_superadmin_get_admins",
        {
            "p_search": search,
        },
    )


def get_superadmin_admin_details(
    db: Session,
    admin_id: int,
):
    return _fetch_one(
        db,
        "fn_superadmin_get_admin_details",
        {
            "p_admin_id": admin_id,
        },
    )


def get_superadmin_investors(
    db: Session,
    search: str | None = None,
    branch_id: int | None = None,
    status_id: int | None = None,
    limit: int = 10,
    offset: int = 0,
):
    return _fetch_all(
        db,
        "fn_superadmin_get_investors",
        {
            "p_search": search,
            "p_branch_id": branch_id,
            "p_status_id": status_id,
            "p_limit": limit,
            "p_offset": offset,
        },
    )


def get_superadmin_investor_details(
    db: Session,
    investor_id: str,
):
    return _fetch_one(
        db,
        "fn_superadmin_get_investor_details",
        {
            "p_investor_id": investor_id,
        },
    )


def get_superadmin_investments(
    db: Session,
    search: str | None = None,
    branch_id: int | None = None,
    status_id: int | None = None,
    limit: int = 10,
    offset: int = 0,
):
    return _fetch_all(
        db,
        "fn_superadmin_get_investments",
        {
            "p_search": search,
            "p_branch_id": branch_id,
            "p_status_id": status_id,
            "p_limit": limit,
            "p_offset": offset,
        },
    )


def get_superadmin_payment_queue(
    db: Session,
    payment_type: str,
    limit: int = 10,
    offset: int = 0,
):
    return _fetch_all(
        db,
        "fn_superadmin_get_payment_queue",
        {
            "p_payment_type": payment_type,
            "p_limit": limit,
            "p_offset": offset,
        },
    )





def get_superadmin_payment_details(
    db: Session,
    source_id: int,
    payment_type: str,
):
    return _fetch_one(
        db,
        "fn_superadmin_get_payment_details",
        {
            "p_source_id": source_id,
            "p_payment_type": payment_type,
        },
    )