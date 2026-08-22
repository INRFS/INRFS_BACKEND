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
            FROM public.{function_name}(
                {placeholders}
            )
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


def get_investors(
    db: Session,
    search: str | None = None,
    branch_id: int | None = None,
    status_id: int | None = None,
    limit: int = 10,
    offset: int = 0,
):
    return _fetch_all(
        db=db,
        function_name="fn_superadmin_get_investors",
        params={
            "p_search": search,
            "p_branch_id": branch_id,
            "p_status_id": status_id,
            "p_limit": limit,
            "p_offset": offset,
        },
    )


def get_investor_details(
    db: Session,
    investor_id: str,
):
    return _fetch_one(
        db=db,
        function_name="fn_superadmin_get_investor_details",
        params={
            "p_investor_id": investor_id,
        },
    )


def get_investor_summary(
    db: Session,
):
    return _fetch_one(
        db=db,
        function_name="fn_superadmin_get_investor_summary",
    )


def get_investor_count(
    db: Session,
    search: str | None = None,
    branch_id: int | None = None,
    status_id: int | None = None,
):
    rows = _fetch_all(
        db=db,
        function_name="fn_superadmin_get_investors",
        params={
            "p_search": search,
            "p_branch_id": branch_id,
            "p_status_id": status_id,
            "p_limit": 100,
            "p_offset": 0,
        },
    )

    return len(rows)



def get_superadmin_investor_branches(
    db: Session,
):
    return _fetch_all(
        db=db,
        function_name="fn_superadmin_get_master_branches",
    )


def get_superadmin_investor_statuses(
    db: Session,
):
    return _fetch_all(
        db=db,
        function_name="fn_superadmin_get_investor_statuses",
    )
