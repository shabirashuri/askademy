import uuid
from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import DbSession, require_roles
from app.core.errors import Forbidden
from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserRead, UserUpdate
from app.services import user_service

router = APIRouter(prefix="/users", tags=["users"])

AdminUser = Annotated[User, Depends(require_roles(UserRole.ADMIN))]
StaffUser = Annotated[User, Depends(require_roles(UserRole.ADMIN, UserRole.TEACHER))]


@router.post(
    "",
    response_model=UserRead,
    status_code=201,
    summary="Create a user (admins: any role; teachers: students only)",
)
def create_user(payload: UserCreate, db: DbSession, current: StaffUser) -> User:
    if current.role == UserRole.TEACHER and payload.role != UserRole.STUDENT:
        raise Forbidden("Teachers can only add student accounts.")
    return user_service.create_user(db, payload)


@router.get("", response_model=list[UserRead], summary="List users")
def list_users(db: DbSession, current: StaffUser, role: UserRole | None = None) -> list[User]:
    if current.role == UserRole.TEACHER:
        role = UserRole.STUDENT
    return user_service.list_users(db, role)


@router.patch("/{user_id}", response_model=UserRead, summary="Update a user (admin)")
def update_user(user_id: uuid.UUID, payload: UserUpdate, db: DbSession, admin: AdminUser) -> User:
    return user_service.update_user(db, user_id, payload, admin)
