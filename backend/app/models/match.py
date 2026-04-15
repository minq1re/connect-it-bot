from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Match(Base):
    __tablename__ = "matches"
    __table_args__ = (
        UniqueConstraint("user1_id", "user2_id", name="uq_match_pair"),
        CheckConstraint("user1_id < user2_id", name="ck_match_order"),
        Index("ix_matches_user1_created", "user1_id", "created_at"),
        Index("ix_matches_user2_created", "user2_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True, comment="ID мэтча"
    )
    user1_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Первый участник мэтча (ID меньше user2_id)",
    )
    user2_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Второй участник мэтча (ID больше user1_id)",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, comment="Активен ли мэтч"
    )
    notification_sent: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Отправлено ли уведомление о мэтче участникам",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Дата и время создания мэтча",
    )

    user1: Mapped["User"] = relationship(
        "User",
        foreign_keys=[user1_id],
        back_populates="matches_as_user1",
    )
    user2: Mapped["User"] = relationship(
        "User",
        foreign_keys=[user2_id],
        back_populates="matches_as_user2",
    )

    def __repr__(self) -> str:
        return (
            "Match("
            f"id={self.id}, user1_id={self.user1_id}, user2_id={self.user2_id}, "
            f"is_active={self.is_active}, notification_sent={self.notification_sent})"
        )
