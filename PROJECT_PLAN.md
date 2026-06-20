# Grant Management Portal — Project Plan

## Epics Overview

| Epic | Description |
|------|-------------|
| User Authentication | Registration, login, OAuth 2.0, and JWT session management |
| Grant Management | CRUD operations for funding opportunities by grantors |
| Application Submission | Grantees apply to grants; grantors review submissions |
| Admin & RBAC | Role assignment and permission enforcement |

---

## Epic 1: User Authentication

### User Story 1: OAuth Sign-In

**As a** new user, **I want to** sign in with my Google account **so that** I don't have to remember another password.

**Acceptance Criteria:**
- A `GET /api/auth/google` endpoint redirects to Google's authorization page.
- The callback endpoint exchanges the authorization code for an access token.
- Upon successful authentication, a new user account is created with the GRANTEE role if one does not exist.
- The user is issued a JWT containing their user ID and roles.

### User Story 2: Email/Password Registration

**As a** grant applicant, **I want to** register with my email and password **so that** I can access the portal without using a third-party provider.

**Acceptance Criteria:**
- `POST /api/auth/register` accepts name, email, and password and returns 201 with user details (no password).
- Duplicate email registration returns a 400 error.
- New users are automatically assigned the GRANTEE role.

---

## Epic 2: Grant Management

### User Story 3: Create a Grant

**As a** grantor, **I want to** publish funding opportunities **so that** grantees can discover and apply for them.

**Acceptance Criteria:**
- `POST /api/grants` creates a grant with title, description, and amount.
- Only users with the GRANTOR role can create grants.
- The grant is linked to the creating user as `grantor_id`.

### User Story 4: Manage Own Grants

**As a** grantor, **I want to** update or delete my grants **so that** I can keep funding information accurate.

**Acceptance Criteria:**
- `PUT /api/grants/{id}` updates a grant only when the requester is the owning grantor.
- `DELETE /api/grants/{id}` allows deletion by the owning grantor or an ADMIN.
- Other grantors receive 403 when attempting to modify grants they do not own.

---

## Epic 3: Application Submission

### User Story 5: Apply for a Grant

**As a** grantee, **I want to** submit a proposal for a grant **so that** I can request funding.

**Acceptance Criteria:**
- `POST /api/grants/{id}/apply` accepts a proposal and returns 201 with the application object.
- Only GRANTEE users can submit applications.
- Duplicate applications from the same grantee to the same grant are rejected.

### User Story 6: Review Applications

**As a** grantor, **I want to** view all applications for my grants **so that** I can evaluate proposals.

**Acceptance Criteria:**
- `GET /api/grants/{id}/applications` returns applications for the specified grant.
- Only the grantor who owns the grant can access the list.
- Other grantors receive 403 when accessing applications for grants they do not own.

---

## Epic 4: Admin & RBAC

### User Story 7: Assign Roles

**As an** admin, **I want to** assign roles to users **so that** they can perform role-appropriate actions.

**Acceptance Criteria:**
- `POST /api/users/{id}/roles` assigns a role (ADMIN, GRANTOR, or GRANTEE) to a user.
- Only ADMIN users can access this endpoint.
- Invalid role names return 400.

### User Story 8: Secure API Access

**As a** platform operator, **I want** all protected endpoints to enforce RBAC **so that** users cannot access unauthorized resources.

**Acceptance Criteria:**
- Requests without a valid JWT receive 401.
- Requests with a valid JWT but insufficient role receive 403.
- JWT payload includes `userId` and `roles` array.

---

## Sprint Milestones

1. **Sprint 1:** Docker setup, database models, seed script, local auth
2. **Sprint 2:** OAuth integration, RBAC middleware, grant endpoints
3. **Sprint 3:** Application endpoints, admin user management
4. **Sprint 4:** Test suite, coverage report, documentation
