#!/usr/bin/env python3
"""
Генерирует валидную строку initData (подпись как у Telegram WebApp) для локальной
отладки Flutter Web в обычном браузере, где нет Telegram.WebApp.

Использование:
  cd backend
  python scripts/dev_telegram_init_data.py

Скопируйте выведенную команду flutter build web / flutter run — после этого
кнопка «Продолжить через Telegram» заработает без встроенного клиента Telegram.

Пересоздавайте строку раз в сутки (ограничение auth_date на backend) или после смены BOT_TOKEN.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import sys
import time
import urllib.parse
from pathlib import Path

_BACKEND = Path(__file__).resolve().parents[1]


def _load_bot_token() -> str:
    try:
        from dotenv import load_dotenv

        load_dotenv(_BACKEND / ".env")
    except ImportError:
        pass
    token = os.getenv("BOT_TOKEN", "").strip()
    if not token:
        print("Задайте BOT_TOKEN в backend/.env", file=sys.stderr)
        sys.exit(1)
    return token


def build_init_data(bot_token: str, user_id: int, first_name: str, username: str) -> str:
    user_obj: dict = {
        "id": user_id,
        "first_name": first_name,
        "username": username,
    }
    user_json = json.dumps(user_obj, separators=(",", ":"), ensure_ascii=False)
    fields = {
        "user": user_json,
        "auth_date": str(int(time.time())),
    }
    check_data_string = "\n".join(f"{k}={fields[k]}" for k in sorted(fields.keys()))
    secret_key = hmac.new(
        b"WebAppData",
        bot_token.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).digest()
    data_hash = hmac.new(
        secret_key,
        check_data_string.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).hexdigest()
    fields["hash"] = data_hash
    return urllib.parse.urlencode(fields)


def main() -> None:
    token = _load_bot_token()
    user_id = int(os.environ.get("DEV_INIT_USER_ID", "123456789"))
    first_name = os.environ.get("DEV_INIT_FIRST_NAME", "Local Dev")
    username = os.environ.get("DEV_INIT_USERNAME", "localdev")
    init_data = build_init_data(token, user_id, first_name, username)

    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    print("Скопируйте одну из команд (PowerShell):\n")
    escaped = init_data.replace('"', '`"')
    print(f'flutter build web --dart-define=TELEGRAM_INIT_DATA="{escaped}"')
    print("\nИли быстрый запуск в Chrome:")
    print(f'flutter run -d chrome --dart-define=TELEGRAM_INIT_DATA="{escaped}"')


if __name__ == "__main__":
    main()
