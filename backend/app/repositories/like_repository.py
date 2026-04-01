from __future__ import annotations

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import InvalidOperationError
from app.models.dislike import Dislike
from app.models.like import Like
from app.repositories.base_repository import BaseRepository


class LikeRepository(BaseRepository):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def create_like(self, from_user_id: int, to_user_id: int) -> Like:
        if from_user_id == to_user_id:
            raise InvalidOperationError("Пользователь не может поставить лайк самому себе.")
        # Если был дизлайк на этого пользователя, удаляем его перед лайком.
        existing_dislike = await self.get_dislike_between(from_user_id, to_user_id)
        if existing_dislike:
            await self.session.delete(existing_dislike)
        like = Like(from_user_id=from_user_id, to_user_id=to_user_id)
        self.session.add(like)
        await self._commit()
        await self.session.refresh(like)
        return like

    async def get_like_between(self, from_user_id: int, to_user_id: int) -> Like | None:
        stmt = select(Like).where(
            and_(Like.from_user_id == from_user_id, Like.to_user_id == to_user_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

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

    async def remove_like(self, from_user_id: int, to_user_id: int) -> bool:
        like = await self.get_like_between(from_user_id, to_user_id)
        if not like:
            return False
        await self.session.delete(like)
        await self._commit()
        return True

    async def create_dislike(self, from_user_id: int, to_user_id: int) -> Dislike:
        if from_user_id == to_user_id:
            raise InvalidOperationError("Пользователь не может поставить дизлайк самому себе.")
        # Если был лайк на этого пользователя, удаляем его перед дизлайком.
        existing_like = await self.get_like_between(from_user_id, to_user_id)
        if existing_like:
            await self.session.delete(existing_like)
        dislike = Dislike(from_user_id=from_user_id, to_user_id=to_user_id)
        self.session.add(dislike)
        await self._commit()
        await self.session.refresh(dislike)
        return dislike

    async def get_dislike_between(
        self, from_user_id: int, to_user_id: int
    ) -> Dislike | None:
        stmt = select(Dislike).where(
            and_(Dislike.from_user_id == from_user_id, Dislike.to_user_id == to_user_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
