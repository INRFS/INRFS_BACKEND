from typing import Any, Dict, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session


def _rows(result):
    return [
        dict(row._mapping)
        for row in result.fetchall()
    ]


def _row(result):
    row = result.first()
    return (
        dict(row._mapping)
        if row
        else None
    )


def get_report_filters(
    db: Session,
) -> Dict[str, Any]:
    branches = _rows(
        db.execute(
            text(
                """
                SELECT
                    id,
                    branch_name,
                    city_name
                FROM public.master_branch
                WHERE COALESCE(is_active, TRUE) = TRUE
                ORDER BY branch_name
                """
            )
        )
    )

    statuses = _rows(
        db.execute(
            text(
                """
                SELECT
                    id,
                    status_name
                FROM public.master_investment_status
                WHERE COALESCE(is_active, TRUE) = TRUE
                ORDER BY id
                """
            )
        )
    )

    admins = _rows(
        db.execute(
            text(
                """
                SELECT
                    u.id,
                    u.full_name,
                    u.email,
                    u.mobile,
                    u.branch_id,
                    b.branch_name,
                    r.id AS role_id,
                    r.role_name
                FROM public.tn_application_user u
                INNER JOIN public.master_role r
                    ON r.id = u.role_id
                LEFT JOIN public.master_branch b
                    ON b.id = u.branch_id
                WHERE
                    UPPER(TRIM(r.role_name)) = 'ADMIN'
                    AND COALESCE(u.is_active, TRUE) = TRUE
                ORDER BY u.full_name
                """
            )
        )
    )

    return {
        "success": True,
        "data": {
            "branches": branches,
            "statuses": statuses,
            "admins": admins,
        },
        "branches": branches,
        "statuses": statuses,
        "admins": admins,
    }


def get_investments(
    db: Session,
    search: Optional[str] = None,
    branch_id: Optional[int] = None,
    admin_id: Optional[int] = None,
    status_id: Optional[int] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
):
    where = ["1 = 1"]

    params = {
        "limit": min(
            max(int(limit or 100), 1),
            500,
        ),
        "offset": max(
            int(offset or 0),
            0,
        ),
    }

    if search:
        where.append(
            """
            (
                i.investment_id ILIKE :search
                OR COALESCE(ir.investor_id, '') ILIKE :search
                OR COALESCE(investor_u.full_name, '') ILIKE :search
                OR COALESCE(admin_u.full_name, '') ILIKE :search
                OR COALESCE(admin_u.email, '') ILIKE :search
                OR COALESCE(b.branch_name, '') ILIKE :search
            )
            """
        )
        params["search"] = (
            f"%{search.strip()}%"
        )

    if branch_id:
        where.append(
            "ir.branch_id = :branch_id"
        )
        params["branch_id"] = branch_id

    if admin_id:
        where.append(
            "i.approved_by = :admin_id"
        )
        params["admin_id"] = admin_id

    if status_id:
        where.append(
            "i.investment_status_id = :status_id"
        )
        params["status_id"] = status_id

    if from_date:
        where.append(
            "i.investment_date::date >= :from_date"
        )
        params["from_date"] = from_date

    if to_date:
        where.append(
            "i.investment_date::date <= :to_date"
        )
        params["to_date"] = to_date

    where_sql = " AND ".join(where)

    base_from = """
        FROM public.tn_investment i

        INNER JOIN public.tn_investor_registration ir
            ON ir.id = i.investor_registration_id

        INNER JOIN public.tn_application_user investor_u
            ON investor_u.id = ir.user_id

        LEFT JOIN public.master_branch b
            ON b.id = ir.branch_id

        LEFT JOIN public.master_investment_status s
            ON s.id = i.investment_status_id

        LEFT JOIN public.tn_application_user admin_u
            ON admin_u.id = i.approved_by

        LEFT JOIN public.master_role admin_role
            ON admin_role.id = admin_u.role_id

        LEFT JOIN public.tn_application_user superadmin_u
            ON superadmin_u.id = i.modified_by

        LEFT JOIN public.master_role superadmin_role
            ON superadmin_role.id = superadmin_u.role_id
    """

    count_result = db.execute(
        text(
            f"""
            SELECT COUNT(*) AS total
            {base_from}
            WHERE {where_sql}
            """
        ),
        params,
    )

    total = int(
        count_result.scalar() or 0
    )

    result = db.execute(
        text(
            f"""
            SELECT
                i.id,
                i.investment_id,
                i.investor_registration_id,

                ir.investor_id,
                investor_u.full_name AS investor_name,
                investor_u.email AS investor_email,
                investor_u.mobile AS investor_mobile,

                ir.branch_id,
                b.branch_name,
                b.city_name,

                CASE
                    WHEN UPPER(
                        TRIM(
                            COALESCE(
                                admin_role.role_name,
                                ''
                            )
                        )
                    ) = 'ADMIN'
                    THEN i.approved_by
                    ELSE NULL
                END AS admin_id,

                CASE
                    WHEN UPPER(
                        TRIM(
                            COALESCE(
                                admin_role.role_name,
                                ''
                            )
                        )
                    ) = 'ADMIN'
                    THEN admin_u.full_name
                    ELSE NULL
                END AS admin_name,

                CASE
                    WHEN UPPER(
                        TRIM(
                            COALESCE(
                                admin_role.role_name,
                                ''
                            )
                        )
                    ) = 'ADMIN'
                    THEN admin_u.email
                    ELSE NULL
                END AS admin_email,

                CASE
                    WHEN UPPER(
                        TRIM(
                            COALESCE(
                                superadmin_role.role_name,
                                ''
                            )
                        )
                    ) = 'SUPERADMIN'
                    THEN i.modified_by
                    ELSE NULL
                END AS superadmin_id,

                CASE
                    WHEN UPPER(
                        TRIM(
                            COALESCE(
                                superadmin_role.role_name,
                                ''
                            )
                        )
                    ) = 'SUPERADMIN'
                    THEN superadmin_u.full_name
                    ELSE NULL
                END AS superadmin_name,

                CASE
                    WHEN UPPER(
                        TRIM(
                            COALESCE(
                                superadmin_role.role_name,
                                ''
                            )
                        )
                    ) = 'SUPERADMIN'
                    THEN superadmin_u.email
                    ELSE NULL
                END AS superadmin_email,

                i.investment_amount,
                i.interest_rate,
                i.expected_interest_amount,
                i.maturity_amount,

                i.investment_status_id AS status_id,
                COALESCE(
                    s.status_name,
                    'Unknown'
                ) AS status_name,

                i.investment_date,
                i.maturity_date,

                t.tenure_months,

                i.approved_date,
                i.remarks,
                i.created_date,
                i.modified_date

            {base_from}

            LEFT JOIN public.master_investment_tenure t
                ON t.id = i.tenure_id

            WHERE {where_sql}

            ORDER BY
                i.investment_date DESC NULLS LAST,
                i.id DESC

            LIMIT :limit
            OFFSET :offset
            """
        ),
        params,
    )

    return {
        "success": True,
        "data": _rows(result),
        "total": total,
        "limit": params["limit"],
        "offset": params["offset"],
    }


def get_investment_details(
    db: Session,
    investment_id: str,
):
    result = db.execute(
        text(
            """
            SELECT
                i.id,
                i.investment_id,
                i.investor_registration_id,

                ir.investor_id,
                investor_u.full_name AS investor_name,
                investor_u.email AS investor_email,
                investor_u.mobile AS investor_mobile,

                ir.branch_id,
                b.branch_name,
                b.city_name,

                CASE
                    WHEN UPPER(
                        TRIM(
                            COALESCE(
                                admin_role.role_name,
                                ''
                            )
                        )
                    ) = 'ADMIN'
                    THEN i.approved_by
                    ELSE NULL
                END AS admin_id,

                CASE
                    WHEN UPPER(
                        TRIM(
                            COALESCE(
                                admin_role.role_name,
                                ''
                            )
                        )
                    ) = 'ADMIN'
                    THEN admin_u.full_name
                    ELSE NULL
                END AS admin_name,

                CASE
                    WHEN UPPER(
                        TRIM(
                            COALESCE(
                                admin_role.role_name,
                                ''
                            )
                        )
                    ) = 'ADMIN'
                    THEN admin_u.email
                    ELSE NULL
                END AS admin_email,

                CASE
                    WHEN UPPER(
                        TRIM(
                            COALESCE(
                                superadmin_role.role_name,
                                ''
                            )
                        )
                    ) = 'SUPERADMIN'
                    THEN i.modified_by
                    ELSE NULL
                END AS superadmin_id,

                CASE
                    WHEN UPPER(
                        TRIM(
                            COALESCE(
                                superadmin_role.role_name,
                                ''
                            )
                        )
                    ) = 'SUPERADMIN'
                    THEN superadmin_u.full_name
                    ELSE NULL
                END AS superadmin_name,

                CASE
                    WHEN UPPER(
                        TRIM(
                            COALESCE(
                                superadmin_role.role_name,
                                ''
                            )
                        )
                    ) = 'SUPERADMIN'
                    THEN superadmin_u.email
                    ELSE NULL
                END AS superadmin_email,

                i.investment_amount,
                i.interest_rate,
                i.expected_interest_amount,
                i.maturity_amount,

                i.investment_status_id AS status_id,
                COALESCE(
                    s.status_name,
                    'Unknown'
                ) AS status_name,

                i.investment_date,
                i.maturity_date,
                t.tenure_months,

                i.approved_date,
                i.remarks,
                i.created_date,
                i.modified_date

            FROM public.tn_investment i

            INNER JOIN public.tn_investor_registration ir
                ON ir.id = i.investor_registration_id

            INNER JOIN public.tn_application_user investor_u
                ON investor_u.id = ir.user_id

            LEFT JOIN public.master_branch b
                ON b.id = ir.branch_id

            LEFT JOIN public.master_investment_status s
                ON s.id = i.investment_status_id

            LEFT JOIN public.master_investment_tenure t
                ON t.id = i.tenure_id

            LEFT JOIN public.tn_application_user admin_u
                ON admin_u.id = i.approved_by

            LEFT JOIN public.master_role admin_role
                ON admin_role.id = admin_u.role_id

            LEFT JOIN public.tn_application_user superadmin_u
                ON superadmin_u.id = i.modified_by

            LEFT JOIN public.master_role superadmin_role
                ON superadmin_role.id = superadmin_u.role_id

            WHERE i.investment_id = :investment_id

            LIMIT 1
            """
        ),
        {
            "investment_id": str(
                investment_id
            ).strip()
        },
    )

    data = _row(result)

    return {
        "success": bool(data),
        "data": data,
    }


def get_admin_report(
    db: Session,
    search: Optional[str] = None,
    branch_id: Optional[int] = None,
    status_id: Optional[int] = None,
    admin_id: Optional[int] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
):
    conditions = [
        "UPPER(TRIM(r.role_name)) = 'ADMIN'",
        "COALESCE(u.is_active, TRUE) = TRUE",
    ]

    params = {}

    if search:
        conditions.append(
            """
            (
                COALESCE(u.full_name, '') ILIKE :search
                OR COALESCE(u.email, '') ILIKE :search
                OR COALESCE(b.branch_name, '') ILIKE :search
                OR COALESCE(u.mobile, '') ILIKE :search
            )
            """
        )
        params["search"] = (
            f"%{search.strip()}%"
        )

    if branch_id:
        conditions.append(
            "u.branch_id = :branch_id"
        )
        params["branch_id"] = branch_id

    if admin_id:
        conditions.append(
            "u.id = :admin_id"
        )
        params["admin_id"] = admin_id

    investment_conditions = [
        "i.approved_by = u.id"
    ]

    if status_id:
        investment_conditions.append(
            "i.investment_status_id = :status_id"
        )
        params["status_id"] = status_id

    if from_date:
        investment_conditions.append(
            "i.investment_date::date >= :from_date"
        )
        params["from_date"] = from_date

    if to_date:
        investment_conditions.append(
            "i.investment_date::date <= :to_date"
        )
        params["to_date"] = to_date

    investment_join = " AND ".join(
        investment_conditions
    )

    result = db.execute(
        text(
            f"""
            SELECT
                u.id AS admin_id,
                u.full_name AS admin_name,
                u.email AS admin_email,
                u.mobile AS admin_mobile,
                u.branch_id,
                b.branch_name,

                COUNT(DISTINCT i.id)
                    AS investment_count,

                COUNT(DISTINCT ir.id)
                    AS investor_count,

                COALESCE(
                    SUM(i.investment_amount),
                    0
                ) AS principal_amount,

                COALESCE(
                    SUM(
                        i.expected_interest_amount
                    ),
                    0
                ) AS expected_interest,

                COALESCE(
                    SUM(i.maturity_amount),
                    0
                ) AS maturity_amount,

                COUNT(i.id)
                FILTER (
                    WHERE LOWER(
                        COALESCE(
                            s.status_name,
                            ''
                        )
                    ) LIKE '%pending%'
                ) AS pending_count,

                COUNT(i.id)
                FILTER (
                    WHERE
                        LOWER(
                            COALESCE(
                                s.status_name,
                                ''
                            )
                        ) LIKE '%approv%'
                        OR
                        LOWER(
                            COALESCE(
                                s.status_name,
                                ''
                            )
                        ) LIKE '%active%'
                ) AS approved_count,

                COUNT(i.id)
                FILTER (
                    WHERE LOWER(
                        COALESCE(
                            s.status_name,
                            ''
                        )
                    ) LIKE '%reject%'
                ) AS rejected_count,

                COUNT(i.id)
                FILTER (
                    WHERE
                        LOWER(
                            COALESCE(
                                s.status_name,
                                ''
                            )
                        ) LIKE '%sett%'
                        OR
                        LOWER(
                            COALESCE(
                                s.status_name,
                                ''
                            )
                        ) LIKE '%close%'
                        OR
                        LOWER(
                            COALESCE(
                                s.status_name,
                                ''
                            )
                        ) LIKE '%paid%'
                ) AS settled_count

            FROM public.tn_application_user u

            INNER JOIN public.master_role r
                ON r.id = u.role_id

            LEFT JOIN public.master_branch b
                ON b.id = u.branch_id

            LEFT JOIN public.tn_investment i
                ON {investment_join}

            LEFT JOIN public.tn_investor_registration ir
                ON ir.id =
                    i.investor_registration_id

            LEFT JOIN public.master_investment_status s
                ON s.id =
                    i.investment_status_id

            WHERE
                {" AND ".join(conditions)}

            GROUP BY
                u.id,
                u.full_name,
                u.email,
                u.mobile,
                u.branch_id,
                b.branch_name

            ORDER BY
                principal_amount DESC,
                u.full_name ASC
            """
        ),
        params,
    )

    data = _rows(result)

    return {
        "success": True,
        "data": data,
        "total": len(data),
    }


def get_investor_report(
    db: Session,
    search: Optional[str] = None,
    branch_id: Optional[int] = None,
    status_id: Optional[int] = None,
    admin_id: Optional[int] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
):
    conditions = [
        "COALESCE(ir.is_active, TRUE) = TRUE"
    ]

    params = {}

    if search:
        conditions.append(
            """
            (
                COALESCE(ir.investor_id, '') ILIKE :search
                OR COALESCE(u.full_name, '') ILIKE :search
                OR COALESCE(u.email, '') ILIKE :search
                OR COALESCE(u.mobile, '') ILIKE :search
                OR COALESCE(b.branch_name, '') ILIKE :search
            )
            """
        )
        params["search"] = (
            f"%{search.strip()}%"
        )

    if branch_id:
        conditions.append(
            "ir.branch_id = :branch_id"
        )
        params["branch_id"] = branch_id

    investment_join = [
        "i.investor_registration_id = ir.id"
    ]

    if status_id:
        investment_join.append(
            "i.investment_status_id = :status_id"
        )
        params["status_id"] = status_id

    if admin_id:
        investment_join.append(
            "i.approved_by = :admin_id"
        )
        params["admin_id"] = admin_id

    if from_date:
        investment_join.append(
            "i.investment_date::date >= :from_date"
        )
        params["from_date"] = from_date

    if to_date:
        investment_join.append(
            "i.investment_date::date <= :to_date"
        )
        params["to_date"] = to_date

    join_filter = " AND ".join(
        investment_join
    )

    result = db.execute(
        text(
            f"""
            SELECT
                ir.id AS investor_registration_id,
                ir.investor_id,
                u.full_name AS investor_name,
                u.email AS investor_email,
                u.mobile AS investor_mobile,

                ir.branch_id,
                b.branch_name,

                COUNT(i.id)
                    AS investment_count,

                COALESCE(
                    SUM(i.investment_amount),
                    0
                ) AS principal_amount,

                COALESCE(
                    SUM(
                        i.expected_interest_amount
                    ),
                    0
                ) AS expected_interest,

                COALESCE(
                    SUM(i.maturity_amount),
                    0
                ) AS maturity_amount,

                COUNT(i.id)
                FILTER (
                    WHERE LOWER(
                        COALESCE(
                            s.status_name,
                            ''
                        )
                    ) LIKE '%pending%'
                ) AS pending_count,

                COUNT(i.id)
                FILTER (
                    WHERE
                        LOWER(
                            COALESCE(
                                s.status_name,
                                ''
                            )
                        ) LIKE '%approv%'
                        OR
                        LOWER(
                            COALESCE(
                                s.status_name,
                                ''
                            )
                        ) LIKE '%active%'
                ) AS active_count,

                COUNT(i.id)
                FILTER (
                    WHERE
                        LOWER(
                            COALESCE(
                                s.status_name,
                                ''
                            )
                        ) LIKE '%sett%'
                        OR
                        LOWER(
                            COALESCE(
                                s.status_name,
                                ''
                            )
                        ) LIKE '%close%'
                        OR
                        LOWER(
                            COALESCE(
                                s.status_name,
                                ''
                            )
                        ) LIKE '%paid%'
                ) AS settled_count,

                COUNT(i.id)
                FILTER (
                    WHERE LOWER(
                        COALESCE(
                            s.status_name,
                            ''
                        )
                    ) LIKE '%reject%'
                ) AS rejected_count

            FROM public.tn_investor_registration ir

            INNER JOIN public.tn_application_user u
                ON u.id = ir.user_id

            LEFT JOIN public.master_branch b
                ON b.id = ir.branch_id

            LEFT JOIN public.tn_investment i
                ON {join_filter}

            LEFT JOIN public.master_investment_status s
                ON s.id =
                    i.investment_status_id

            WHERE
                {" AND ".join(conditions)}

            GROUP BY
                ir.id,
                ir.investor_id,
                u.full_name,
                u.email,
                u.mobile,
                ir.branch_id,
                b.branch_name

            ORDER BY
                principal_amount DESC,
                u.full_name
            """
        ),
        params,
    )

    data = _rows(result)

    return {
        "success": True,
        "data": data,
        "total": len(data),
    }


def get_settlement_report(
    db: Session,
    search: Optional[str] = None,
    branch_id: Optional[int] = None,
    admin_id: Optional[int] = None,
    status_id: Optional[int] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    limit: int = 500,
    offset: int = 0,
):
    where = [
        """
        s.settlement_type IN (
            'TENURE_TIMEOUT',
            'PRECLOSE'
        )
        """
    ]

    params = {
        "limit": min(
            max(int(limit or 500), 1),
            500,
        ),
        "offset": max(
            int(offset or 0),
            0,
        ),
    }

    if search:
        where.append(
            """
            (
                COALESCE(
                    investor_u.full_name,
                    ''
                ) ILIKE :search
                OR COALESCE(
                    investor_u.email,
                    ''
                ) ILIKE :search
                OR COALESCE(
                    i.investment_id,
                    ''
                ) ILIKE :search
                OR COALESCE(
                    b.branch_name,
                    ''
                ) ILIKE :search
            )
            """
        )
        params["search"] = (
            f"%{search.strip()}%"
        )

    if branch_id:
        where.append(
            "ir.branch_id = :branch_id"
        )
        params["branch_id"] = branch_id

    if admin_id:
        where.append(
            "s.approved_by = :admin_id"
        )
        params["admin_id"] = admin_id

    if status_id:
        where.append(
            "s.settlement_status_id = :status_id"
        )
        params["status_id"] = status_id

    if from_date:
        where.append(
            """COALESCE(
                s.approved_date,
                s.created_date
            )::date >= :from_date"""
        )
        params["from_date"] = from_date

    if to_date:
        where.append(
            """COALESCE(
                s.approved_date,
                s.created_date

                            )::date <= :to_date"""
        )
        params["to_date"] = to_date

    where_sql = " AND ".join(where)

    base_sql = """
        FROM public.tn_settlement s

        INNER JOIN public.tn_investment i
            ON i.id = s.investment_id

        INNER JOIN public.tn_investor_registration ir
            ON ir.id = i.investor_registration_id

        INNER JOIN public.tn_application_user investor_u
            ON investor_u.id = ir.user_id

        LEFT JOIN public.master_branch b
            ON b.id = ir.branch_id

        LEFT JOIN public.master_settlement_status ss
            ON ss.id = s.settlement_status_id

        LEFT JOIN public.tn_application_user admin_u
            ON admin_u.id = s.approved_by

        LEFT JOIN public.tn_application_user superadmin_u
            ON superadmin_u.id =
                s.superadmin_approved_by
    """

    total_result = db.execute(
        text(
            f"""
            SELECT COUNT(*)
            {base_sql}
            WHERE {where_sql}
            """
        ),
        params,
    )

    total = int(
        total_result.scalar() or 0
    )

    result = db.execute(
        text(
            f"""
            SELECT
                s.id AS settlement_id,

                s.settlement_type,

                CASE
                    WHEN s.settlement_type =
                        'TENURE_TIMEOUT'
                    THEN 'Tenure Settlement'
                    WHEN s.settlement_type =
                        'PRECLOSE'
                    THEN 'Pre-Close Settlement'
                    ELSE s.settlement_type
                END AS settlement_type_name,

                i.investment_id,

                ir.investor_id,

                investor_u.full_name
                    AS investor_name,

                investor_u.email
                    AS investor_email,

                ir.branch_id,

                b.branch_name,

                s.approved_by AS admin_id,

                admin_u.full_name
                    AS admin_name,

                s.superadmin_approved_by
                    AS superadmin_id,

                superadmin_u.full_name
                    AS superadmin_name,

                s.net_settlement_amount
                    AS settlement_amount,

                s.settlement_status_id
                    AS status_id,

                ss.status_name
                    AS status_name,

                s.approved_date,

                s.created_date,

                s.modified_date,

                s.remarks

            {base_sql}

            WHERE {where_sql}

            ORDER BY
                COALESCE(
                    s.approved_date,
                    s.created_date
                ) DESC NULLS LAST,
                s.id DESC

            LIMIT :limit
            OFFSET :offset
            """
        ),
        params,
    )

    return {
        "success": True,
        "data": _rows(result),
        "total": total,
        "limit": params["limit"],
        "offset": params["offset"],
    }


def get_extension_report(
    db: Session,
    search: Optional[str] = None,
    branch_id: Optional[int] = None,
    admin_id: Optional[int] = None,
    status_id: Optional[int] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    limit: int = 500,
    offset: int = 0,
):
    del admin_id
    del status_id
    del from_date
    del to_date

    result = db.execute(
        text(
            """
            SELECT *
            FROM public.fn_superadmin_get_all_tenure_extensions(
                CAST(:p_branch_id AS INTEGER),
                CAST(:p_limit AS INTEGER),
                CAST(:p_offset AS INTEGER)
            )
            """
        ),
        {
            "p_branch_id": branch_id,
            "p_limit": min(
                max(int(limit or 500), 1),
                500,
            ),
            "p_offset": max(
                int(offset or 0),
                0,
            ),
        },
    )

    data = _rows(result)

    if search:
        query = (
            str(search)
            .strip()
            .lower()
        )

        data = [
            row
            for row in data
            if query in " ".join(
                str(
                    row.get(key, "")
                )
                for key in (
                    "request_id",
                    "investment_id",
                    "investor_id",
                    "investor_name",
                    "branch_name",
                    "admin_name",
                    "status_name",
                )
            ).lower()
        ]

    return {
        "success": True,
        "data": data,
        "total": len(data),
        "limit": min(
            max(int(limit or 500), 1),
            500,
        ),
        "offset": max(
            int(offset or 0),
            0,
        ),
    }
