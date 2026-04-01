from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class TelegramUserData(BaseModel):
    id: int
    first_name: str | None = None
    last_name: str | None = None
    username: str | None = None
    language_code: str | None = None
    allows_write_to_pm: bool | None = None


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    is_blocked: bool


class AuthResponse(UserResponse):
    has_profile: bool
