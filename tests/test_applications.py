from tests.conftest import auth_header, create_user_with_role
from app.models import RoleName


def login_as(client, email):
    response = client.post("/api/auth/login", json={"email": email, "password": "Password123"})
    return response.json()["accessToken"]


class TestApplications:
    def _create_grant(self, client, db_session, auth_service):
        grantor = create_user_with_role(db_session, auth_service, "app-grantor@example.com", RoleName.GRANTOR)
        token = login_as(client, grantor.email)
        response = client.post(
            "/api/grants",
            json={"title": "Education Grant", "description": "For schools", "amount": 25000},
            headers=auth_header(token),
        )
        return response.json()["id"], grantor

    def test_grantee_can_apply(self, client, db_session, auth_service):
        grant_id, _ = self._create_grant(client, db_session, auth_service)
        grantee = create_user_with_role(db_session, auth_service, "applicant@example.com", RoleName.GRANTEE)
        token = login_as(client, grantee.email)

        response = client.post(
            f"/api/grants/{grant_id}/apply",
            json={"proposal": "Our school needs funding for STEM labs."},
            headers=auth_header(token),
        )
        assert response.status_code == 201
        data = response.json()
        assert data["proposal"].startswith("Our school")
        assert data["status"] == "submitted"

    def test_grantor_can_view_applications(self, client, db_session, auth_service):
        grant_id, grantor = self._create_grant(client, db_session, auth_service)
        grantee = create_user_with_role(db_session, auth_service, "app-grantee@example.com", RoleName.GRANTEE)
        grantee_token = login_as(client, grantee.email)
        grantor_token = login_as(client, grantor.email)

        client.post(
            f"/api/grants/{grant_id}/apply",
            json={"proposal": "Detailed proposal text."},
            headers=auth_header(grantee_token),
        )

        response = client.get(
            f"/api/grants/{grant_id}/applications",
            headers=auth_header(grantor_token),
        )
        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_other_grantor_cannot_view_applications(self, client, db_session, auth_service):
        grant_id, _ = self._create_grant(client, db_session, auth_service)
        other_grantor = create_user_with_role(
            db_session, auth_service, "other-grantor@example.com", RoleName.GRANTOR
        )
        other_token = login_as(client, other_grantor.email)

        response = client.get(
            f"/api/grants/{grant_id}/applications",
            headers=auth_header(other_token),
        )
        assert response.status_code == 403

    def test_grantee_can_view_own_application(self, client, db_session, auth_service):
        grant_id, _ = self._create_grant(client, db_session, auth_service)
        grantee = create_user_with_role(db_session, auth_service, "view-app@example.com", RoleName.GRANTEE)
        token = login_as(client, grantee.email)

        apply_response = client.post(
            f"/api/grants/{grant_id}/apply",
            json={"proposal": "My proposal."},
            headers=auth_header(token),
        )
        app_id = apply_response.json()["id"]

        response = client.get(f"/api/applications/{app_id}", headers=auth_header(token))
        assert response.status_code == 200

    def test_duplicate_application_rejected(self, client, db_session, auth_service):
        grant_id, _ = self._create_grant(client, db_session, auth_service)
        grantee = create_user_with_role(db_session, auth_service, "dup-app@example.com", RoleName.GRANTEE)
        token = login_as(client, grantee.email)

        payload = {"proposal": "First application."}
        client.post(f"/api/grants/{grant_id}/apply", json=payload, headers=auth_header(token))
        response = client.post(f"/api/grants/{grant_id}/apply", json=payload, headers=auth_header(token))
        assert response.status_code == 400
