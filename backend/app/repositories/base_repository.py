from __future__ import annotations

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DuplicateEntityError, RepositoryError


class BaseRepository:
    """Базовый репозиторий с безопасным commit/rollback."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def _commit(self) -> None:
        try:
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise DuplicateEntityError("Нарушены ограничения целостности данных.") from exc
        except SQLAlchemyError as exc:
            await self.session.rollback()
            raise RepositoryError("Ошибка работы с базой данных.") from exc
