"""
Telegram-бот ConnectIT: кнопка «Открыть приложение» (Web App).

WEB_APP_URL задаётся в окружении или в backend/.env — не хардкодить в коде.

Почему localhost не открывается с телефона в Telegram:
  - «localhost» на телефоне — это сам телефон, не ваш ПК.
  - Нужен либо HTTPS-туннель (ngrok, cloudflared), либо IP в одной Wi‑Fi сети
    (иногда Telegram всё равно требует HTTPS для Web App — надёжнее туннель).

Локальная разработка с телефона (типовой сценарий):
  1) Поднять backend:  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
  2) Собрать и раздать Flutter web, например:
       cd frontend && flutter build web
       cd frontend/build/web && python -m http.server 8080 --bind 0.0.0.0
  3) Туннель на фронт (публичный HTTPS):
       ngrok http 8080
     Скопировать URL вида https://xxxx.ngrok-free.app в WEB_APP_URL.
  4) Второй туннель на API (если приложение ходит на тот же хост, что и браузер):
       ngrok http 8000
     В Flutter/web задать API_BASE_URL=https://yyyy.ngrok-free.app
  5) В backend/.env выставить WEB_APP_URL и перезапустить бота.

Запуск бота локально:
  cd backend && python -m app.bot

Запуск бота в Docker: см. docker-compose-dev.yml (сервис bot).
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from pathlib import Path

from aiogram import Bot, Dispatcher, Router
from aiogram.filters import CommandStart
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    WebAppInfo,
)
from dotenv import load_dotenv

# Загружаем backend/.env при локальном запуске; в Docker переменные обычно уже заданы.
_env_path = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(_env_path, override=False)

BOT_TOKEN = os.getenv("BOT_TOKEN")
# Публичный URL веб-приложения (страница Flutter Web), который откроется в WebView Telegram.
WEB_APP_URL = (os.getenv("WEB_APP_URL") or "").strip().rstrip("/")


def _validate_web_app_url(url: str) -> None:
    if not url:
        logging.error(
            "WEB_APP_URL не задан. Укажите в backend/.env или переменных окружения, "
            "например: WEB_APP_URL=https://xxxx.ngrok-free.app"
        )
        sys.exit(1)
    if not (url.startswith("http://") or url.startswith("https://")):
        logging.error("WEB_APP_URL должен начинаться с http:// или https://")
        sys.exit(1)
    # Локальный адрес с телефона не откроется — только предупреждение.
    if "localhost" in url or "127.0.0.1" in url:
        logging.warning(
            "WEB_APP_URL указывает на localhost/127.0.0.1 — из Telegram на телефоне "
            "это не сработает. Для теста с телефона используйте ngrok/cloudflared или IP в LAN + HTTPS."
        )


router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Открыть приложение",
                    web_app=WebAppInfo(url=WEB_APP_URL),
                )
            ]
        ]
    )
    await message.answer(
        "ConnectIT — найди своего наставника в IT.\n\n"
        "Нажми кнопку ниже, чтобы открыть приложение.",
        reply_markup=keyboard,
    )


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    _validate_web_app_url(WEB_APP_URL)
    if not BOT_TOKEN:
        logging.error("BOT_TOKEN не задан (backend/.env или переменная окружения).")
        sys.exit(1)

    logging.info("Запуск бота, WEB_APP_URL=%s", WEB_APP_URL)

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
