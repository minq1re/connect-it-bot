from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlalchemy import BigInteger, DateTime, Enum as SQLEnum, ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ReportStatus(str, Enum):
    OPEN = "open"
    REVIEWING = "reviewing"
    RESOLVED = "resolved"
    REJECTED = "rejected"


class Report(Base):
    __tablename__ = "reports"
    __table_args__ = (
        Index("ix_reports_reported_status", "reported_user_id", "status"),
        Index("ix_reports_reporter_created", "reporter_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True, comment="ID жалобы"
    )
    reporter_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Пользователь, отправивший жалобу",
    )
    reported_user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Пользователь, на которого отправлена жалоба",
    )
    reason: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="Короткая причина жалобы"
    )
    details: Mapped[str | None] = mapped_column(
        Text, comment="Подробное описание жалобы"
    )
    status: Mapped[ReportStatus] = mapped_column(
        SQLEnum(
            ReportStatus,
            name="report_status",
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
        ),
        nullable=False,
        default=ReportStatus.OPEN,
        server_default=ReportStatus.OPEN.value,
        comment="Текущий статус обработки жалобы",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Дата и время создания жалобы",
    )

    reporter: Mapped["User"] = relationship(
        "User",
        foreign_keys=[reporter_id],
        back_populates="reports_sent",
    )
    reported_user: Mapped["User"] = relationship(
        "User",
        foreign_keys=[reported_user_id],
        back_populates="reports_received",
    )

    def __repr__(self) -> str:
        return (
            "Report("
            f"id={self.id}, reporter_id={self.reporter_id}, "
            f"reported_user_id={self.reported_user_id}, status={self.status})"
        )
