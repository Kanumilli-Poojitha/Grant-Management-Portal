from uuid import UUID

from sqlalchemy.orm import Session

from app.models import Application, ApplicationStatus, Grant, User


class GrantService:
    def create_grant(
        self,
        db: Session,
        grantor: User,
        title: str,
        description: str,
        amount: float,
    ) -> Grant:
        grant = Grant(
            title=title,
            description=description,
            amount=amount,
            grantor_id=grantor.id,
        )
        db.add(grant)
        db.commit()
        db.refresh(grant)
        return grant

    def list_grants(self, db: Session) -> list[Grant]:
        return db.query(Grant).order_by(Grant.created_at.desc()).all()

    def get_grant(self, db: Session, grant_id: UUID) -> Grant | None:
        return db.query(Grant).filter(Grant.id == grant_id).first()

    def update_grant(
        self,
        db: Session,
        grant: Grant,
        title: str | None = None,
        description: str | None = None,
        amount: float | None = None,
    ) -> Grant:
        if title is not None:
            grant.title = title
        if description is not None:
            grant.description = description
        if amount is not None:
            grant.amount = amount
        db.commit()
        db.refresh(grant)
        return grant

    def delete_grant(self, db: Session, grant: Grant) -> None:
        db.delete(grant)
        db.commit()


class ApplicationService:
    def submit_application(
        self,
        db: Session,
        grant: Grant,
        grantee: User,
        proposal: str,
    ) -> Application:
        existing = (
            db.query(Application)
            .filter(Application.grant_id == grant.id, Application.grantee_id == grantee.id)
            .first()
        )
        if existing:
            raise ValueError("You have already applied to this grant")

        application = Application(
            grant_id=grant.id,
            grantee_id=grantee.id,
            proposal=proposal,
            status=ApplicationStatus.SUBMITTED,
        )
        db.add(application)
        db.commit()
        db.refresh(application)
        return application

    def list_applications_for_grant(self, db: Session, grant: Grant) -> list[Application]:
        return (
            db.query(Application)
            .filter(Application.grant_id == grant.id)
            .order_by(Application.created_at.desc())
            .all()
        )

    def get_application(self, db: Session, application_id: UUID) -> Application | None:
        return db.query(Application).filter(Application.id == application_id).first()
