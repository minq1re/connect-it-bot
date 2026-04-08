from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class UserCreate(BaseModel):
    first_name: str = Field(min_length=1, max_length=128)
    age: int = Field(ge=14, le=100)
    description: str = Field(min_length=1, max_length=2000)
    role: Literal["mentor", "mentee"]
    direction: str = Field(min_length=1, max_length=128)


class UserUpdate(BaseModel):
    first_name: str | None = Field(default=None, min_length=1, max_length=128)
    age: int | None = Field(default=None, ge=14, le=100)
    description: str | None = Field(default=None, min_length=1, max_length=2000)
    role: Literal["mentor", "mentee"] | None = None
    direction: str | None = Field(default=None, min_length=1, max_length=128)


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


class ToggleActiveResponse(BaseModel):
    is_active: bool
    message: str
