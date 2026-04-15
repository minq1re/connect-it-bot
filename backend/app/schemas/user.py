from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.directions import DIRECTIONS, is_supported_direction


class UserCreate(BaseModel):
    first_name: str = Field(min_length=1, max_length=128)
    age: int = Field(ge=14, le=100)
    description: str = Field(min_length=1, max_length=2000)
    role: Literal["mentor", "mentee"]
    direction: str = Field(min_length=1, max_length=128)

    @field_validator("direction")
    @classmethod
    def validate_direction(cls, value: str) -> str:
        if not is_supported_direction(value):
            raise ValueError(f"Направление должно быть одним из: {', '.join(DIRECTIONS)}")
        return value


class UserUpdate(BaseModel):
    first_name: str | None = Field(default=None, min_length=1, max_length=128)
    age: int | None = Field(default=None, ge=14, le=100)
    description: str | None = Field(default=None, min_length=1, max_length=2000)
    role: Literal["mentor", "mentee"] | None = None
    direction: str | None = Field(default=None, min_length=1, max_length=128)

    @field_validator("direction")
    @classmethod
    def validate_direction(cls, value: str | None) -> str | None:
        if value is None:
            return value
        if not is_supported_direction(value):
            raise ValueError(f"Направление должно быть одним из: {', '.join(DIRECTIONS)}")
        return value


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    telegram_id: int
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    age: int | None = None
    description: str | None = None
    role: str | None = None
    direction: str | None = None
    photo_url: str | None = None
    is_active: bool
    is_blocked: bool
    created_at: datetime
    updated_at: datetime


class CandidateResponse(UserResponse):
    """Ответ для выдачи кандидатов на мэтчинг."""


class ToggleActiveResponse(BaseModel):
    is_active: bool
    message: str
