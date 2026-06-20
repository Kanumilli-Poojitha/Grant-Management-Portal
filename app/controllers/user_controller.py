from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.rbac import CurrentUser, require_roles
from app.models import RoleName
from app.schemas.auth import AssignRoleRequest, UserResponse
from app.services.user_service import UserService

router = APIRouter(prefix="/api/users", tags=["Users"])
user_service = UserService()


@router.get("", response_model=list[UserResponse])
def list_users(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[CurrentUser, Depends(require_roles(RoleName.ADMIN))],
):
    return user_service.list_users(db)


@router.post("/{user_id}/roles", response_model=UserResponse)
def assign_role(
    user_id: UUID,
    payload: AssignRoleRequest,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[CurrentUser, Depends(require_roles(RoleName.ADMIN))],
):
    try:
        user = user_service.assign_role(db, user_id, payload.role.upper())
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return user
