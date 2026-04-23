from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_admin_user
from app.core.database import get_db
from app.core.exceptions import InvalidOperationError
from app.models.report import ReportStatus
from app.models.user import User
from app.repositories.report_repository import ReportRepository
from app.repositories.user_repository import UserRepository
from app.schemas.report import AdminReportResponse, ReportStatusUpdate

router = APIRouter(prefix="/api/admin", tags=["admin"])
logger = logging.getLogger(__name__)


class UserBlockResponse(BaseModel):
    user_id: int
    is_blocked: bool
    message: str


@router.get("/reports", response_model=list[AdminReportResponse])
async def list_reports(
    status_filter: ReportStatus | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    _: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> list[AdminReportResponse]:
    repo = ReportRepository(db)
    reports = await repo.list_all(limit=limit, offset=offset, status=status_filter)
    return [
        AdminReportResponse(
            id=report.id,
            reporter_id=report.reporter_id,
            reported_user_id=report.reported_user_id,
            reason=report.reason,
            status=report.status,
            created_at=report.created_at,
            resolved_at=report.resolved_at,
            resolution_note=report.resolution_note,
        )
        for report in reports
    ]


@router.patch("/reports/{report_id}/status", response_model=AdminReportResponse)
async def update_report_status(
    report_id: int,
    payload: ReportStatusUpdate,
    _: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> AdminReportResponse:
    repo = ReportRepository(db)
    report = await repo.get_by_id(report_id)
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Жалоба не найдена.")
    try:
        updated = await repo.update_status(
            report_id=report_id,
            status=payload.status,
            resolution_note=payload.resolution_note,
        )
    except InvalidOperationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    logger.info(
        "Админ обновил статус жалобы id=%s status=%s",
        updated.id,
        updated.status.value,
    )

    return AdminReportResponse(
        id=updated.id,
        reporter_id=updated.reporter_id,
        reported_user_id=updated.reported_user_id,
        reason=updated.reason,
        status=updated.status,
        created_at=updated.created_at,
        resolved_at=updated.resolved_at,
        resolution_note=updated.resolution_note,
    )


@router.patch("/users/{user_id}/block", response_model=UserBlockResponse)
async def block_user(
    user_id: int,
    _: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> UserBlockResponse:
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден.",
        )

    if user.is_blocked:
        return UserBlockResponse(
            user_id=user.id,
            is_blocked=True,
            message="Пользователь уже заблокирован.",
        )

    updated = await user_repo.update(user, is_blocked=True, is_active=False)
    logger.info("Админ заблокировал пользователя id=%s telegram_id=%s", updated.id, updated.telegram_id)
    return UserBlockResponse(
        user_id=updated.id,
        is_blocked=updated.is_blocked,
        message="Пользователь заблокирован.",
    )
