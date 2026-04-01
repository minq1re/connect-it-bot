from __future__ import annotations

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import InvalidOperationError
from app.models.match import Match
from app.repositories.base_repository import BaseRepository


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

    async def create(self, user_a_id: int, user_b_id: int, is_active: bool = True) -> Match:
        user1_id, user2_id = self.normalize_pair(user_a_id, user_b_id)
        match = Match(user1_id=user1_id, user2_id=user2_id, is_active=is_active)
        self.session.add(match)
        await self._commit()
        await self.session.refresh(match)
        return match

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
