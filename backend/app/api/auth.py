from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_user
from app.models.user import User
from app.schemas.auth import AuthResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _detect_profile(user: User) -> bool:
    # Профиль считаем заполненным, если есть минимум bio или age, или city.
    return bool(user.bio or user.age or user.city)


@router.get("/me", response_model=AuthResponse)
async def auth_me(current_user: User = Depends(get_current_user)) -> AuthResponse:
    return AuthResponse(
        id=current_user.id,
        username=current_user.username,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        is_blocked=current_user.is_blocked,
        has_profile=_detect_profile(current_user),
    )
