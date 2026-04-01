"""Конфигурация подключения к PostgreSQL для FastAPI + SQLAlchemy (async)."""

from __future__ import annotations

import os
from pathlib import Path
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text


def _load_local_env_file() -> None:
    """Минимальная загрузка переменных из backend/.env без внешних зависимостей."""
    env_path = Path(__file__).resolve().parents[2] / ".env"
    if not env_path.exists():
        return

    for line in env_path.read_text(encoding="utf-8").splitlines():
        clean = line.strip()
        if not clean or clean.startswith("#") or "=" not in clean:
            continue
        key, value = clean.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def _build_async_database_url() -> str:
    """Преобразует DATABASE_URL в формат драйвера asyncpg."""
    raw_url = os.getenv(
        "DATABASE_URL",
        "postgresql://connectit_user:connectit_password@localhost:5432/connectit_db",
    )
    if raw_url.startswith("postgresql+asyncpg://"):
        return raw_url
    if raw_url.startswith("postgresql://"):
        return raw_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return raw_url


_load_local_env_file()
ASYNC_DATABASE_URL = _build_async_database_url()
DB_ECHO = os.getenv("DB_ECHO", "false").lower() == "true"
DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "10"))
DB_MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "20"))
DB_POOL_TIMEOUT = int(os.getenv("DB_POOL_TIMEOUT", "30"))


class Base(DeclarativeBase):
    """Базовый declarative-класс для ORM-моделей."""


engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=DB_ECHO,
    pool_pre_ping=True,
    pool_size=DB_POOL_SIZE,
    max_overflow=DB_MAX_OVERFLOW,
    pool_timeout=DB_POOL_TIMEOUT,
)

AsyncSessionFactory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autoflush=False,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency для FastAPI: предоставляет сессию БД."""
    async with AsyncSessionFactory() as session:
        yield session


async def ping_db() -> bool:
    """Проверка доступности БД для healthcheck и startup-проверок."""
    async with AsyncSessionFactory() as session:
        result = await session.execute(text("SELECT 1"))
        return result.scalar_one() == 1


async def ensure_runtime_compatibility() -> None:
    """
    Минимальная защита от дрейфа схемы на dev-стендах.
    Позволяет безопасно добавить критичную колонку без ручной миграции.
    """
    async with AsyncSessionFactory() as session:
        await session.execute(
            text(
                "ALTER TABLE IF EXISTS users "
                "ADD COLUMN IF NOT EXISTS is_blocked BOOLEAN NOT NULL DEFAULT FALSE"
            )
        )
        await session.commit()
