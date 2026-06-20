from datetime import datetime, timedelta, timezone
from typing import Optional

import httpx
import redis
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.models import Role, RoleName, User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"


class AuthService:
    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or get_settings()
        self._redis: Optional[redis.Redis] = None

    @property
    def redis_client(self) -> redis.Redis:
        if self._redis is None:
            self._redis = redis.from_url(self.settings.redis_url, decode_responses=True)
        return self._redis

    def hash_password(self, password: str) -> str:
        return pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    def create_access_token(self, user: User) -> str:
        now = datetime.now(timezone.utc)
        expire = now + timedelta(minutes=self.settings.jwt_expire_minutes)
        payload = {
            "userId": str(user.id),
            "roles": user.role_names(),
            "exp": int(expire.timestamp()),
            "iat": int(now.timestamp()),
        }
        token = jwt.encode(payload, self.settings.jwt_secret, algorithm=self.settings.jwt_algorithm)
        self.redis_client.setex(f"session:{token}", self.settings.jwt_expire_minutes * 60, str(user.id))
        return token

    def decode_token(self, token: str) -> dict:
        try:
            payload = jwt.decode(token, self.settings.jwt_secret, algorithms=[self.settings.jwt_algorithm])
            if not self.redis_client.exists(f"session:{token}"):
                raise JWTError("Session expired or revoked")
            return payload
        except JWTError as exc:
            raise ValueError("Invalid or expired token") from exc

    def revoke_token(self, token: str) -> None:
        self.redis_client.delete(f"session:{token}")

    def register_user(self, db: Session, name: str, email: str, password: str) -> User:
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            raise ValueError("Email already registered")

        grantee_role = db.query(Role).filter(Role.name == RoleName.GRANTEE.value).first()
        if not grantee_role:
            raise RuntimeError("GRANTEE role not found. Run database seed.")

        user = User(
            name=name,
            email=email,
            password_hash=self.hash_password(password),
        )
        user.roles.append(grantee_role)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    def authenticate_user(self, db: Session, email: str, password: str) -> User:
        user = db.query(User).filter(User.email == email).first()
        if not user or not user.password_hash:
            raise ValueError("Invalid email or password")
        if not self.verify_password(password, user.password_hash):
            raise ValueError("Invalid email or password")
        return user

    def get_google_auth_url(self) -> str:
        params = {
            "client_id": self.settings.oauth_client_id,
            "redirect_uri": self.settings.oauth_redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "access_type": "offline",
            "prompt": "consent",
        }
        query = "&".join(f"{key}={value}" for key, value in params.items())
        return f"{GOOGLE_AUTH_URL}?{query}"

    def handle_google_callback(self, db: Session, code: str) -> tuple[User, str]:
        token_data = self._exchange_google_code(code)
        profile = self._fetch_google_profile(token_data["access_token"])
        user = self._get_or_create_oauth_user(db, profile)
        access_token = self.create_access_token(user)
        return user, access_token

    def _exchange_google_code(self, code: str) -> dict:
        response = httpx.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": self.settings.oauth_client_id,
                "client_secret": self.settings.oauth_client_secret,
                "redirect_uri": self.settings.oauth_redirect_uri,
                "grant_type": "authorization_code",
            },
            timeout=10.0,
        )
        if response.status_code != 200:
            raise ValueError("Failed to exchange authorization code")
        return response.json()

    def _fetch_google_profile(self, access_token: str) -> dict:
        response = httpx.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10.0,
        )
        if response.status_code != 200:
            raise ValueError("Failed to fetch user profile")
        return response.json()

    def _get_or_create_oauth_user(self, db: Session, profile: dict) -> User:
        email = profile.get("email")
        if not email:
            raise ValueError("OAuth provider did not return an email")

        oauth_id = profile.get("id")
        name = profile.get("name") or email.split("@")[0]

        user = db.query(User).filter(User.email == email).first()
        if user:
            if not user.oauth_provider:
                user.oauth_provider = "google"
                user.oauth_id = oauth_id
                db.commit()
                db.refresh(user)
            return user

        grantee_role = db.query(Role).filter(Role.name == RoleName.GRANTEE.value).first()
        if not grantee_role:
            raise RuntimeError("GRANTEE role not found. Run database seed.")

        user = User(
            email=email,
            name=name,
            oauth_provider="google",
            oauth_id=oauth_id,
        )
        user.roles.append(grantee_role)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
