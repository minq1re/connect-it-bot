from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import time
from urllib.parse import parse_qsl

from app.schemas.auth import TelegramUserData

logger = logging.getLogger(__name__)

MAX_AUTH_AGE_SECONDS = 24 * 60 * 60


def _get_bot_token() -> str:
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise ValueError("BOT_TOKEN не задан в переменных окружения.")
    return token


def validate_telegram_init_data(init_data: str) -> dict:
    """
    Полностью оффлайн-валидация initData по алгоритму Telegram WebApp.
    """
    if not init_data:
        logger.debug("Пустой initData при валидации.")
        raise ValueError("Пустой initData.")

    parsed_pairs = parse_qsl(init_data, keep_blank_values=True, strict_parsing=True)
    data = dict(parsed_pairs)

    provided_hash = data.pop("hash", None)
    if not provided_hash:
        logger.debug("В initData отсутствует hash.")
        raise ValueError("В initData отсутствует hash.")

    auth_date_raw = data.get("auth_date")
    if not auth_date_raw or not auth_date_raw.isdigit():
        logger.debug("В initData отсутствует или некорректен auth_date.")
        raise ValueError("В initData отсутствует или некорректен auth_date.")

    auth_date = int(auth_date_raw)
    now = int(time.time())
    if now - auth_date > MAX_AUTH_AGE_SECONDS:
        logger.debug("initData просрочен по auth_date.")
        raise ValueError("initData просрочен.")

    check_data_string = "\n".join(f"{key}={value}" for key, value in sorted(data.items()))
    secret_key = hmac.new(
        key=b"WebAppData",
        msg=_get_bot_token().encode("utf-8"),
        digestmod=hashlib.sha256,
    ).digest()
    calculated_hash = hmac.new(
        key=secret_key,
        msg=check_data_string.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(calculated_hash, provided_hash):
        logger.debug("initData не прошел проверку подписи.")
        raise ValueError("Невалидная подпись initData.")

    logger.debug("initData успешно валидирован.")
    return data


def extract_user_from_init_data(init_data: str) -> TelegramUserData:
    payload = validate_telegram_init_data(init_data)
    raw_user = payload.get("user")
    if not raw_user:
        logger.debug("В initData отсутствует поле user.")
        raise ValueError("В initData отсутствует поле user.")

    try:
        user_dict = json.loads(raw_user)
    except json.JSONDecodeError as exc:
        logger.debug("Поле user в initData не является валидным JSON.")
        raise ValueError("Поле user в initData некорректно.") from exc

    return TelegramUserData(**user_dict)
