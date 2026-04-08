from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.core.exceptions import DuplicateEntityError, InvalidOperationError
from app.core.upload import delete_photo, save_photo
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import ToggleActiveResponse, UserCreate, UserResponse, UserUpdate

router = APIRouter(prefix="/api/users", tags=["users"])


def _has_profile_data(user: User) -> bool:
    return bool(user.bio or user.age or user.role or user.direction or user.avatar_url)


def _to_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        telegram_id=user.telegram_id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        age=user.age,
        description=user.bio,
        role=user.role,
        direction=user.direction,
        photo_url=user.avatar_url,
        is_active=user.is_active,
        is_blocked=user.is_blocked,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_profile(
    first_name: str = Form(...),
    age: int = Form(...),
    description: str = Form(...),
    role: str = Form(...),
    direction: str = Form(...),
    photo: UploadFile | None = File(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    repo = UserRepository(db)
    user = await repo.get_by_id(current_user.id)
    if user is None:
        raise HTTPException(status_code=404, detail="Пользователь не найден.")

    if user.is_active and _has_profile_data(user):
        raise HTTPException(status_code=400, detail="У вас уже есть активная анкета.")

    try:
        payload = UserCreate(
            first_name=first_name,
            age=age,
            description=description,
            role=role,  # type: ignore[arg-type]
            direction=direction,
        )
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    photo_url = user.avatar_url
    if photo is not None:
        photo_url = await save_photo(user.id, photo)

    try:
        updated = await repo.update(
            user,
            first_name=payload.first_name,
            age=payload.age,
            bio=payload.description,
            role=payload.role,
            direction=payload.direction,
            avatar_url=photo_url,
            is_active=True,
        )
    except (InvalidOperationError, DuplicateEntityError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return _to_response(updated)


@router.get("/me", response_model=UserResponse)
async def get_my_profile(current_user: User = Depends(get_current_user)) -> UserResponse:
    if not _has_profile_data(current_user):
        raise HTTPException(status_code=404, detail="Анкета еще не создана.")
    return _to_response(current_user)


@router.put("/me", response_model=UserResponse)
async def update_my_profile(
    first_name: str | None = Form(default=None),
    age: int | None = Form(default=None),
    description: str | None = Form(default=None),
    role: str | None = Form(default=None),
    direction: str | None = Form(default=None),
    photo: UploadFile | None = File(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    repo = UserRepository(db)
    user = await repo.get_by_id(current_user.id)
    if user is None:
        raise HTTPException(status_code=404, detail="Пользователь не найден.")
    if not _has_profile_data(user):
        raise HTTPException(status_code=404, detail="Анкета еще не создана.")

    try:
        payload = UserUpdate(
            first_name=first_name,
            age=age,
            description=description,
            role=role,  # type: ignore[arg-type]
            direction=direction,
        )
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    updates = payload.model_dump(exclude_unset=True, exclude_none=True)
    if "description" in updates:
        updates["bio"] = updates.pop("description")

    if photo is not None:
        old_url = user.avatar_url
        new_url = await save_photo(user.id, photo)
        updates["avatar_url"] = new_url
        # Удаляем старый файл только после успешного сохранения нового.
        delete_photo(old_url)

    if not updates:
        return _to_response(user)

    try:
        updated = await repo.update(user, **updates)
    except (InvalidOperationError, DuplicateEntityError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _to_response(updated)


@router.patch("/me/toggle-active", response_model=ToggleActiveResponse)
async def toggle_profile_active(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ToggleActiveResponse:
    repo = UserRepository(db)
    user = await repo.get_by_id(current_user.id)
    if user is None:
        raise HTTPException(status_code=404, detail="Пользователь не найден.")
    if not _has_profile_data(user):
        raise HTTPException(status_code=404, detail="Анкета еще не создана.")

    updated = await repo.update(user, is_active=not user.is_active)
    message = "Анкета отображается в поиске." if updated.is_active else "Анкета скрыта из поиска."
    return ToggleActiveResponse(is_active=updated.is_active, message=message)
