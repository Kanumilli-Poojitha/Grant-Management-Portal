import os
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("JWT_SECRET", "test-secret-key-for-jwt-signing-min-32-chars")
os.environ.setdefault("OAUTH_CLIENT_ID", "test-client-id")
os.environ.setdefault("OAUTH_CLIENT_SECRET", "test-client-secret")

import app.database as database_module
from app.config import get_settings
from app.database import Base, get_db
from app.main import app
from app.models import Role, RoleName, User
from app.services.auth_service import AuthService

get_settings.cache_clear()

app.router.on_startup.clear()


@pytest.fixture
def mock_redis():
    client = MagicMock()
    client.exists.return_value = 1
    client.setex.return_value = True
    client.delete.return_value = True
    with patch("app.services.auth_service.redis.from_url", return_value=client):
        yield client


@pytest.fixture
def db_engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    database_module.engine = engine
    database_module.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


def _seed_roles(session):
    for role_name in RoleName:
        if not session.query(Role).filter(Role.name == role_name.value).first():
            session.add(Role(name=role_name.value))
    session.commit()


@pytest.fixture
def db_session(db_engine, mock_redis):
    session = database_module.SessionLocal()
    _seed_roles(session)
    yield session
    session.close()


@pytest.fixture
def client(db_session, mock_redis):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def auth_service():
    return AuthService(get_settings())


def register_and_login(client, email, name="Test User", password="Password123"):
    client.post("/api/auth/register", json={"name": name, "email": email, "password": password})
    response = client.post("/api/auth/login", json={"email": email, "password": password})
    return response.json()["accessToken"]


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def get_role(db_session, role_name: RoleName) -> Role:
    return db_session.query(Role).filter(Role.name == role_name.value).first()


def assign_role(db_session, user: User, role_name: RoleName) -> User:
    role = get_role(db_session, role_name)
    if role not in user.roles:
        user.roles.append(role)
        db_session.commit()
        db_session.refresh(user)
    return user


def create_user_with_role(db_session, auth_service, email, role_name: RoleName, name="Role User"):
    user = User(
        name=name,
        email=email,
        password_hash=auth_service.hash_password("Password123"),
    )
    user.roles.append(get_role(db_session, role_name))
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user
