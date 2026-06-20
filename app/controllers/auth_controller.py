from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.rbac import CurrentUser, get_current_user, require_roles
from app.models import RoleName
from app.schemas.auth import (
    AssignRoleRequest,
    LoginRequest,
    OAuthCallbackResponse,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.services.auth_service import AuthService
from app.services.user_service import UserService

router = APIRouter(prefix="/api/auth", tags=["Authentication"])
auth_service = AuthService()
user_service = UserService()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Annotated[Session, Depends(get_db)]):
    try:
        user = auth_service.register_user(db, payload.name, payload.email, payload.password)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return user


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Annotated[Session, Depends(get_db)]):
    try:
        user = auth_service.authenticate_user(db, payload.email, payload.password)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    token = auth_service.create_access_token(user)
    return TokenResponse(accessToken=token)


@router.get("/google")
def google_login():
    return RedirectResponse(url=auth_service.get_google_auth_url())


@router.get("/google/callback", response_model=OAuthCallbackResponse)
def google_callback(code: str, db: Annotated[Session, Depends(get_db)]):
    try:
        user, token = auth_service.handle_google_callback(db, code)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return OAuthCallbackResponse(accessToken=token, user=UserResponse.model_validate(user))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(current_user: Annotated[CurrentUser, Depends(get_current_user)]):
    auth_service.revoke_token(current_user.token)
    return None
