from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True, comment="Внутренний ID пользователя"
    )
    telegram_id: Mapped[int] = mapped_column(
        BigInteger,
        unique=True,
        index=True,
        nullable=False,
        comment="Уникальный Telegram ID",
    )
    username: Mapped[str | None] = mapped_column(
        String(64), index=True, comment="Username из Telegram"
    )
    first_name: Mapped[str | None] = mapped_column(
        String(128), comment="Имя пользователя"
    )
    last_name: Mapped[str | None] = mapped_column(
        String(128), comment="Фамилия пользователя"
    )
    age: Mapped[int | None] = mapped_column(
        Integer, index=True, comment="Возраст для фильтрации анкет"
    )
    city: Mapped[str | None] = mapped_column(
        String(128), index=True, comment="Город пользователя"
    )
    role: Mapped[str | None] = mapped_column(
        String(16), index=True, comment="Роль пользователя: mentor или mentee"
    )
    direction: Mapped[str | None] = mapped_column(
        String(128), index=True, comment="Направление наставничества"
    )
    bio: Mapped[str | None] = mapped_column(Text, comment="Краткое описание анкеты")
    skills: Mapped[str | None] = mapped_column(
        Text, comment="Навыки/интересы в свободной форме"
    )
    about_me: Mapped[str | None] = mapped_column(
        Text, comment="Расширенная информация о пользователе"
    )
    avatar_url: Mapped[str | None] = mapped_column(
        String(512), comment="Ссылка на аватар в CDN/Telegram"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, index=True, comment="Активна ли анкета"
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Прошел ли пользователь модерацию/верификацию",
    )
    is_blocked: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        comment="Заблокирован ли пользователь для доступа к приложению",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Дата и время создания",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Дата и время последнего обновления",
    )

    likes_sent: Mapped[list["Like"]] = relationship(
        "Like",
        foreign_keys="Like.from_user_id",
        back_populates="from_user",
        cascade="all, delete-orphan",
    )
    likes_received: Mapped[list["Like"]] = relationship(
        "Like",
        foreign_keys="Like.to_user_id",
        back_populates="to_user",
        cascade="all, delete-orphan",
    )
    dislikes_sent: Mapped[list["Dislike"]] = relationship(
        "Dislike",
        foreign_keys="Dislike.from_user_id",
        back_populates="from_user",
        cascade="all, delete-orphan",
    )
    dislikes_received: Mapped[list["Dislike"]] = relationship(
        "Dislike",
        foreign_keys="Dislike.to_user_id",
        back_populates="to_user",
        cascade="all, delete-orphan",
    )
    matches_as_user1: Mapped[list["Match"]] = relationship(
        "Match",
        foreign_keys="Match.user1_id",
        back_populates="user1",
        cascade="all, delete-orphan",
    )
    matches_as_user2: Mapped[list["Match"]] = relationship(
        "Match",
        foreign_keys="Match.user2_id",
        back_populates="user2",
        cascade="all, delete-orphan",
    )
    reports_sent: Mapped[list["Report"]] = relationship(
        "Report",
        foreign_keys="Report.reporter_id",
        back_populates="reporter",
        cascade="all, delete-orphan",
    )
    reports_received: Mapped[list["Report"]] = relationship(
        "Report",
        foreign_keys="Report.reported_user_id",
        back_populates="reported_user",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            "User("
            f"id={self.id}, telegram_id={self.telegram_id}, username={self.username!r}, "
            f"is_active={self.is_active}, is_blocked={self.is_blocked})"
        )
