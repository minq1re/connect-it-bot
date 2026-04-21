from __future__ import annotations

import logging

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.repositories.match_repository import MatchRepository
from app.repositories.user_repository import UserRepository
from app.schemas.match import MatchItemResponse

router = APIRouter(prefix="/api/matches", tags=["matches"])
logger = logging.getLogger(__name__)


@router.get("", response_model=list[MatchItemResponse])
async def list_matches(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[MatchItemResponse]:
    match_repo = MatchRepository(db)
    user_repo = UserRepository(db)
    matches = await match_repo.list_user_matches(current_user.id, only_active=True)
    items: list[MatchItemResponse] = []

    for match in matches:
        partner_id = match.user2_id if match.user1_id == current_user.id else match.user1_id
        partner = await user_repo.get_by_id(partner_id)
        if partner is None:
            logger.warning("Партнер по мэтчу не найден: match_id=%s partner_id=%s", match.id, partner_id)
            continue
        items.append(
            MatchItemResponse(
                match_id=match.id,
                partner_user_id=partner.id,
                partner_telegram_id=partner.telegram_id,
                partner_first_name=partner.first_name,
                partner_last_name=partner.last_name,
                partner_age=partner.age,
                partner_role=partner.role,  # type: ignore[arg-type]
                partner_direction=partner.direction,
                partner_photo_url=partner.avatar_url,
                created_at=match.created_at,
            )
        )
    return items
