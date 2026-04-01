from __future__ import annotations

import asyncio

from sqlalchemy import text

from app.core.database import AsyncSessionFactory
from app.core.exceptions import DuplicateEntityError, InvalidOperationError, RepositoryError
from app.repositories.like_repository import LikeRepository
from app.repositories.match_repository import MatchRepository
from app.repositories.report_repository import ReportRepository
from app.repositories.user_repository import UserRepository


async def main() -> None:
    try:
        async with AsyncSessionFactory() as session:
            # 1) Проверяем, что подключение к БД работает.
            ping_result = await session.execute(text("SELECT 1 AS ok"))
            print(f"DB ping: {ping_result.scalar_one()}")

            user_repo = UserRepository(session)
            like_repo = LikeRepository(session)
            match_repo = MatchRepository(session)
            report_repo = ReportRepository(session)

        # 2) Создаем тестовых пользователей (или берем существующих).
            user1 = await user_repo.get_by_telegram_id(1000000001)
            if not user1:
                user1 = await user_repo.create(
                    telegram_id=1000000001,
                    username="mentor_anna",
                    first_name="Anna",
                    city="Moscow",
                    age=24,
                    bio="Python наставник",
                    skills="Python, FastAPI, PostgreSQL",
                )

            user2 = await user_repo.get_by_telegram_id(1000000002)
            if not user2:
                user2 = await user_repo.create(
                    telegram_id=1000000002,
                    username="student_ivan",
                    first_name="Ivan",
                    city="Kazan",
                    age=21,
                    bio="Ищу наставника по backend",
                    skills="SQL, Docker",
                )

        # 3) Создаем лайки в обе стороны -> формируем мэтч.
            if not await like_repo.get_like_between(user1.id, user2.id):
                await like_repo.create_like(user1.id, user2.id)
            if not await like_repo.get_like_between(user2.id, user1.id):
                await like_repo.create_like(user2.id, user1.id)

            is_mutual = await like_repo.has_mutual_like(user1.id, user2.id)
            if is_mutual:
                match = await match_repo.create_if_not_exists(user1.id, user2.id)
                print(f"Match created/found: {match}")

        # 4) Создаем тестовую жалобу (при необходимости).
            reports = await report_repo.list_for_user(user2.id)
            if not reports:
                report = await report_repo.create(
                    reporter_id=user1.id,
                    reported_user_id=user2.id,
                    reason="spam",
                    details="Тестовая жалоба для проверки репозитория",
                )
                print(f"Report created: {report}")

            print("Test data check completed successfully.")
    except (DuplicateEntityError, InvalidOperationError, RepositoryError) as exc:
        print(f"Repository error: {exc}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
