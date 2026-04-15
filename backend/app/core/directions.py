from __future__ import annotations

# Единый список направлений для backend-валидации и фильтров.
DIRECTIONS: tuple[str, ...] = (
    "Python разработка",
    "Java разработка",
    "Frontend",
    "Backend",
    "UX/UI дизайн",
    "Data Science",
    "DevOps",
    "QA тестирование",
    "Маркетинг",
    "Управление проектами",
    "Английский язык",
)


def is_supported_direction(value: str) -> bool:
    return value in DIRECTIONS
