from __future__ import annotations

import logging

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import InvalidOperationError
from app.models.dislike import Dislike
from app.models.like import Like
from app.repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class LikeRepository(BaseRepository):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def create_like(
        self,
        from_user_id: int,
        to_user_id: int,
        *,
        auto_commit: bool = True,
    ) -> Like:
        if from_user_id == to_user_id:
            raise InvalidOperationError("Пользователь не может поставить лайк самому себе.")

        like = Like(from_user_id=from_user_id, to_user_id=to_user_id)
        self.session.add(like)
        if auto_commit:
            await self._commit()
            await self.session.refresh(like)
        else:
            await self.session.flush()
        return like

    async def get_like_between(self, from_user_id: int, to_user_id: int) -> Like | None:
        stmt = select(Like).where(
            and_(Like.from_user_id == from_user_id, Like.to_user_id == to_user_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def has_like(self, from_user_id: int, to_user_id: int) -> bool:
        return (await self.get_like_between(from_user_id, to_user_id)) is not None

    async def has_mutual_like(self, user_a_id: int, user_b_id: int) -> bool:
        stmt = select(Like).where(
            or_(
                and_(Like.from_user_id == user_a_id, Like.to_user_id == user_b_id),
                and_(Like.from_user_id == user_b_id, Like.to_user_id == user_a_id),
            )
        )
        result = await self.session.execute(stmt)
        likes = list(result.scalars().all())
        return len(likes) == 2

    async def delete_like(
        self,
        from_user_id: int,
        to_user_id: int,
        *,
        auto_commit: bool = True,
    ) -> bool:
        like = await self.get_like_between(from_user_id, to_user_id)
        if not like:
            return False
        await self.session.delete(like)
        if auto_commit:
            await self._commit()
        else:
            await self.session.flush()
        return True

    async def remove_like(self, from_user_id: int, to_user_id: int) -> bool:
        # Совместимость со старым именем.
        return await self.delete_like(from_user_id, to_user_id, auto_commit=True)

    async def create_dislike(
        self,
        from_user_id: int,
        to_user_id: int,
        *,
        auto_commit: bool = True,
    ) -> Dislike:
        if from_user_id == to_user_id:
            raise InvalidOperationError("Пользователь не может поставить дизлайк самому себе.")

        dislike = Dislike(from_user_id=from_user_id, to_user_id=to_user_id)
        self.session.add(dislike)
        if auto_commit:
            await self._commit()
            await self.session.refresh(dislike)
        else:
            await self.session.flush()
        return dislike

    async def get_dislike_between(
        self, from_user_id: int, to_user_id: int
    ) -> Dislike | None:
        stmt = select(Dislike).where(
            and_(Dislike.from_user_id == from_user_id, Dislike.to_user_id == to_user_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def has_dislike(self, from_user_id: int, to_user_id: int) -> bool:
        return (await self.get_dislike_between(from_user_id, to_user_id)) is not None

    async def delete_dislike(
        self,
        from_user_id: int,
        to_user_id: int,
        *,
        auto_commit: bool = True,
    ) -> bool:
        dislike = await self.get_dislike_between(from_user_id, to_user_id)
        if not dislike:
            return False
        await self.session.delete(dislike)
        if auto_commit:
            await self._commit()
        else:
            await self.session.flush()
        return True
