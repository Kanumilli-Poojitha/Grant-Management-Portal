# Grant Management Portal

A secure, multi-user web API for managing grant applications with **Role-Based Access Control (RBAC)**, **OAuth 2.0** authentication, and an **MVC** architecture. Built with FastAPI, PostgreSQL, and Redis, fully containerized with Docker Compose.

## Features

- Email/password registration and login with JWT tokens
- Google OAuth 2.0 sign-in
- Three roles: `ADMIN`, `GRANTOR`, `GRANTEE`
- Grant CRUD with ownership-based permissions
- Grant application submission and review
- Redis-backed session management for JWT tokens
- Automated database seeding (roles + default admin)
- Test suite with ≥70% code coverage

## Architecture (MVC)

| Layer | Location | Responsibility |
|-------|----------|----------------|
| **Model** | `app/models/`, `app/services/` | Data entities and business logic |
| **View** | `app/schemas/` | JSON serialization (Pydantic) |
| **Controller** | `app/controllers/` | HTTP route handlers |

RBAC middleware lives in `app/middleware/rbac.py`.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose
- (Optional) Python 3.12+ for local development and testing

## Quick Start

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd Grant-Management-Portal
   ```

2. **Configure environment**

   ```bash
   cp .env.example .env
   ```

   Edit `.env` and set your Google OAuth credentials if you plan to test OAuth:

   - Register an app at [Google Cloud Console](https://console.cloud.google.com/)
   - Set authorized redirect URI to `http://localhost:8000/api/auth/google/callback`
   - Copy Client ID and Secret into `.env`

3. **Start all services**

   ```bash
   docker-compose up --build
   ```

   This starts:
   - **app** — FastAPI API on port 8000
   - **db** — PostgreSQL 16 on port 5432
   - **cache** — Redis 7 on port 6379

4. **Verify health**

   ```bash
   curl http://localhost:8000/health
   ```

5. **Explore the API**

   Open [http://localhost:8000/docs](http://localhost:8000/docs) for interactive Swagger documentation.

## Default Admin User

Seeded automatically on startup:

| Field | Value |
|-------|-------|
| Email | `admin@grantportal.com` |
| Password | `Admin123!` |
| Role | `ADMIN` |

## API Endpoints

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Register with email/password |
| POST | `/api/auth/login` | Login, returns JWT |
| GET | `/api/auth/google` | Redirect to Google OAuth |
| GET | `/api/auth/google/callback` | OAuth callback, returns JWT |
| POST | `/api/auth/logout` | Revoke JWT session |

### Users (Admin)

| Method | Endpoint | Required Role |
|--------|----------|---------------|
| GET | `/api/users` | ADMIN |
| POST | `/api/users/{id}/roles` | ADMIN |

### Grants

| Method | Endpoint | Required Role |
|--------|----------|---------------|
| POST | `/api/grants` | GRANTOR |
| GET | `/api/grants` | GRANTEE, GRANTOR, ADMIN |
| GET | `/api/grants/{id}` | GRANTEE, GRANTOR, ADMIN |
| PUT | `/api/grants/{id}` | GRANTOR (owner) |
| DELETE | `/api/grants/{id}` | GRANTOR (owner) or ADMIN |

### Applications

| Method | Endpoint | Required Role |
|--------|----------|---------------|
| POST | `/api/grants/{id}/apply` | GRANTEE |
| GET | `/api/grants/{id}/applications` | GRANTOR (owner) |
| GET | `/api/applications/{id}` | GRANTEE (submitter) or GRANTOR (owner) |

## JWT Format

Decoded payload:

```json
{
  "userId": "uuid",
  "roles": ["GRANTEE"],
  "iat": 1616239022,
  "exp": 1616242622
}
```

Use the token in subsequent requests:

```
Authorization: Bearer <accessToken>
```

## Example Workflow

```bash
# 1. Register a grantee
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"Alice","email":"alice@example.com","password":"SecurePass1"}'

# 2. Login as admin and assign GRANTOR role to a user
ADMIN_TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@grantportal.com","password":"Admin123!"}' | jq -r .accessToken)

# 3. Login as grantee
GRANTEE_TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"alice@example.com","password":"SecurePass1"}' | jq -r .accessToken)

# 4. List grants
curl http://localhost:8000/api/grants -H "Authorization: Bearer $GRANTEE_TOKEN"
```

## Running Tests

Install dependencies locally:

```bash
pip install -r requirements.txt
```

Run tests with coverage (requires ≥70% statement coverage):

```bash
make test-coverage
```

Or directly:

```bash
pytest --cov=app --cov-report=term-missing --cov-report=html:coverage --cov-fail-under=70
```

Coverage report is written to `coverage/index.html`.

## Environment Variables

See [`.env.example`](.env.example) for all required variables:

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string |
| `REDIS_URL` | Redis connection string |
| `JWT_SECRET` | Secret key for signing JWTs |
| `JWT_ALGORITHM` | JWT algorithm (default: HS256) |
| `JWT_EXPIRE_MINUTES` | Token lifetime in minutes |
| `OAUTH_CLIENT_ID` | Google OAuth client ID |
| `OAUTH_CLIENT_SECRET` | Google OAuth client secret |
| `OAUTH_REDIRECT_URI` | OAuth callback URL |
| `DEFAULT_ADMIN_EMAIL` | Seeded admin email |
| `DEFAULT_ADMIN_PASSWORD` | Seeded admin password |

## Project Structure

```
Grant-Management-Portal/
├── app/
│   ├── controllers/     # Route handlers (Controller)
│   ├── middleware/      # RBAC authentication
│   ├── models/          # SQLAlchemy models (Model)
│   ├── schemas/         # Pydantic schemas (View)
│   ├── services/        # Business logic (Model)
│   ├── config.py
│   ├── database.py
│   ├── main.py
│   └── seed.py
├── tests/
├── docker-compose.yml
├── Dockerfile
├── Makefile
├── PROJECT_PLAN.md
├── .env.example
└── README.md
```

## License

MIT

Demo video
https://drive.google.com/file/d/1A_hHrba_fL5dxabnV3kp3ITOaVZQSNc3/view?usp=sharing

Live video
https://drive.google.com/file/d/1OeM3AH-LQ65zg6_Q-oxeJrvX8bSlgiyE/view?usp=sharing
