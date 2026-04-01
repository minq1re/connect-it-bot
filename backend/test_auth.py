from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import os
import time
from urllib.parse import urlencode

from app.core.database import AsyncSessionFactory, ensure_runtime_compatibility
from app.core.security import extract_user_from_init_data, validate_telegram_init_data
from app.api.dependencies import get_current_user
from app.api.exceptions_handlers import BlockedUserException
from app.repositories.user_repository import UserRepository


def build_init_data(user_payload: dict, bot_token: str, auth_date: int | None = None) -> str:
    auth_ts = auth_date or int(time.time())
    data: dict[str, str] = {
        "auth_date": str(auth_ts),
        "query_id": "AAHdF6IQAAAAAN0XohDhrOrc",
        "user": json.dumps(user_payload, separators=(",", ":"), ensure_ascii=False),
    }
    check_data = "\n".join(f"{k}={v}" for k, v in sorted(data.items()))
    secret_key = hmac.new(b"WebAppData", bot_token.encode("utf-8"), hashlib.sha256).digest()
    data_hash = hmac.new(secret_key, check_data.encode("utf-8"), hashlib.sha256).hexdigest()
    data["hash"] = data_hash
    return urlencode(data)


async def set_blocked(telegram_id: int, blocked: bool) -> None:
    async with AsyncSessionFactory() as session:
        repo = UserRepository(session)
        user = await repo.get_by_telegram_id(telegram_id)
        if user:
            await repo.update(user, is_blocked=blocked)


async def run_tests() -> None:
    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        raise RuntimeError("Для test_auth.py нужно задать BOT_TOKEN в окружении или .env")

    user_payload = {
        "id": 123456789,
        "first_name": "Test",
        "last_name": "User",
        "username": "test_user",
        "language_code": "ru",
    }
    valid_init_data = build_init_data(user_payload, bot_token)
    invalid_init_data = valid_init_data.replace("hash=", "hash=broken")

    await ensure_runtime_compatibility()

    # 1) Корректная подпись (проверка криптографии)
    validated = validate_telegram_init_data(valid_init_data)
    extracted = extract_user_from_init_data(valid_init_data)
    print("valid_init_data: ok", validated.get("auth_date"), extracted.id)

    # 2) Некорректная подпись -> ожидаем ошибку
    try:
        validate_telegram_init_data(invalid_init_data)
        raise AssertionError("Ожидалась ошибка для некорректной подписи.")
    except Exception:
        print("invalid_init_data: rejected as expected")

    # 3) Создание нового пользователя и получение существующего
    async with AsyncSessionFactory() as session:
        created_or_loaded = await get_current_user(valid_init_data, session)
        loaded_again = await get_current_user(valid_init_data, session)
        print("existing_user: ok", loaded_again.id)
        assert created_or_loaded.telegram_id == user_payload["id"]
        assert created_or_loaded.id == loaded_again.id

    # 4) Блокированный пользователь
    await set_blocked(user_payload["id"], True)
    try:
        async with AsyncSessionFactory() as session:
            await get_current_user(valid_init_data, session)
        raise AssertionError("Ожидалась ошибка BlockedUserException.")
    except BlockedUserException:
        print("blocked_user: rejected as expected")
    finally:
        await set_blocked(user_payload["id"], False)

    print("All auth tests passed.")


if __name__ == "__main__":
    asyncio.run(run_tests())
