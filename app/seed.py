import logging

from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import SessionLocal
from app.models import Role, RoleName, User
from app.services.auth_service import AuthService

logger = logging.getLogger(__name__)


def seed_database() -> None:
    settings = get_settings()
    auth_service = AuthService(settings)
    db: Session = SessionLocal()

    try:
        for role_name in RoleName:
            existing_role = db.query(Role).filter(Role.name == role_name.value).first()
            if not existing_role:
                db.add(Role(name=role_name.value))
                logger.info("Created role: %s", role_name.value)

        db.commit()

        admin_role = db.query(Role).filter(Role.name == RoleName.ADMIN.value).first()
        admin_user = db.query(User).filter(User.email == settings.default_admin_email).first()

        if not admin_user:
            admin_user = User(
                name=settings.default_admin_name,
                email=settings.default_admin_email,
                password_hash=auth_service.hash_password(settings.default_admin_password),
            )
            admin_user.roles.append(admin_role)
            db.add(admin_user)
            logger.info("Created default admin user: %s", settings.default_admin_email)
        elif admin_role not in admin_user.roles:
            admin_user.roles.append(admin_role)

        db.commit()
    finally:
        db.close()
