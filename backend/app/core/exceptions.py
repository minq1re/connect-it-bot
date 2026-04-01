from __future__ import annotations


class RepositoryError(Exception):
    """Базовая ошибка слоя репозиториев."""


class DuplicateEntityError(RepositoryError):
    """Ошибка создания дубликата (нарушение unique-ограничений)."""


class InvalidOperationError(RepositoryError):
    """Некорректная операция с точки зрения бизнес-правил."""
