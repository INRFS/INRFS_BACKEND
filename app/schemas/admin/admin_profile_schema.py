from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class AdminProfileResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None


class AdminProfileUpdate(BaseModel):
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
    )

    email: Optional[str] = Field(
        default=None,
        max_length=255,
    )

    mobile: Optional[str] = Field(
        default=None,
        max_length=20,
    )