from typing import Annotated, Callable, Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import RoleName, User
from app.services.auth_service import AuthService
from app.services.user_service import UserService

security = HTTPBearer(auto_error=False)
auth_service = AuthService()
user_service = UserService()


class CurrentUser:
    def __init__(self, user: User, token: str, roles: list[str]):
        self.user = user
        self.token = token
        self.roles = roles

    @property
    def id(self) -> UUID:
        return self.user.id

    def has_role(self, role: RoleName | str) -> bool:
        role_value = role.value if isinstance(role, RoleName) else role
        return role_value in self.roles

    def has_any_role(self, roles: list[RoleName | str]) -> bool:
        return any(self.has_role(role) for role in roles)


def get_current_user(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)],
    db: Annotated[Session, Depends(get_db)],
) -> CurrentUser:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header",
        )

    try:
        payload = auth_service.decode_token(credentials.credentials)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    user_id = payload.get("userId")
    roles = payload.get("roles", [])
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    user = user_service.get_user_by_id(db, UUID(user_id))
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return CurrentUser(user=user, token=credentials.credentials, roles=roles)


def require_roles(*required_roles: RoleName) -> Callable:
    def dependency(current_user: Annotated[CurrentUser, Depends(get_current_user)]) -> CurrentUser:
        if not current_user.has_any_role(list(required_roles)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of roles: {[r.value for r in required_roles]}",
            )
        return current_user

    return dependency
