from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.core.exceptions import InvalidOperationError
from app.models.user import User
from app.repositories.report_repository import ReportRepository
from app.repositories.user_repository import UserRepository
from app.schemas.report import ReportCreate, ReportResponse

router = APIRouter(prefix="/api/reports", tags=["reports"])
logger = logging.getLogger(__name__)


@router.post("", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
async def create_report(
    payload: ReportCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ReportResponse:
    if payload.reported_user_id == current_user.id:
        raise HTTPException(
            status_code=400,
            detail="Нельзя пожаловаться на самого себя",
        )

    if not current_user.is_active:
        raise HTTPException(
            status_code=400,
            detail="У вас нет активной анкеты",
        )

    user_repo = UserRepository(db)
    target_user = await user_repo.get_by_id(payload.reported_user_id)
    if target_user is None:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    report_repo = ReportRepository(db)
    since = datetime.now(timezone.utc) - timedelta(hours=24)
    existing_recent = await report_repo.get_recent_between(
        reporter_id=current_user.id,
        reported_user_id=payload.reported_user_id,
        since=since,
    )
    if existing_recent is not None:
        raise HTTPException(
            status_code=409,
            detail="Вы уже подавали жалобу на этого пользователя",
        )

    try:
        report = await report_repo.create(
            reporter_id=current_user.id,
            reported_user_id=payload.reported_user_id,
            reason=payload.reason,
        )
    except InvalidOperationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    logger.info(
        "Создана жалоба id=%s reporter_id=%s reported_user_id=%s",
        report.id,
        report.reporter_id,
        report.reported_user_id,
    )

    return ReportResponse(
        id=report.id,
        reported_user_id=report.reported_user_id,
        reason=report.reason,
        status=report.status,
        created_at=report.created_at,
    )
