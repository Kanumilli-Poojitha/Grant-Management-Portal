from jose import jwt

from tests.conftest import auth_header, register_and_login


class TestAuthRegistration:
    def test_register_success(self, client):
        response = client.post(
            "/api/auth/register",
            json={"name": "Jane Grantee", "email": "jane@example.com", "password": "SecurePass1"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "jane@example.com"
        assert data["name"] == "Jane Grantee"
        assert "password" not in data
        assert "id" in data

    def test_register_duplicate_email(self, client):
        payload = {"name": "User One", "email": "dup@example.com", "password": "SecurePass1"}
        client.post("/api/auth/register", json=payload)
        response = client.post("/api/auth/register", json=payload)
        assert response.status_code == 400


class TestAuthLogin:
    def test_login_success(self, client):
        client.post(
            "/api/auth/register",
            json={"name": "Login User", "email": "login@example.com", "password": "SecurePass1"},
        )
        response = client.post(
            "/api/auth/login",
            json={"email": "login@example.com", "password": "SecurePass1"},
        )
        assert response.status_code == 200
        assert "accessToken" in response.json()

    def test_login_invalid_credentials(self, client):
        response = client.post(
            "/api/auth/login",
            json={"email": "missing@example.com", "password": "wrongpassword"},
        )
        assert response.status_code == 401


class TestJwtPayload:
    def test_jwt_contains_user_id_and_roles(self, client):
        token = register_and_login(client, "jwt@example.com")
        payload = jwt.decode(token, key="", options={"verify_signature": False})
        assert "userId" in payload
        assert "roles" in payload
        assert "GRANTEE" in payload["roles"]
        assert "iat" in payload
        assert "exp" in payload


class TestGoogleOAuth:
    def test_google_redirect(self, client):
        response = client.get("/api/auth/google", follow_redirects=False)
        assert response.status_code == 307
        assert "accounts.google.com" in response.headers["location"]

    def test_google_callback_success(self, client, mock_redis):
        with (
            client as c,
        ):
            import app.services.auth_service as auth_module

            original_exchange = auth_module.AuthService._exchange_google_code
            original_profile = auth_module.AuthService._fetch_google_profile

            auth_module.AuthService._exchange_google_code = lambda self, code: {
                "access_token": "fake-token"
            }
            auth_module.AuthService._fetch_google_profile = lambda self, token: {
                "id": "google-123",
                "email": "oauth@example.com",
                "name": "OAuth User",
            }

            try:
                response = c.get("/api/auth/google/callback?code=valid-code")
                assert response.status_code == 200
                data = response.json()
                assert "accessToken" in data
                assert data["user"]["email"] == "oauth@example.com"
            finally:
                auth_module.AuthService._exchange_google_code = original_exchange
                auth_module.AuthService._fetch_google_profile = original_profile

    def test_google_callback_invalid_code(self, client):
        import app.services.auth_service as auth_module

        original = auth_module.AuthService._exchange_google_code
        auth_module.AuthService._exchange_google_code = lambda self, code: (_ for _ in ()).throw(
            ValueError("Failed to exchange authorization code")
        )
        try:
            response = client.get("/api/auth/google/callback?code=bad-code")
            assert response.status_code == 400
        finally:
            auth_module.AuthService._exchange_google_code = original


class TestLogout:
    def test_logout_revokes_token(self, client):
        token = register_and_login(client, "logout@example.com")
        response = client.post("/api/auth/logout", headers=auth_header(token))
        assert response.status_code == 204
