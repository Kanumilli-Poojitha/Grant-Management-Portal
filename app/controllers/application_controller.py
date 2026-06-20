from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.rbac import CurrentUser, require_roles
from app.models import RoleName
from app.schemas.application import ApplicationCreateRequest, ApplicationResponse
from app.services.grant_service import ApplicationService, GrantService

router = APIRouter(tags=["Applications"])
grant_service = GrantService()
application_service = ApplicationService()


@router.post(
    "/api/grants/{grant_id}/apply",
    response_model=ApplicationResponse,
    status_code=status.HTTP_201_CREATED,
)
def apply_to_grant(
    grant_id: UUID,
    payload: ApplicationCreateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(require_roles(RoleName.GRANTEE))],
):
    grant = grant_service.get_grant(db, grant_id)
    if not grant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grant not found")

    try:
        application = application_service.submit_application(
            db, grant, current_user.user, payload.proposal
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return application


@router.get("/api/grants/{grant_id}/applications", response_model=list[ApplicationResponse])
def list_grant_applications(
    grant_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(require_roles(RoleName.GRANTOR))],
):
    grant = grant_service.get_grant(db, grant_id)
    if not grant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grant not found")
    if grant.grantor_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not the grant owner")

    return application_service.list_applications_for_grant(db, grant)


@router.get("/api/applications/{application_id}", response_model=ApplicationResponse)
def get_application(
    application_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[
        CurrentUser,
        Depends(require_roles(RoleName.GRANTEE, RoleName.GRANTOR)),
    ],
):
    application = application_service.get_application(db, application_id)
    if not application:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")

    is_grantee = application.grantee_id == current_user.id
    is_grantor = application.grant.grantor_id == current_user.id
    if not is_grantee and not is_grantor:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    return application
