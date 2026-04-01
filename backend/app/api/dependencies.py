from __future__ import annotations

import logging

from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.exceptions_handlers import BlockedUserException, UnauthorizedException
from app.core.database import get_db
from app.core.security import extract_user_from_init_data
from app.models.user import User
from app.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)


async def get_current_user(
    x_telegram_init_data: str = Header(..., alias="X-Telegram-Init-Data"),
    db: AsyncSession = Depends(get_db),
) -> User:
    try:
        tg_user = extract_user_from_init_data(x_telegram_init_data)
        logger.debug("Попытка аутентификации telegram_id=%s", tg_user.id)
    except Exception as exc:
        logger.warning("Ошибка валидации initData: %s", str(exc))
        raise UnauthorizedException("Невалидный initData Telegram WebApp.") from exc

    repo = UserRepository(db)
    user = await repo.get_by_telegram_id(tg_user.id)
    if user is None:
        user = await repo.create(
            telegram_id=tg_user.id,
            username=tg_user.username,
            first_name=tg_user.first_name,
            last_name=tg_user.last_name,
        )
        logger.info("Создан новый пользователь telegram_id=%s", tg_user.id)
    else:
        # Актуализируем основные Telegram-поля при повторном входе.
        user = await repo.update(
            user,
            username=tg_user.username,
            first_name=tg_user.first_name,
            last_name=tg_user.last_name,
        )

    if user.is_blocked:
        logger.warning("Заблокированный пользователь telegram_id=%s", tg_user.id)
        raise BlockedUserException("Ваш аккаунт заблокирован. Обратитесь в поддержку.")

    return user
