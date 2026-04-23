from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlalchemy import BigInteger, DateTime, Enum as SQLEnum, ForeignKey, Index, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ReportStatus(str, Enum):
    NEW = "new"
    IN_PROGRESS = "in_progress"
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
        Text,
        nullable=False,
        comment="Текст жалобы",
    )
    status: Mapped[ReportStatus] = mapped_column(
        SQLEnum(
            ReportStatus,
            name="report_status",
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
            native_enum=False,
        ),
        nullable=False,
        default=ReportStatus.NEW,
        server_default=ReportStatus.NEW.value,
        comment="Текущий статус обработки жалобы",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Дата и время создания жалобы",
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Дата и время закрытия жалобы",
    )
    resolution_note: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Комментарий модератора о решении",
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
            f"reported_user_id={self.reported_user_id}, status={self.status.value})"
        )
