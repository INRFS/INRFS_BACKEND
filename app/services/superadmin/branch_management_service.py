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

    return rows[0] if rows else {}


def get_superadmin_branches(
    db: Session,
    search: str | None = None,
    limit: int = 10,
    offset: int = 0,
):
    return _fetch_all(
        db=db,
        function_name="fn_superadmin_get_branches",
        params={
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
        db=db,
        function_name="fn_superadmin_get_branch_details",
        params={
            "p_branch_id": branch_id,
        },
    )


def get_superadmin_branch_states(
    db: Session,
):
    result = db.execute(
        text(
            """
            SELECT
                id,
                state_name
            FROM public.master_state
            ORDER BY state_name ASC
            """
        )
    )

    return [
        dict(row)
        for row in result.mappings().all()
    ]


def create_superadmin_branch(
    db: Session,
    branch_name: str,
    city_name: str,
    state_id: int,
    is_active: bool = True,
):
    branch_name = branch_name.strip()
    city_name = city_name.strip()

    existing = db.execute(
        text(
            """
            SELECT id
            FROM public.master_branch
            WHERE LOWER(branch_name) =
                  LOWER(:branch_name)
            """
        ),
        {
            "branch_name": branch_name,
        },
    ).scalar()

    if existing:
        raise ValueError(
            "A branch with this name already exists."
        )

    state_exists = db.execute(
        text(
            """
            SELECT id
            FROM public.master_state
            WHERE id = :state_id
            """
        ),
        {
            "state_id": state_id,
        },
    ).scalar()

    if not state_exists:
        raise ValueError(
            "Selected state does not exist."
        )

    result = db.execute(
        text(
            """
            INSERT INTO public.master_branch
            (
                branch_name,
                city_name,
                state_id,
                is_active
            )
            VALUES
            (
                :branch_name,
                :city_name,
                :state_id,
                :is_active
            )
            RETURNING id
            """
        ),
        {
            "branch_name": branch_name,
            "city_name": city_name,
            "state_id": state_id,
            "is_active": is_active,
        },
    )

    branch_id = result.scalar_one()

    db.commit()

    return get_superadmin_branch_details(
        db=db,
        branch_id=branch_id,
    )


def update_superadmin_branch(
    db: Session,
    branch_id: int,
    branch_name: str,
    city_name: str,
    state_id: int,
    is_active: bool,
):
    branch_name = branch_name.strip()
    city_name = city_name.strip()

    existing = db.execute(
        text(
            """
            SELECT id
            FROM public.master_branch
            WHERE id = :branch_id
            """
        ),
        {
            "branch_id": branch_id,
        },
    ).scalar()

    if not existing:
        raise ValueError(
            "Branch not found."
        )

    duplicate = db.execute(
        text(
            """
            SELECT id
            FROM public.master_branch
            WHERE LOWER(branch_name) =
                  LOWER(:branch_name)
              AND id <> :branch_id
            """
        ),
        {
            "branch_name": branch_name,
            "branch_id": branch_id,
        },
    ).scalar()

    if duplicate:
        raise ValueError(
            "Another branch with this name already exists."
        )

    state_exists = db.execute(
        text(
            """
            SELECT id
            FROM public.master_state
            WHERE id = :state_id
            """
        ),
        {
            "state_id": state_id,
        },
    ).scalar()

    if not state_exists:
        raise ValueError(
            "Selected state does not exist."
        )

    db.execute(
        text(
            """
            UPDATE public.master_branch
            SET
                branch_name = :branch_name,
                city_name = :city_name,
                state_id = :state_id,
                is_active = :is_active
            WHERE id = :branch_id
            """
        ),
        {
            "branch_name": branch_name,
            "city_name": city_name,
            "state_id": state_id,
            "is_active": is_active,
            "branch_id": branch_id,
        },
    )

    db.commit()

    return get_superadmin_branch_details(
        db=db,
        branch_id=branch_id,
    )


def delete_superadmin_branch(
    db: Session,
    branch_id: int,
):
    existing = db.execute(
        text(
            """
            SELECT id
            FROM public.master_branch
            WHERE id = :branch_id
            """
        ),
        {
            "branch_id": branch_id,
        },
    ).scalar()

    if not existing:
        raise ValueError(
            "Branch not found."
        )

    db.execute(
        text(
            """
            UPDATE public.master_branch
            SET is_active = FALSE
            WHERE id = :branch_id
            """
        ),
        {
            "branch_id": branch_id,
        },
    )

    db.commit()

    return {
        "branch_id": branch_id,
        "message":
            "Branch deactivated successfully.",
    }