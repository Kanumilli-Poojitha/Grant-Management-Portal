from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models import ApplicationStatus


class ApplicationCreateRequest(BaseModel):
    proposal: str = Field(min_length=1)


class ApplicationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    grant_id: UUID
    grantee_id: UUID
    proposal: str
    status: ApplicationStatus
    created_at: datetime
    updated_at: datetime
