from __future__ import annotations

import logging
import os
import time

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.auth import router as auth_router
from app.api.users import router as users_router
from app.api.exceptions_handlers import register_exception_handlers
from app.core.database import ensure_runtime_compatibility, ping_db
from app.core.upload import ensure_uploads_dir

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="ConnectIT Backend")

default_origins = "http://localhost:8080,http://127.0.0.1:8080,https://connectit.app"
cors_origins = [o.strip() for o in os.getenv("CORS_ORIGINS", default_origins).split(",")]

# Локальная разработка (любой порт) + туннели без ручного CORS_ORIGINS:
# - Cloudflare Quick Tunnel: https://xxxxx.trycloudflare.com
# - ngrok: https://xxxxx.ngrok-free.app
_cors_origin_regex = (
    r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$"
    r"|^https://[a-zA-Z0-9.-]+\.trycloudflare\.com$"
    r"|^https://[a-zA-Z0-9.-]+\.ngrok-free\.app$"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_origin_regex=_cors_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
register_exception_handlers(app)
app.include_router(auth_router)
app.include_router(users_router)
ensure_uploads_dir()
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start) * 1000
    logger.debug(
        "HTTP %s %s -> %s in %.2fms",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response


@app.on_event("startup")
async def startup_check_database() -> None:
    # Ранний fail-fast: если БД недоступна, это видно сразу при запуске сервера.
    await ensure_runtime_compatibility()
    await ping_db()


@app.get("/health/db")
async def health_db() -> JSONResponse:
    is_ok = await ping_db()
    if is_ok:
        return JSONResponse(status_code=200, content={"status": "ok"})
    return JSONResponse(status_code=503, content={"status": "db_unavailable"})
