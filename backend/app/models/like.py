from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Like(Base):
    __tablename__ = "likes"
    __table_args__ = (
        UniqueConstraint("from_user_id", "to_user_id", name="uq_like_pair"),
        Index("ix_likes_from_created", "from_user_id", "created_at"),
        Index("ix_likes_to_created", "to_user_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True, comment="ID реакции like"
    )
    from_user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Кто поставил лайк",
    )
    to_user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Кому поставили лайк",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Дата и время создания лайка",
    )

    from_user: Mapped["User"] = relationship(
        "User",
        foreign_keys=[from_user_id],
        back_populates="likes_sent",
    )
    to_user: Mapped["User"] = relationship(
        "User",
        foreign_keys=[to_user_id],
        back_populates="likes_received",
    )

    def __repr__(self) -> str:
        return (
            "Like("
            f"id={self.id}, from_user_id={self.from_user_id}, to_user_id={self.to_user_id})"
        )
