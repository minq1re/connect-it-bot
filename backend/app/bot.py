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

Если при старте polling падает с TelegramNetworkError / Cannot connect to api.telegram.org:
  это исходящий доступ к Bot API (не связано с WEB_APP_URL). Частые причины — блокировка
  Telegram, firewall, нестабильный DNS. Варианты: системный VPN, прокси на выход
  (переменная TELEGRAM_PROXY_URL или HTTPS_PROXY, см. код ниже), либо запуск бота на VPS
  с нормальным доступом к api.telegram.org.

ВАЖНО — MTProto из «Настройки → Данные и память → Прокси» в Telegram:
  это протокол только для приложения Telegram. Бот (Python + aiohttp) к api.telegram.org
  ходит по HTTPS и понимает только HTTP-прокси или SOCKS5 (например http://127.0.0.1:7890
  или socks5://127.0.0.1:1080), которые обычно даёт Clash / v2rayN / аналог на ПК.
  Hostname вида *.blancproxy.link:443 из MTProto в TELEGRAM_PROXY_URL указать нельзя —
  формат другой. Нужен локальный HTTP/SOCKS или VPS, где api.telegram.org доступен напрямую.
"""

from __future__ import annotations

import asyncio
from contextlib import suppress
import logging
import os
import random
import sys
from pathlib import Path

from aiohttp import ClientSession
from aiohttp.hdrs import USER_AGENT
from aiohttp.http import SERVER_SOFTWARE
from aiogram import Bot, Dispatcher, Router
from aiogram.__meta__ import __version__
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.exceptions import TelegramNetworkError
from aiogram.filters import CommandStart
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    WebAppInfo,
)
from dotenv import load_dotenv

from app.core.database import AsyncSessionFactory
from app.models.match import Match
from app.repositories.match_repository import MatchRepository
from app.repositories.user_repository import UserRepository

# Загружаем .env: рядом с пакетом app (папка backend) и из текущей рабочей директории.
_backend_dir = Path(__file__).resolve().parents[1]
for _candidate in (_backend_dir / ".env", Path.cwd() / ".env"):
    if _candidate.is_file():
        load_dotenv(_candidate, override=False)


def _parse_windows_proxy_server(raw: str) -> str | None:
    """Преобразует ProxyServer из реестра WinINET в URL для aiohttp."""
    raw = raw.strip()
    if not raw:
        return None
    if "=" in raw:
        for part in (p.strip() for p in raw.split(";") if p.strip()):
            low = part.lower()
            if low.startswith("https="):
                host = part.split("=", 1)[1].strip()
                return host if "://" in host else f"http://{host}"
        for part in (p.strip() for p in raw.split(";") if p.strip()):
            low = part.lower()
            if low.startswith("http="):
                host = part.split("=", 1)[1].strip()
                return host if "://" in host else f"http://{host}"
        return None
    if "://" in raw:
        return raw
    return f"http://{raw}"


def _apply_windows_system_proxy_if_needed() -> None:
    """
    VPN часто включает «системный прокси» в Windows, но не задаёт HTTPS_PROXY для консоли.
    Тогда Python до api.telegram.org не ходит — подставляем прокси из реестра.
    """
    if os.getenv("TELEGRAM_PROXY_URL") or os.getenv("HTTPS_PROXY") or os.getenv("HTTP_PROXY"):
        return
    if sys.platform != "win32":
        return
    try:
        import winreg
    except ImportError:
        return
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Internet Settings",
        )
        enable, _ = winreg.QueryValueEx(key, "ProxyEnable")
        if int(enable) != 1:
            return
        server, _ = winreg.QueryValueEx(key, "ProxyServer")
    except OSError:
        return
    url = _parse_windows_proxy_server(str(server))
    if url:
        os.environ["HTTPS_PROXY"] = url


_apply_windows_system_proxy_if_needed()

BOT_TOKEN = os.getenv("BOT_TOKEN")
# Публичный URL веб-приложения (страница Flutter Web), который откроется в WebView Telegram.
WEB_APP_URL = (os.getenv("WEB_APP_URL") or "").strip().rstrip("/")
# Исходящий прокси до api.telegram.org (HTTP/HTTPS/SOCKS5 — как поддерживает aiohttp).
# Пример локального клиента VPN: TELEGRAM_PROXY_URL=http://127.0.0.1:7890
TELEGRAM_PROXY_URL = (
    (
        os.getenv("TELEGRAM_PROXY_URL")
        or os.getenv("HTTPS_PROXY")
        or os.getenv("HTTP_PROXY")
        or ""
    ).strip()
    or None
)


class TrustEnvAiohttpSession(AiohttpSession):
    """ClientSession с trust_env=True — подхватывает HTTP(S)_PROXY из окружения."""

    async def create_session(self) -> ClientSession:
        if self._should_reset_connector:
            await self.close()
        if self._session is None or self._session.closed:
            self._session = ClientSession(
                connector=self._connector_type(**self._connector_init),
                headers={
                    USER_AGENT: f"{SERVER_SOFTWARE} aiogram/{__version__}",
                },
                trust_env=True,
            )
            self._should_reset_connector = False
        return self._session


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
            "WEB_APP_URL — localhost: с телефона не откроется; для полноценного Web App в Telegram "
            "нужен HTTPS (туннель). HTTP на localhost: кнопка будет обычной ссылкой в браузер."
        )


def _start_reply_markup() -> InlineKeyboardMarkup:
    """
    У Telegram для поля web_app разрешены только HTTPS URL.
    Локальный http:// — иначе InlineKeyboardButton(url=...) (открывается в браузере).
    """
    if WEB_APP_URL.lower().startswith("https://"):
        btn = InlineKeyboardButton(
            text="Открыть приложение",
            web_app=WebAppInfo(url=WEB_APP_URL),
        )
    else:
        btn = InlineKeyboardButton(
            text="Открыть в браузере",
            url=WEB_APP_URL,
        )
    return InlineKeyboardMarkup(inline_keyboard=[[btn]])


router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    keyboard = _start_reply_markup()
    await message.answer(
        "ConnectIT — найди своего наставника в IT.\n\n"
        "Нажми кнопку ниже, чтобы открыть приложение.",
        reply_markup=keyboard,
    )


def _display_name(first_name: str | None, username: str | None, fallback_id: int) -> str:
    if first_name:
        return first_name
    if username:
        return f"@{username}"
    return f"пользователь {fallback_id}"


def _chat_button(tg_user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Написать в чат",
                    url=f"tg://user?id={tg_user_id}",
                )
            ]
        ]
    )


async def send_match_notification(bot: Bot, match: Match) -> bool:
    """
    Отправляет уведомления о мэтче обоим участникам.
    Возвращает True, если хотя бы одно сообщение доставлено.
    """
    async with AsyncSessionFactory() as session:
        user_repo = UserRepository(session)
        user1 = await user_repo.get_by_id(match.user1_id)
        user2 = await user_repo.get_by_id(match.user2_id)

    if user1 is None or user2 is None:
        logging.error(
            "Уведомление о мэтче невозможно: match_id=%s user1=%s user2=%s",
            match.id,
            user1 is not None,
            user2 is not None,
        )
        return False

    deliveries = 0
    pairs = ((user1, user2), (user2, user1))
    for receiver, partner in pairs:
        partner_name = _display_name(partner.first_name, partner.username, partner.telegram_id)
        text = f"У вас мэтч с {partner_name}! Напишите ему/ей:"
        try:
            await bot.send_message(
                chat_id=receiver.telegram_id,
                text=text,
                reply_markup=_chat_button(partner.telegram_id),
            )
            deliveries += 1
            logging.info(
                "Отправлено уведомление о мэтче match_id=%s to_telegram_id=%s",
                match.id,
                receiver.telegram_id,
            )
        except Exception as exc:
            # Пользователь мог не запускать бота, отключить диалог или заблокировать его.
            logging.warning(
                "Не удалось отправить уведомление match_id=%s to_telegram_id=%s: %s",
                match.id,
                receiver.telegram_id,
                str(exc),
            )
    return deliveries > 0


async def check_new_matches(bot: Bot) -> None:
    """
    Фоновый цикл: проверяет несообщенные мэтчи и отправляет уведомления.
    """
    logging.info("Фоновая задача уведомлений о мэтчах запущена.")
    while True:
        try:
            async with AsyncSessionFactory() as session:
                match_repo = MatchRepository(session)
                matches = await match_repo.get_unsent_matches(limit=10)

            if matches:
                logging.info("Найдено мэтчей без уведомления: %s", len(matches))

            for match in matches:
                delivered = await send_match_notification(bot, match)
                if delivered:
                    async with AsyncSessionFactory() as session:
                        match_repo = MatchRepository(session)
                        await match_repo.mark_notification_sent(match.id, auto_commit=True)
                    logging.info("Мэтч помечен как notified: match_id=%s", match.id)
                else:
                    logging.warning(
                        "Мэтч оставлен в очереди уведомлений: match_id=%s",
                        match.id,
                    )
        except asyncio.CancelledError:
            logging.info("Фоновая задача уведомлений остановлена.")
            raise
        except Exception:
            logging.exception("Ошибка в check_new_matches")

        await asyncio.sleep(random.randint(5, 10))


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
    if WEB_APP_URL.lower().startswith("http://"):
        logging.info(
            "WEB_APP_URL без HTTPS: кнопка «Открыть в браузере» (Bot API не даёт Web App по http). "
            "Для встроенного Web App в Telegram задайте HTTPS (cloudflared/ngrok на порт со статикой)."
        )
    if TELEGRAM_PROXY_URL:
        logging.info("Прокси для Telegram API: %s", TELEGRAM_PROXY_URL)

    if TELEGRAM_PROXY_URL:
        session: AiohttpSession | TrustEnvAiohttpSession = AiohttpSession(
            proxy=TELEGRAM_PROXY_URL
        )
    else:
        session = TrustEnvAiohttpSession()
    bot = Bot(token=BOT_TOKEN, session=session)
    dp = Dispatcher()
    dp.include_router(router)
    notifier_task = asyncio.create_task(check_new_matches(bot))
    try:
        await dp.start_polling(bot)
    except TelegramNetworkError:
        logging.error(
            "Сеть к Telegram Bot API недоступна. "
            "Прокси MTProto из настроек Telegram сюда не подходит — "
            "нужен TELEGRAM_PROXY_URL=http://127.0.0.1:ПОРТ или socks5://127.0.0.1:ПОРТ "
            "(порт из Clash/v2rayN и т.п.) либо запуск бота на VPS вне блокировки."
        )
        raise
    finally:
        notifier_task.cancel()
        with suppress(asyncio.CancelledError):
            await notifier_task


if __name__ == "__main__":
    asyncio.run(main())
