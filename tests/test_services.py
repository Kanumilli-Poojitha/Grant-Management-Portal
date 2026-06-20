from app.services.auth_service import AuthService
from app.services.grant_service import ApplicationService, GrantService
from app.services.user_service import UserService
from app.models import RoleName, User
from tests.conftest import create_user_with_role, get_role


class TestAuthServiceUnit:
    def test_hash_and_verify_password(self, auth_service):
        hashed = auth_service.hash_password("MyPassword1")
        assert auth_service.verify_password("MyPassword1", hashed)
        assert not auth_service.verify_password("WrongPassword", hashed)

    def test_create_and_decode_token(self, auth_service, db_session, mock_redis):
        user = create_user_with_role(db_session, auth_service, "unit@example.com", RoleName.GRANTEE)
        token = auth_service.create_access_token(user)
        payload = auth_service.decode_token(token)
        assert payload["userId"] == str(user.id)
        assert "GRANTEE" in payload["roles"]

    def test_get_google_auth_url(self, auth_service):
        url = auth_service.get_google_auth_url()
        assert "client_id=" in url
        assert "redirect_uri=" in url


class TestUserServiceUnit:
    def test_assign_invalid_role(self, db_session):
        service = UserService()
        user = User(name="Test", email="invalid-role@example.com", password_hash="x")
        db_session.add(user)
        db_session.commit()
        try:
            service.assign_role(db_session, user.id, "INVALID")
            assert False, "Expected ValueError"
        except ValueError as exc:
            assert "Invalid role" in str(exc)

    def test_assign_role_to_missing_user(self, db_session):
        service = UserService()
        import uuid

        try:
            service.assign_role(db_session, uuid.uuid4(), RoleName.ADMIN.value)
            assert False, "Expected LookupError"
        except LookupError:
            pass


class TestGrantServiceUnit:
    def test_create_and_list_grants(self, db_session, auth_service):
        grant_service = GrantService()
        grantor = create_user_with_role(db_session, auth_service, "gs@example.com", RoleName.GRANTOR)
        grant = grant_service.create_grant(db_session, grantor, "Title", "Description", 5000)
        grants = grant_service.list_grants(db_session)
        assert any(g.id == grant.id for g in grants)


class TestApplicationServiceUnit:
    def test_submit_application(self, db_session, auth_service):
        grant_service = GrantService()
        app_service = ApplicationService()
        grantor = create_user_with_role(db_session, auth_service, "as-grantor@example.com", RoleName.GRANTOR)
        grantee = create_user_with_role(db_session, auth_service, "as-grantee@example.com", RoleName.GRANTEE)
        grant = grant_service.create_grant(db_session, grantor, "Grant", "Desc", 1000)
        application = app_service.submit_application(db_session, grant, grantee, "Proposal text")
        assert application.grantee_id == grantee.id
