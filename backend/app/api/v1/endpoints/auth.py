from fastapi import APIRouter, Request

from app.api.deps import CurrentUser, DbSession
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.user import UserRead
from app.services import auth_service

router = APIRouter(prefix="/auth")


@router.post("/login", response_model=TokenResponse, summary="Log in with email and password")
def login(payload: LoginRequest, request: Request, db: DbSession) -> TokenResponse:
    client_ip = request.client.host if request.client else ""
    user = auth_service.authenticate(db, payload.email, payload.password, client_ip)
    return TokenResponse(
        access_token=auth_service.issue_token(user), user=UserRead.model_validate(user)
    )


@router.get("/me", response_model=UserRead, summary="Get the authenticated user")
def me(user: CurrentUser) -> UserRead:
    return UserRead.model_validate(user)
