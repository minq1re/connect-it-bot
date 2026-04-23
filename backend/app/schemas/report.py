from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.models.report import ReportStatus


class ReportCreate(BaseModel):
    reported_user_id: int = Field(gt=0)
    reason: str = Field(min_length=10, max_length=1000)

    @field_validator("reason")
    @classmethod
    def validate_reason_not_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Текст жалобы не должен быть пустым.")
        if len(stripped) < 10:
            raise ValueError("Текст жалобы должен содержать минимум 10 символов.")
        return stripped


class ReportResponse(BaseModel):
    id: int
    reported_user_id: int
    reason: str
    status: ReportStatus
    created_at: datetime


class ReportStatusUpdate(BaseModel):
    status: ReportStatus
    resolution_note: str | None = Field(default=None, max_length=2000)

    @field_validator("resolution_note")
    @classmethod
    def normalize_resolution_note(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None


class AdminReportResponse(BaseModel):
    id: int
    reporter_id: int
    reported_user_id: int
    reason: str
    status: ReportStatus
    created_at: datetime
    resolved_at: datetime | None = None
    resolution_note: str | None = None
