from tests.conftest import auth_header, create_user_with_role, register_and_login
from app.models import RoleName


def login_as(client, email):
    response = client.post("/api/auth/login", json={"email": email, "password": "Password123"})
    return response.json()["accessToken"]


class TestGrantManagement:
    def test_grantor_can_create_grant(self, client, db_session, auth_service):
        grantor = create_user_with_role(db_session, auth_service, "grantor@example.com", RoleName.GRANTOR)
        token = login_as(client, grantor.email)

        response = client.post(
            "/api/grants",
            json={
                "title": "Community Health Fund",
                "description": "Funding for local health initiatives",
                "amount": 50000,
            },
            headers=auth_header(token),
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Community Health Fund"
        assert data["grantor_id"] == str(grantor.id)

    def test_grantee_cannot_create_grant(self, client):
        token = register_and_login(client, "grantee-only@example.com")
        response = client.post(
            "/api/grants",
            json={"title": "Test", "description": "Desc", "amount": 1000},
            headers=auth_header(token),
        )
        assert response.status_code == 403

    def test_grantor_can_update_own_grant(self, client, db_session, auth_service):
        grantor = create_user_with_role(db_session, auth_service, "owner@example.com", RoleName.GRANTOR)
        token = login_as(client, grantor.email)

        create_response = client.post(
            "/api/grants",
            json={"title": "Original", "description": "Desc", "amount": 1000},
            headers=auth_header(token),
        )
        grant_id = create_response.json()["id"]

        response = client.put(
            f"/api/grants/{grant_id}",
            json={"title": "Updated Title"},
            headers=auth_header(token),
        )
        assert response.status_code == 200
        assert response.json()["title"] == "Updated Title"

    def test_grantor_cannot_update_other_grant(self, client, db_session, auth_service):
        owner = create_user_with_role(db_session, auth_service, "owner2@example.com", RoleName.GRANTOR)
        other = create_user_with_role(db_session, auth_service, "other@example.com", RoleName.GRANTOR)

        owner_token = login_as(client, owner.email)
        other_token = login_as(client, other.email)

        create_response = client.post(
            "/api/grants",
            json={"title": "Owner Grant", "description": "Desc", "amount": 1000},
            headers=auth_header(owner_token),
        )
        grant_id = create_response.json()["id"]

        response = client.put(
            f"/api/grants/{grant_id}",
            json={"title": "Hacked"},
            headers=auth_header(other_token),
        )
        assert response.status_code == 403

    def test_admin_can_delete_any_grant(self, client, db_session, auth_service):
        grantor = create_user_with_role(db_session, auth_service, "del-owner@example.com", RoleName.GRANTOR)
        admin = create_user_with_role(db_session, auth_service, "del-admin@example.com", RoleName.ADMIN)

        grantor_token = login_as(client, grantor.email)
        admin_token = login_as(client, admin.email)

        create_response = client.post(
            "/api/grants",
            json={"title": "Delete Me", "description": "Desc", "amount": 1000},
            headers=auth_header(grantor_token),
        )
        grant_id = create_response.json()["id"]

        response = client.delete(f"/api/grants/{grant_id}", headers=auth_header(admin_token))
        assert response.status_code == 204

    def test_get_grant_not_found(self, client):
        token = register_and_login(client, "viewer@example.com")
        response = client.get(
            "/api/grants/00000000-0000-0000-0000-000000000001",
            headers=auth_header(token),
        )
        assert response.status_code == 404
