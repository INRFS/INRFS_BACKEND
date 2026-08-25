from sqlalchemy import text
from sqlalchemy.orm import Session
from decimal import Decimal

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


# =========================================================
# ADMIN LIST
# =========================================================

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


# =========================================================
# ADMIN DETAILS
# =========================================================

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


# =========================================================
# MASTER BRANCHES
# =========================================================

def get_superadmin_master_branches(
    db: Session,
):
    return _fetch_all(
        db=db,
        function_name="fn_superadmin_get_master_branches",
    )


# =========================================================
# ROLES
# =========================================================

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


# =========================================================
# STATUSES
# =========================================================

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


# =========================================================
# CREATE ADMIN
# =========================================================

def create_superadmin_admin(
    db: Session,
    full_name: str,
    email: str,
    mobile: str,
    branch_id: int,
    role_id: int,
    status_id: int,
    password: str,
    created_by: int,
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
                :p_status_id,
                :p_password,
                :p_created_by
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
            "p_password": password,
            "p_created_by": created_by,
        },
    )

    row = result.mappings().first()

    if not row:
        db.rollback()

        raise ValueError(
            "Admin creation failed."
        )

    data = dict(row)

    # PostgreSQL function can return
    # success = false for validation errors.
    if not data.get("success"):
        db.rollback()

        raise ValueError(
            data.get(
                "message",
                "Unable to create admin.",
            )
        )

    db.commit()

    return data


# =========================================================
# UPDATE ADMIN
# =========================================================

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

    row = result.mappings().first()

    if not row:
        db.rollback()

        raise ValueError(
            "Admin update failed."
        )

    data = dict(row)

    if data.get("success") is False:
        db.rollback()

        raise ValueError(
            data.get(
                "message",
                "Unable to update admin.",
            )
        )

    db.commit()

    return data


# =========================================================
# SUSPEND ADMIN
# =========================================================

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

    row = result.mappings().first()

    if not row:
        db.rollback()

        return {
            "success": True,
            "admin_id": admin_id,
        }

    data = dict(row)

    if data.get("success") is False:
        db.rollback()

        raise ValueError(
            data.get(
                "message",
                "Unable to suspend admin.",
            )
        )

    db.commit()

    return data