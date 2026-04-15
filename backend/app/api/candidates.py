from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.core.directions import DIRECTIONS, is_supported_direction
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import CandidateResponse

router = APIRouter(prefix="/api/candidates", tags=["candidates"])
logger = logging.getLogger(__name__)


def _to_candidate_response(user: User) -> CandidateResponse:
    return CandidateResponse(
        id=user.id,
        telegram_id=user.telegram_id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        age=user.age,
        description=user.bio,
        role=user.role,
        direction=user.direction,
        photo_url=user.avatar_url,
        is_active=user.is_active,
        is_blocked=user.is_blocked,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


@router.get("", response_model=list[CandidateResponse])
async def get_candidates(
    direction: str | None = Query(default=None),
    limit: int = Query(default=1, ge=1, le=50),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[CandidateResponse]:
    if direction is not None and not is_supported_direction(direction):
        allowed = ", ".join(DIRECTIONS)
        from fastapi import HTTPException

        raise HTTPException(
            status_code=422,
            detail=f"Некорректное направление. Допустимые значения: {allowed}",
        )

    logger.debug(
        "GET /api/candidates current_user_id=%s current_role=%s direction=%s limit=%s offset=%s",
        current_user.id,
        current_user.role,
        direction,
        limit,
        offset,
    )
    repo = UserRepository(db)
    users = await repo.get_candidates(
        current_user_id=current_user.id,
        direction_filter=direction,
        limit=limit,
        offset=offset,
    )
    logger.debug(
        "GET /api/candidates current_user_id=%s returned=%s",
        current_user.id,
        len(users),
    )
    return [_to_candidate_response(user) for user in users]
