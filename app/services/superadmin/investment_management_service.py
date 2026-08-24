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
            f":{key}"
            for key in params
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


def get_investments(
    db: Session,
    search: str | None = None,
    branch_id: int | None = None,
    status_id: int | None = None,
    limit: int = 10,
    offset: int = 0,
):
    return _fetch_all(
        db=db,
        function_name="fn_superadmin_get_investments",
        params={
            "p_search": search,
            "p_branch_id": branch_id,
            "p_status_id": status_id,
            "p_limit": limit,
            "p_offset": offset,
        },
    )


def get_investment_summary(
    db: Session,
):
    return _fetch_one(
        db=db,
        function_name="fn_superadmin_get_investment_summary",
    )


def get_investment_status_distribution(
    db: Session,
):
    return _fetch_all(
        db=db,
        function_name="fn_superadmin_get_investment_status",
    )


def get_investment_count(
    db: Session,
    search: str | None = None,
    branch_id: int | None = None,
    status_id: int | None = None,
):
    rows = get_investments(
        db=db,
        search=search,
        branch_id=branch_id,
        status_id=status_id,
        limit=100,
        offset=0,
    )

    return len(rows)


def get_branches(
    db: Session,
):
    result = db.execute(
        text(
            """
            SELECT
                id,
                branch_name,
                state_id,
                city_name,
                is_active
            FROM public.master_branch
            WHERE is_active = TRUE
            ORDER BY branch_name
            """
        )
    )

    return [
        dict(row)
        for row in result.mappings().all()
    ]


def get_investment_statuses(
    db: Session,
):
    result = db.execute(
        text(
            """
            SELECT
                id,
                status_name,
                is_active
            FROM public.master_investment_status
            WHERE is_active = TRUE
            ORDER BY status_name
            """
        )
    )

    return [
        dict(row)
        for row in result.mappings().all()
    ]