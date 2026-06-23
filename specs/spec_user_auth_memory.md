# TripGraph AI — User Authentication & Persistent Memory

Version: 1.1 (login is optional — memory is skipped for anonymous users)

---

# 1. Overview

## Purpose

Add optional user login/registration to TripGraph AI and replace the current JSON-file-based memory store (`/tmp/tripgraph_memory_{user_id}.json`) with a persistent SQL database.

The goal is to:
- Let users plan trips without any account (anonymous mode — full planning, no memory)
- Optionally identify users via JWT so their travel preferences and trip history persist across sessions
- Keep the planning pipeline unchanged — memory surfaces as a dict injected into the workflow when a user is logged in, and is simply skipped when they are not

---

# 2. Architecture Pattern

```
Client
  │
  ├── POST /api/auth/register   ─► UserDB (SQLite)  ─► JWT token
  ├── POST /api/auth/login      ─► UserDB (verify)  ─► JWT token
  │
  ├── POST /api/parse-chat          ┐
  ├── POST /api/generate-itinerary  ├─ optional Bearer token
  │                                 │
  │      token present  ─► user_id ─► MemoryDB (SQLite) ─► inject into pipeline
  │      no token       ─► skip memory, plan anonymously
  │
  ├── GET  /api/auth/me         ─► requires token
  ├── GET  /api/memory          ─► requires token
  └── PATCH /api/memory         ─► requires token
```

Database: **SQLite** (zero-config, built into Python).
ORM: **SQLAlchemy** (sync, Core + ORM layer).
Upgrade path: change `DATABASE_URL` in `.env` from `sqlite:///./tripgraph.db` to a PostgreSQL DSN — no code changes required.

---

# 3. Capabilities

This feature adds:

- User registration (email + password)
- User login returning a signed JWT access token
- **Optional auth on planning routes** — token present → load memory; no token → plan without memory
- SQL-backed memory store replacing the current `/tmp` JSON file store
- Memory CRUD: read preferences, append past trips, update preferences on every plan
- Backward-compatible: existing routes that pass `user_id` in the request body continue to work; the token-derived `user_id` takes precedence when both are present

---

# 4. Database Schema

## Table: `users`

| Column         | Type         | Constraints              |
|----------------|--------------|--------------------------|
| `id`           | INTEGER      | PRIMARY KEY, AUTOINCREMENT |
| `email`        | VARCHAR(255) | UNIQUE, NOT NULL, INDEX  |
| `hashed_password` | VARCHAR(255) | NOT NULL              |
| `display_name` | VARCHAR(100) | nullable                 |
| `created_at`   | DATETIME     | NOT NULL, default now()  |
| `is_active`    | BOOLEAN      | NOT NULL, default TRUE   |

## Table: `user_memory`

Mirrors the existing `_DEFAULT_MEMORY` dict so the planning pipeline sees the same shape.

| Column                    | Type         | Constraints              |
|---------------------------|--------------|--------------------------|
| `user_id`                 | INTEGER      | FK → users.id, PRIMARY KEY |
| `preferred_origins`       | TEXT (JSON)  | NOT NULL, default `[]`   |
| `preferred_destinations`  | TEXT (JSON)  | NOT NULL, default `[]`   |
| `budget_min`              | INTEGER      | nullable                 |
| `budget_max`              | INTEGER      | nullable                 |
| `preferred_hotel_tier`    | VARCHAR(50)  | nullable                 |
| `activity_preferences`    | TEXT (JSON)  | NOT NULL, default `[]`   |
| `avoidances`              | TEXT (JSON)  | NOT NULL, default `[]`   |
| `travel_style`            | VARCHAR(100) | nullable                 |
| `past_trips`              | TEXT (JSON)  | NOT NULL, default `[]`   |
| `updated_at`              | DATETIME     | NOT NULL, updated on write |

JSON list columns are stored as serialised JSON strings (SQLite has no native array type). SQLAlchemy `TypeDecorator` handles encode/decode transparently.

---

# 5. API Endpoints

## POST /api/auth/register

Register a new user.

**Request body:**
```json
{
  "email": "user@example.com",
  "password": "secret123",
  "display_name": "Aman"
}
```

**Response 201:**
```json
{
  "user_id": 42,
  "email": "user@example.com",
  "display_name": "Aman",
  "access_token": "<JWT>",
  "token_type": "bearer"
}
```

**Errors:**
- `400` — email already registered
- `422` — validation error (email format, password length < 8)

---

## POST /api/auth/login

Authenticate and get a token.

**Request body (form OR JSON):**
```json
{
  "email": "user@example.com",
  "password": "secret123"
}
```

**Response 200:**
```json
{
  "access_token": "<JWT>",
  "token_type": "bearer"
}
```

**Errors:**
- `401` — incorrect email or password

---

## GET /api/auth/me

Return the logged-in user's profile.

**Headers:** `Authorization: Bearer <token>`

**Response 200:**
```json
{
  "user_id": 42,
  "email": "user@example.com",
  "display_name": "Aman",
  "created_at": "2026-06-23T10:00:00Z"
}
```

---

## GET /api/memory

Return the logged-in user's stored travel memory.

**Headers:** `Authorization: Bearer <token>`

**Response 200:**
```json
{
  "preferred_origins": ["Gurugram"],
  "preferred_destinations": ["Rishikesh", "Jaipur"],
  "budget_range": {"min": 10000, "max": 20000},
  "preferred_hotel_tier": "comfort",
  "activity_preferences": ["rafting", "hiking"],
  "avoidances": ["flights"],
  "travel_style": "adventure",
  "past_trips": [{"destination": "Rishikesh", "date": "2026-01-15"}]
}
```

---

## PATCH /api/memory

Merge updates into the user's memory (same semantics as the current `update_user_memory` function).

**Headers:** `Authorization: Bearer <token>`

**Request body (all fields optional):**
```json
{
  "preferred_origins": ["Gurugram"],
  "activity_preferences": ["rafting"],
  "past_trips": [{"destination": "Rishikesh", "date": "2026-01-15"}]
}
```

**Response 200:** Updated memory object (same shape as GET /api/memory).

---

# 6. Authentication Details

## Token format

- Algorithm: `HS256`
- Payload: `{ "sub": "<user_id as str>", "exp": <unix timestamp> }`
- Expiry: configurable via `JWT_EXPIRE_MINUTES` (default: 10080 = 7 days)
- Secret: `JWT_SECRET_KEY` env variable — must be set; startup fails with a clear error if missing

## Password storage

- Hash with `bcrypt` via `passlib[bcrypt]`
- Plain-text password never stored or logged

## Auth middleware

A FastAPI dependency `get_current_user(token: str = Depends(oauth2_scheme))`:
1. Decode the JWT with `python-jose`
2. Look up `users` table by `sub` (user_id)
3. Raise `401` on expired/invalid token or inactive user
4. Return the `User` ORM object

Existing routes that accept `user_id` in the request body keep working without a token. When a valid token is present, the token-derived `user_id` is used and the body field is ignored.

---

# 7. Configuration Management

## New environment variables

| Variable           | Default                        | Purpose                           |
|--------------------|--------------------------------|-----------------------------------|
| `DATABASE_URL`     | `sqlite:///./tripgraph.db`     | SQLAlchemy connection string       |
| `JWT_SECRET_KEY`   | *(no default — required)*      | Signs/verifies JWT tokens          |
| `JWT_EXPIRE_MINUTES` | `10080`                      | Token lifetime (7 days)            |

Add to `.env.example`:
```
DATABASE_URL=sqlite:///./tripgraph.db
JWT_SECRET_KEY=change-me-to-a-random-32-char-string
JWT_EXPIRE_MINUTES=10080
```

---

# 8. Functional Requirements

The system shall:

- Allow any client to call `/api/parse-chat` and `/api/generate-itinerary` without a token (anonymous planning)
- When a valid Bearer token is present on a planning request, load the user's memory from the DB and inject it into the pipeline
- When no token is present on a planning request, skip memory entirely and plan as if no history exists
- Register a user with a unique email and bcrypt-hashed password
- Return a signed JWT on successful registration and login
- Reject login with incorrect credentials with a `401` (never reveal which field is wrong)
- Validate email format and enforce a minimum password length of 8 characters
- Create an empty `user_memory` row on first registration
- Load memory from the SQL DB instead of the `/tmp` JSON file
- Merge memory updates without overwriting existing data with empty values (preserve current `update_user_memory` merge semantics)
- Append to `past_trips` without duplicating entries
- Never block a planning request due to a memory read/write error — fall back to empty memory on DB error
- Require a valid token for `GET /api/auth/me`, `GET /api/memory`, and `PATCH /api/memory`

---

# 9. Deliverables

| Deliverable             | File                                   |
|-------------------------|----------------------------------------|
| SQLAlchemy models       | `backend/db/models.py`                 |
| DB session factory      | `backend/db/session.py`                |
| DB initialisation       | `backend/db/init_db.py`                |
| Auth utilities          | `backend/auth/utils.py`                |
| Auth dependency         | `backend/auth/dependencies.py`         |
| Auth routes             | `backend/api/auth_routes.py`           |
| Memory routes           | `backend/api/memory_routes.py`         |
| SQL memory store        | `backend/memory/sql_store.py`          |
| Updated memory store    | `backend/memory/store.py` (replace JSON impl) |
| Updated config          | `backend/config.py` (add new vars)     |
| Updated main.py         | `backend/main.py` (register routers, call init_db) |
| Updated requirements    | `backend/requirements.txt`             |
| Optional auth on parse-chat | `backend/api/chat_routes.py` (add `get_optional_user`) |
| Optional auth on generate-itinerary | `backend/api/itinerary_routes.py` (add `get_optional_user`) |
| Memory load in constraints path | `backend/agents/workflow.py` (`run_workflow_from_constraints` accepts `user_id`) |

---

# 10. Acceptance Criteria

## AC 1 — Register new user
Given a POST to `/api/auth/register` with a valid email and password ≥ 8 chars,
the system shall create a user row, create an empty memory row, and return a valid JWT.

## AC 2 — Reject duplicate email
Given a POST to `/api/auth/register` with an email already in the DB,
the system shall return `400 Bad Request`.

## AC 3 — Login with correct credentials
Given a POST to `/api/auth/login` with the registered email and correct password,
the system shall return a valid JWT access token.

## AC 4 — Reject wrong password
Given a POST to `/api/auth/login` with an incorrect password,
the system shall return `401 Unauthorized` without revealing which field is wrong.

## AC 5 — Token-protected route
Given a GET to `/api/auth/me` with a valid Bearer token,
the system shall return the authenticated user's profile.

## AC 6 — Expired / invalid token rejected
Given a GET to `/api/auth/me` with an expired or tampered token,
the system shall return `401 Unauthorized`.

## AC 7 — Memory persists across requests
Given a PATCH to `/api/memory` that adds a preferred origin,
a subsequent GET to `/api/memory` shall return the updated value.

## AC 8 — Memory merge does not overwrite with empty
Given an existing memory with `activity_preferences: ["rafting"]`,
a PATCH with `activity_preferences: []` shall leave the existing value unchanged.

## AC 9 — past_trips appends, no duplicates
Given a memory with one past trip entry,
a PATCH with the same trip entry shall not duplicate it.

## AC 10 — Anonymous planning works without a token
Given a request to `/api/parse-chat` or `/api/generate-itinerary` with no Bearer token,
the system shall plan normally with empty memory and return a full response.
No `401` shall be raised.

## AC 10b — Logged-in planning loads memory
Given a request to `/api/parse-chat` or `/api/generate-itinerary` with a valid Bearer token,
the system shall resolve the `user_id` from the token, load memory from the DB,
and inject it into the pipeline — with no change to the response format.

## AC 11 — Memory failure is non-fatal
Given a DB error during memory read,
the planning pipeline shall proceed with empty default memory and log a warning.

## AC 12 — Startup fails clearly without JWT secret
Given `JWT_SECRET_KEY` is not set,
the application shall raise a `RuntimeError` at startup with a clear message.

---

# 11. Out of Scope

- OAuth2 social login (Google, GitHub)
- Email verification
- Password reset flow
- Role-based access control
- Rate limiting on auth endpoints
- PostgreSQL migration scripts (switching is a one-line env var change)
