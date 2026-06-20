from uuid import UUID

from sqlalchemy.orm import Session

from app.models import Grant, Role, RoleName, User


class UserService:
    def get_user_by_id(self, db: Session, user_id: UUID) -> User | None:
        return db.query(User).filter(User.id == user_id).first()

    def assign_role(self, db: Session, user_id: UUID, role_name: str) -> User:
        if role_name not in {r.value for r in RoleName}:
            raise ValueError(f"Invalid role: {role_name}")

        user = self.get_user_by_id(db, user_id)
        if not user:
            raise LookupError("User not found")

        role = db.query(Role).filter(Role.name == role_name).first()
        if not role:
            raise RuntimeError(f"Role {role_name} not found in database")

        if role not in user.roles:
            user.roles.append(role)
            db.commit()
            db.refresh(user)

        return user

    def list_users(self, db: Session) -> list[User]:
        return db.query(User).all()
