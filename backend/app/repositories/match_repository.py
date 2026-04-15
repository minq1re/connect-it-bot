from __future__ import annotations

import logging

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DuplicateEntityError
from app.core.exceptions import InvalidOperationError
from app.models.match import Match
from app.repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class MatchRepository(BaseRepository):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    @staticmethod
    def normalize_pair(user_a_id: int, user_b_id: int) -> tuple[int, int]:
        # Храним пару строго в одном порядке, чтобы избежать дублей.
        if user_a_id == user_b_id:
            raise InvalidOperationError("Нельзя создать мэтч пользователя с самим собой.")
        return (user_a_id, user_b_id) if user_a_id < user_b_id else (user_b_id, user_a_id)

    async def get_by_pair(self, user_a_id: int, user_b_id: int) -> Match | None:
        user1_id, user2_id = self.normalize_pair(user_a_id, user_b_id)
        stmt = select(Match).where(
            and_(Match.user1_id == user1_id, Match.user2_id == user2_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_match_between(self, user_a_id: int, user_b_id: int) -> Match | None:
        return await self.get_by_pair(user_a_id, user_b_id)

    async def create(
        self,
        user_a_id: int,
        user_b_id: int,
        is_active: bool = True,
        *,
        auto_commit: bool = True,
    ) -> Match:
        user1_id, user2_id = self.normalize_pair(user_a_id, user_b_id)
        match = Match(user1_id=user1_id, user2_id=user2_id, is_active=is_active)
        self.session.add(match)
        if auto_commit:
            await self._commit()
            await self.session.refresh(match)
        else:
            await self.session.flush()
        return match

    async def create_match(
        self,
        user1_id: int,
        user2_id: int,
        *,
        auto_commit: bool = True,
    ) -> Match:
        existing = await self.get_match_between(user1_id, user2_id)
        if existing is not None:
            raise DuplicateEntityError("Мэтч между этими пользователями уже существует.")
        return await self.create(user1_id, user2_id, is_active=True, auto_commit=auto_commit)

    async def create_if_not_exists(self, user_a_id: int, user_b_id: int) -> Match:
        existing = await self.get_by_pair(user_a_id, user_b_id)
        if existing:
            return existing
        return await self.create(user_a_id, user_b_id, is_active=True)

    async def list_user_matches(self, user_id: int, only_active: bool = True) -> list[Match]:
        stmt = select(Match).where(or_(Match.user1_id == user_id, Match.user2_id == user_id))
        if only_active:
            stmt = stmt.where(Match.is_active.is_(True))
        stmt = stmt.order_by(Match.created_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_unsent_matches(self, limit: int = 10) -> list[Match]:
        stmt = (
            select(Match)
            .where(
                Match.is_active.is_(True),
                Match.notification_sent.is_(False),
            )
            .order_by(Match.created_at.asc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def mark_notification_sent(
        self,
        match_id: int,
        *,
        auto_commit: bool = True,
    ) -> bool:
        match = await self.session.get(Match, match_id)
        if match is None:
            return False
        match.notification_sent = True
        if auto_commit:
            await self._commit()
        else:
            await self.session.flush()
        return True
