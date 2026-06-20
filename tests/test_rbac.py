from tests.conftest import (
    assign_role,
    auth_header,
    create_user_with_role,
    get_role,
    register_and_login,
)
from app.models import RoleName


class TestRbacMiddleware:
    def test_protected_route_without_token(self, client):
        response = client.get("/api/grants")
        assert response.status_code == 401

    def test_protected_route_with_invalid_token(self, client):
        response = client.get("/api/grants", headers={"Authorization": "Bearer invalid.token"})
        assert response.status_code == 401

    def test_grantee_can_list_grants(self, client):
        token = register_and_login(client, "grantee@example.com")
        response = client.get("/api/grants", headers=auth_header(token))
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestAdminEndpoints:
    def test_admin_can_assign_role(self, client, db_session, auth_service):
        admin = create_user_with_role(db_session, auth_service, "admin@test.com", RoleName.ADMIN)
        target = create_user_with_role(db_session, auth_service, "target@test.com", RoleName.GRANTEE)

        admin_token_response = client.post(
            "/api/auth/login",
            json={"email": admin.email, "password": "Password123"},
        )
        admin_token = admin_token_response.json()["accessToken"]

        response = client.post(
            f"/api/users/{target.id}/roles",
            json={"role": "GRANTOR"},
            headers=auth_header(admin_token),
        )
        assert response.status_code == 200

    def test_non_admin_cannot_assign_role(self, client, db_session, auth_service):
        grantee = create_user_with_role(db_session, auth_service, "notadmin@test.com", RoleName.GRANTEE)
        target = create_user_with_role(db_session, auth_service, "target2@test.com", RoleName.GRANTEE)

        token_response = client.post(
            "/api/auth/login",
            json={"email": grantee.email, "password": "Password123"},
        )
        token = token_response.json()["accessToken"]

        response = client.post(
            f"/api/users/{target.id}/roles",
            json={"role": "GRANTOR"},
            headers=auth_header(token),
        )
        assert response.status_code == 403

    def test_admin_can_list_users(self, client, db_session, auth_service):
        admin = create_user_with_role(db_session, auth_service, "admin2@test.com", RoleName.ADMIN)
        token_response = client.post(
            "/api/auth/login",
            json={"email": admin.email, "password": "Password123"},
        )
        token = token_response.json()["accessToken"]
        response = client.get("/api/users", headers=auth_header(token))
        assert response.status_code == 200
        assert len(response.json()) >= 1
