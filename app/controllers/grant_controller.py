from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.rbac import CurrentUser, require_roles
from app.models import RoleName
from app.schemas.grant import GrantCreateRequest, GrantResponse, GrantUpdateRequest
from app.services.grant_service import GrantService

router = APIRouter(prefix="/api/grants", tags=["Grants"])
grant_service = GrantService()


@router.post("", response_model=GrantResponse, status_code=status.HTTP_201_CREATED)
def create_grant(
    payload: GrantCreateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(require_roles(RoleName.GRANTOR))],
):
    grant = grant_service.create_grant(
        db,
        current_user.user,
        payload.title,
        payload.description,
        payload.amount,
    )
    return grant


@router.get("", response_model=list[GrantResponse])
def list_grants(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[
        CurrentUser,
        Depends(require_roles(RoleName.GRANTEE, RoleName.GRANTOR, RoleName.ADMIN)),
    ],
):
    return grant_service.list_grants(db)


@router.get("/{grant_id}", response_model=GrantResponse)
def get_grant(
    grant_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[
        CurrentUser,
        Depends(require_roles(RoleName.GRANTEE, RoleName.GRANTOR, RoleName.ADMIN)),
    ],
):
    grant = grant_service.get_grant(db, grant_id)
    if not grant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grant not found")
    return grant


@router.put("/{grant_id}", response_model=GrantResponse)
def update_grant(
    grant_id: UUID,
    payload: GrantUpdateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(require_roles(RoleName.GRANTOR))],
):
    grant = grant_service.get_grant(db, grant_id)
    if not grant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grant not found")
    if grant.grantor_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not the grant owner")

    return grant_service.update_grant(
        db,
        grant,
        title=payload.title,
        description=payload.description,
        amount=payload.amount,
    )


@router.delete("/{grant_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_grant(
    grant_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[
        CurrentUser,
        Depends(require_roles(RoleName.GRANTOR, RoleName.ADMIN)),
    ],
):
    grant = grant_service.get_grant(db, grant_id)
    if not grant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grant not found")

    is_admin = current_user.has_role(RoleName.ADMIN)
    is_owner = grant.grantor_id == current_user.id
    if not is_admin and not is_owner:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this grant")

    grant_service.delete_grant(db, grant)
    return None
