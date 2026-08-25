from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from sqlalchemy.orm import Session

from app.database import get_db
from app.services.landing_service import (
    get_public_home_stats,
)


router = APIRouter(
    prefix="/public",
    tags=["Public"],
)


@router.get("/home-stats")
def public_home_stats(
    db: Session = Depends(get_db),
):
    """
    Public homepage statistics.

    This endpoint does not require authentication.
    """
    try:
        data = get_public_home_stats(
            db=db
        )

        return {
            "success": True,
            "data": data,
        }

    except HTTPException:
        raise

    except Exception as exc:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )