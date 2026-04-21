from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class MatchItemResponse(BaseModel):
    match_id: int
    partner_user_id: int
    partner_telegram_id: int
    partner_first_name: str | None = None
    partner_last_name: str | None = None
    partner_age: int | None = None
    partner_role: Literal["mentor", "mentee"] | None = None
    partner_direction: str | None = None
    partner_photo_url: str | None = None
    created_at: datetime
