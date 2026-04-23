from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import InvalidOperationError
from app.models.report import Report, ReportStatus
from app.repositories.base_repository import BaseRepository


class ReportRepository(BaseRepository):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def create(
        self,
        reporter_id: int,
        reported_user_id: int,
        reason: str,
    ) -> Report:
        if reporter_id == reported_user_id:
            raise InvalidOperationError("Нельзя отправить жалобу на самого себя.")
        report = Report(
            reporter_id=reporter_id,
            reported_user_id=reported_user_id,
            reason=reason,
            status=ReportStatus.NEW,
        )
        self.session.add(report)
        await self._commit()
        await self.session.refresh(report)
        return report

    async def get_by_id(self, report_id: int) -> Report | None:
        return await self.session.get(Report, report_id)

    async def list_for_user(
        self,
        user_id: int,
        status: ReportStatus | None = None,
    ) -> list[Report]:
        stmt = (
            select(Report)
            .where(Report.reporter_id == user_id)
            .order_by(Report.created_at.desc())
        )
        if status is not None:
            stmt = stmt.where(Report.status == status)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_status(
        self,
        report_id: int,
        status: ReportStatus,
        resolution_note: str | None = None,
    ) -> Report:
        report = await self.get_by_id(report_id)
        if report is None:
            raise InvalidOperationError("Жалоба не найдена.")

        if report.status == status:
            return report

        report.status = status
        report.resolution_note = resolution_note
        if status in (ReportStatus.RESOLVED, ReportStatus.REJECTED):
            report.resolved_at = datetime.now(timezone.utc)
        else:
            report.resolved_at = None
        await self._commit()
        await self.session.refresh(report)
        return report

    async def list_all(
        self,
        limit: int = 50,
        offset: int = 0,
        status: ReportStatus | None = None,
    ) -> list[Report]:
        stmt = select(Report)
        if status is not None:
            stmt = stmt.where(Report.status == status)
        stmt = stmt.order_by(Report.created_at.desc()).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_pending_reports(self) -> list[Report]:
        stmt = (
            select(Report)
            .where(Report.status == ReportStatus.NEW)
            .order_by(Report.created_at.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_reported_user(self, reported_user_id: int) -> list[Report]:
        stmt = (
            select(Report)
            .where(Report.reported_user_id == reported_user_id)
            .order_by(Report.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_recent_between(
        self,
        reporter_id: int,
        reported_user_id: int,
        since: datetime,
    ) -> Report | None:
        stmt = (
            select(Report)
            .where(
                Report.reporter_id == reporter_id,
                Report.reported_user_id == reported_user_id,
                Report.created_at >= since,
            )
            .order_by(Report.created_at.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
