from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegisterRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    accessToken: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    email: str


class AssignRoleRequest(BaseModel):
    role: str = Field(description="Role name: ADMIN, GRANTOR, or GRANTEE")


class OAuthCallbackResponse(BaseModel):
    accessToken: str
    user: UserResponse


class TokenPayload(BaseModel):
    userId: str
    roles: list[str]
    iat: Optional[int] = None
    exp: Optional[int] = None
