from sqlalchemy import text
from sqlalchemy.orm import Session


def get_superadmin_profile(
    db: Session,
    user_id: int,
):
    result = db.execute(
        text(
            """
            SELECT *
            FROM public.fn_superadmin_get_profile(
                :p_user_id
            )
            """
        ),
        {
            "p_user_id": user_id,
        },
    )

    row = result.mappings().first()

    if not row:
        return None

    return dict(row)


def update_superadmin_profile(
    db: Session,
    user_id: int,
    full_name: str,
    email: str,
    mobile: str,
):
    result = db.execute(
        text(
            """
            SELECT *
            FROM public.fn_superadmin_update_profile(
                :p_user_id,
                :p_full_name,
                :p_email,
                :p_mobile
            )
            """
        ),
        {
            "p_user_id": user_id,
            "p_full_name": full_name.strip(),
            "p_email": email.strip(),
            "p_mobile": mobile.strip(),
        },
    )

    row = result.mappings().first()

    db.commit()

    if row:
        return dict(row)

    return get_superadmin_profile(
        db=db,
        user_id=user_id,
    )