from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql://grantuser:grantpass@db:5432/grantdb"
    redis_url: str = "redis://cache:6379/0"

    jwt_secret: str = "change-me-to-a-long-random-secret-key"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    oauth_client_id: str = "your-google-client-id.apps.googleusercontent.com"
    oauth_client_secret: str = "your-google-client-secret"
    oauth_redirect_uri: str = "http://localhost:8000/api/auth/google/callback"

    app_host: str = "0.0.0.0"
    app_port: int = 8000

    default_admin_email: str = "admin@grantportal.com"
    default_admin_password: str = "Admin123!"
    default_admin_name: str = "System Admin"


@lru_cache
def get_settings() -> Settings:
    return Settings()
