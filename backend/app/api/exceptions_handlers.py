from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class UnauthorizedException(Exception):
    def __init__(self, message: str = "Ошибка аутентификации Telegram initData.") -> None:
        self.message = message
        super().__init__(message)


class BlockedUserException(Exception):
    def __init__(self, message: str = "Пользователь заблокирован.") -> None:
        self.message = message
        super().__init__(message)


async def unauthorized_exception_handler(
    request: Request, exc: UnauthorizedException
) -> JSONResponse:
    return JSONResponse(status_code=401, content={"detail": exc.message})


async def blocked_user_exception_handler(
    request: Request, exc: BlockedUserException
) -> JSONResponse:
    return JSONResponse(status_code=403, content={"detail": exc.message})


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(UnauthorizedException, unauthorized_exception_handler)
    app.add_exception_handler(BlockedUserException, blocked_user_exception_handler)
