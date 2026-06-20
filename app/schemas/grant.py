from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class GrantCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1)
    amount: float = Field(gt=0)


class GrantUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, min_length=1)
    amount: float | None = Field(default=None, gt=0)


class GrantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    description: str
    amount: float
    grantor_id: UUID
    created_at: datetime
    updated_at: datetime
