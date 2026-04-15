from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.core.exceptions import DuplicateEntityError, InvalidOperationError
from app.models.user import User
from app.repositories.like_repository import LikeRepository
from app.repositories.match_repository import MatchRepository
from app.repositories.user_repository import UserRepository
from app.schemas.like import DislikeRequest, DislikeResponse, LikeRequest, LikeResponse

router = APIRouter(prefix="/api", tags=["reactions"])
logger = logging.getLogger(__name__)


def _has_active_profile(user: User) -> bool:
    return bool(user.is_active and (user.bio or user.age or user.role or user.direction or user.avatar_url))


def _validate_target_for_reaction(target_user: User | None) -> User:
    if target_user is None:
        raise HTTPException(status_code=404, detail="Пользователь не найден.")
    if target_user.is_blocked:
        raise HTTPException(status_code=400, detail="Нельзя оценивать заблокированного пользователя.")
    if not _has_active_profile(target_user):
        raise HTTPException(status_code=400, detail="Нельзя оценивать пользователя без активной анкеты.")
    return target_user


@router.post("/likes", response_model=LikeResponse)
async def create_like(
    payload: LikeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    current_user_id = current_user.id
    liked_user_id = payload.liked_user_id
    if liked_user_id == current_user_id:
        raise HTTPException(status_code=400, detail="Нельзя поставить лайк самому себе.")

    # get_current_user делает SELECT и может открыть неявную транзакцию (autobegin).
    # Для явной атомарной записи закрываем read-only транзакцию и стартуем новую.
    if db.in_transaction():
        await db.commit()

    async with db.begin():
        user_repo = UserRepository(db)
        like_repo = LikeRepository(db)
        match_repo = MatchRepository(db)

        me = await user_repo.get_by_id(current_user_id)
        if me is None:
            raise HTTPException(status_code=404, detail="Текущий пользователь не найден.")
        if not _has_active_profile(me):
            raise HTTPException(status_code=400, detail="Сначала активируйте и заполните свою анкету.")

        liked_user = _validate_target_for_reaction(await user_repo.get_by_id(liked_user_id))

        if await like_repo.has_like(me.id, liked_user.id):
            raise HTTPException(status_code=409, detail="Лайк этому пользователю уже поставлен.")

        removed_dislike = await like_repo.delete_dislike(me.id, liked_user.id, auto_commit=False)
        if removed_dislike:
            logger.info("Удален дизлайк при замене на лайк: from=%s to=%s", me.id, liked_user.id)

        await like_repo.create_like(me.id, liked_user.id, auto_commit=False)
        logger.info("Поставлен лайк: from=%s to=%s", me.id, liked_user.id)

        is_mutual = await like_repo.has_like(liked_user.id, me.id)
        if not is_mutual:
            response = LikeResponse(is_match=False, match_id=None, message="Лайк сохранен.")
            return JSONResponse(status_code=status.HTTP_200_OK, content=response.model_dump())

        existing_match = await match_repo.get_match_between(me.id, liked_user.id)
        if existing_match is not None:
            response = LikeResponse(
                is_match=True,
                match_id=existing_match.id,
                message="Взаимный лайк уже существует. Мэтч был создан ранее.",
            )
            return JSONResponse(status_code=status.HTTP_200_OK, content=response.model_dump())

        try:
            match = await match_repo.create_match(me.id, liked_user.id, auto_commit=False)
        except DuplicateEntityError:
            # Защита от гонок: если параллельный запрос успел создать мэтч.
            existing = await match_repo.get_match_between(me.id, liked_user.id)
            if existing is None:
                raise
            response = LikeResponse(
                is_match=True,
                match_id=existing.id,
                message="Взаимный лайк найден. Мэтч уже существует.",
            )
            return JSONResponse(status_code=status.HTTP_200_OK, content=response.model_dump())
        except InvalidOperationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        logger.info("Создан мэтч: match_id=%s users=(%s,%s)", match.id, me.id, liked_user.id)
        response = LikeResponse(is_match=True, match_id=match.id, message="Взаимный лайк! Мэтч создан.")
        return JSONResponse(status_code=status.HTTP_201_CREATED, content=response.model_dump())


@router.post("/dislikes", response_model=DislikeResponse)
async def create_dislike(
    payload: DislikeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DislikeResponse:
    current_user_id = current_user.id
    disliked_user_id = payload.disliked_user_id
    if disliked_user_id == current_user_id:
        raise HTTPException(status_code=400, detail="Нельзя поставить дизлайк самому себе.")

    if db.in_transaction():
        await db.commit()

    async with db.begin():
        user_repo = UserRepository(db)
        like_repo = LikeRepository(db)

        me = await user_repo.get_by_id(current_user_id)
        if me is None:
            raise HTTPException(status_code=404, detail="Текущий пользователь не найден.")
        if not _has_active_profile(me):
            raise HTTPException(status_code=400, detail="Сначала активируйте и заполните свою анкету.")

        target_user = _validate_target_for_reaction(await user_repo.get_by_id(disliked_user_id))

        if await like_repo.has_dislike(me.id, target_user.id):
            raise HTTPException(status_code=409, detail="Дизлайк этому пользователю уже поставлен.")

        removed_like = await like_repo.delete_like(me.id, target_user.id, auto_commit=False)
        if removed_like:
            logger.info("Удален лайк при замене на дизлайк: from=%s to=%s", me.id, target_user.id)

        await like_repo.create_dislike(me.id, target_user.id, auto_commit=False)
        logger.info("Поставлен дизлайк: from=%s to=%s", me.id, target_user.id)

    return DislikeResponse(success=True, message="Дизлайк сохранен.")
