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


def get_superadmin_admins(
    db: Session,
    search: str | None = None,
):
    return _fetch_all(
        db=db,
        function_name="fn_superadmin_get_admins",
        params={
            "p_search": search,
        },
    )


def get_superadmin_admin_details(
    db: Session,
    admin_id: int,
):
    return _fetch_one(
        db=db,
        function_name="fn_superadmin_get_admin_details",
        params={
            "p_admin_id": admin_id,
        },
    )


def get_superadmin_master_branches(
    db: Session,
):
    return _fetch_all(
        db=db,
        function_name="fn_superadmin_get_master_branches",
    )


def get_superadmin_roles(
    db: Session,
):
    result = db.execute(
        text(
            """
            SELECT
                id,
                role_name
            FROM public.master_role
            WHERE is_active = TRUE
            ORDER BY role_name
            """
        )
    )

    return [
        dict(row)
        for row in result.mappings().all()
    ]


def get_superadmin_statuses(
    db: Session,
):
    result = db.execute(
        text(
            """
            SELECT
                id,
                status_name
            FROM public.master_user_status
            WHERE is_active = TRUE
            ORDER BY id
            """
        )
    )

    return [
        dict(row)
        for row in result.mappings().all()
    ]


def create_superadmin_admin(
    db: Session,
    full_name: str,
    email: str,
    mobile: str,
    branch_id: int,
    role_id: int,
    status_id: int,
):
    result = db.execute(
        text(
            """
            SELECT *
            FROM public.fn_superadmin_create_admin(
                :p_full_name,
                :p_email,
                :p_mobile,
                :p_branch_id,
                :p_role_id,
                :p_status_id
            )
            """
        ),
        {
            "p_full_name": full_name.strip(),
            "p_email": email.strip(),
            "p_mobile": mobile.strip(),
            "p_branch_id": branch_id,
            "p_role_id": role_id,
            "p_status_id": status_id,
        },
    )

    rows = result.mappings().all()

    db.commit()

    return (
        dict(rows[0])
        if rows
        else {}
    )


def update_superadmin_admin(
    db: Session,
    admin_id: int,
    full_name: str,
    email: str,
    mobile: str,
    branch_id: int,
    role_id: int,
    status_id: int,
):
    result = db.execute(
        text(
            """
            SELECT *
            FROM public.fn_superadmin_update_admin(
                :p_admin_id,
                :p_full_name,
                :p_email,
                :p_mobile,
                :p_branch_id,
                :p_role_id,
                :p_status_id
            )
            """
        ),
        {
            "p_admin_id": admin_id,
            "p_full_name": full_name.strip(),
            "p_email": email.strip(),
            "p_mobile": mobile.strip(),
            "p_branch_id": branch_id,
            "p_role_id": role_id,
            "p_status_id": status_id,
        },
    )

    rows = result.mappings().all()

    db.commit()

    return (
        dict(rows[0])
        if rows
        else {}
    )


def suspend_superadmin_admin(
    db: Session,
    admin_id: int,
    modified_by: int,
):
    result = db.execute(
        text(
            """
            SELECT *
            FROM public.fn_superadmin_suspend_admin(
                :p_admin_id,
                :p_modified_by
            )
            """
        ),
        {
            "p_admin_id": admin_id,
            "p_modified_by": modified_by,
        },
    )

    rows = result.mappings().all()

    db.commit()

    return (
        dict(rows[0])
        if rows
        else {
            "success": True,
            "admin_id": admin_id,
        }
    )