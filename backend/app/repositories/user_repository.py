from __future__ import annotations

import logging

from sqlalchemy import Select, case, exists, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.models.dislike import Dislike
from app.core.exceptions import InvalidOperationError
from app.models.like import Like
from app.models.user import User
from app.repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class UserRepository(BaseRepository):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def create(self, **user_data) -> User:
        if not user_data.get("telegram_id"):
            raise InvalidOperationError("Поле telegram_id обязательно для создания пользователя.")
        user = User(**user_data)
        self.session.add(user)
        await self._commit()
        await self.session.refresh(user)
        return user

    async def get_by_id(self, user_id: int) -> User | None:
        return await self.session.get(User, user_id)

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_active(self, limit: int = 50, offset: int = 0) -> list[User]:
        stmt = (
            select(User)
            .where(User.is_active.is_(True))
            .order_by(User.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_candidates(
        self,
        current_user_id: int,
        direction_filter: str | None = None,
        limit: int = 1,
        offset: int = 0,
    ) -> list[User]:
        logger.debug(
            "get_candidates: current_user_id=%s direction_filter=%s limit=%s offset=%s",
            current_user_id,
            direction_filter,
            limit,
            offset,
        )

        # Важно: исключаем тех, кого пользователь уже оценил (лайк/дизлайк),
        # через NOT EXISTS в одном SQL-запросе без дополнительных проходов.
        liked_subquery: Select[tuple[int]] = select(Like.id).where(
            Like.from_user_id == current_user_id,
            Like.to_user_id == User.id,
        )
        disliked_subquery: Select[tuple[int]] = select(Dislike.id).where(
            Dislike.from_user_id == current_user_id,
            Dislike.to_user_id == User.id,
        )
        current_user_alias = aliased(User)
        current_role_subquery = (
            select(current_user_alias.role)
            .where(current_user_alias.id == current_user_id)
            .scalar_subquery()
        )
        opposite_role_expr = case(
            (current_role_subquery == "mentor", "mentee"),
            (current_role_subquery == "mentee", "mentor"),
            else_=None,
        )

        stmt = (
            select(User)
            .where(
                User.id != current_user_id,
                User.is_active.is_(True),
                User.is_blocked.is_(False),
                ~exists(liked_subquery),
                ~exists(disliked_subquery),
                # Менторы видят только менти, менти видят только менторов.
                # Если у текущего пользователя роль не задана, opposite_role_expr = NULL,
                # и условие не выполнится (вернется пустой список).
                User.role == opposite_role_expr,
            )
            .order_by(User.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        if direction_filter is not None:
            stmt = stmt.where(User.direction == direction_filter)

        result = await self.session.execute(stmt)
        candidates = list(result.scalars().all())
        logger.debug(
            "get_candidates: current_user_id=%s returned=%s",
            current_user_id,
            len(candidates),
        )
        return candidates

    async def update(self, user: User, **changes) -> User:
        for field, value in changes.items():
            setattr(user, field, value)
        await self._commit()
        await self.session.refresh(user)
        return user

    async def delete(self, user: User) -> None:
        await self.session.delete(user)
        await self._commit()
