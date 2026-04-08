from __future__ import annotations

import io
import uuid
from pathlib import Path

from fastapi import UploadFile
from PIL import Image, UnidentifiedImageError

from app.core.exceptions import InvalidOperationError

MAX_PHOTO_SIZE_BYTES = 5 * 1024 * 1024
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png"}
UPLOADS_DIR = Path(__file__).resolve().parents[2] / "static" / "uploads"


def ensure_uploads_dir() -> None:
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)


async def validate_photo(file: UploadFile) -> bytes:
    if not file.content_type or file.content_type.lower() not in ALLOWED_CONTENT_TYPES:
        raise InvalidOperationError("Поддерживаются только изображения JPEG/PNG.")

    content = await file.read()
    await file.seek(0)

    if not content:
        raise InvalidOperationError("Файл изображения пустой.")
    if len(content) > MAX_PHOTO_SIZE_BYTES:
        raise InvalidOperationError("Размер изображения не должен превышать 5MB.")

    try:
        Image.open(io.BytesIO(content)).verify()
    except (UnidentifiedImageError, OSError) as exc:
        raise InvalidOperationError("Файл не является валидным изображением.") from exc

    return content


async def save_photo(user_id: int, file: UploadFile) -> str:
    ensure_uploads_dir()
    raw_content = await validate_photo(file)

    extension = ".jpg" if file.content_type == "image/jpeg" else ".png"
    filename = f"{user_id}_{uuid.uuid4().hex}{extension}"
    output_path = UPLOADS_DIR / filename

    # Нормализуем изображение и ограничиваем максимальный размер 800x800.
    with Image.open(io.BytesIO(raw_content)) as img:
        rgb_image = img.convert("RGB")
        rgb_image.thumbnail((800, 800))
        rgb_image.save(output_path, format="JPEG", quality=85, optimize=True)

    return f"/static/uploads/{filename}"


def delete_photo(photo_url: str | None) -> None:
    if not photo_url:
        return
    filename = Path(photo_url).name
    target = UPLOADS_DIR / filename
    if target.exists():
        target.unlink()
