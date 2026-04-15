from __future__ import annotations

from pydantic import BaseModel, Field


class LikeRequest(BaseModel):
    liked_user_id: int = Field(gt=0)


class LikeResponse(BaseModel):
    is_match: bool
    match_id: int | None = None
    message: str


class DislikeRequest(BaseModel):
    disliked_user_id: int = Field(gt=0)


class DislikeResponse(BaseModel):
    success: bool
    message: str
