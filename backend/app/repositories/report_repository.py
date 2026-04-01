from __future__ import annotations

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
        details: str | None = None,
    ) -> Report:
        if reporter_id == reported_user_id:
            raise InvalidOperationError("Нельзя отправить жалобу на самого себя.")
        report = Report(
            reporter_id=reporter_id,
            reported_user_id=reported_user_id,
            reason=reason,
            details=details,
            status=ReportStatus.OPEN,
        )
        self.session.add(report)
        await self._commit()
        await self.session.refresh(report)
        return report

    async def get_by_id(self, report_id: int) -> Report | None:
        return await self.session.get(Report, report_id)

    async def list_for_user(self, reported_user_id: int) -> list[Report]:
        stmt = (
            select(Report)
            .where(Report.reported_user_id == reported_user_id)
            .order_by(Report.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_status(self, report: Report, status: ReportStatus) -> Report:
        report.status = status
        await self._commit()
        await self.session.refresh(report)
        return report
