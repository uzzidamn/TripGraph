# User Authentication & Persistent Memory — Implementation Plan

Source: `spec_user_auth_memory.md` (Version 1.0)

---

## Architecture

```
Client
  │
  ├── POST /api/auth/register  ─►  backend/api/auth_routes.py
  ├── POST /api/auth/login     ─►  backend/api/auth_routes.py
  ├── GET  /api/auth/me        ─►  backend/api/auth_routes.py  (protected)
  ├── GET  /api/memory         ─►  backend/api/memory_routes.py (protected)
  └── PATCH /api/memory        ─►  backend/api/memory_routes.py (protected)

  Auth middleware (FastAPI Depends):
    backend/auth/dependencies.py  ─► decode JWT ─► lookup user ─► return User ORM

  DB layer:
    backend/db/models.py     — SQLAlchemy ORM: User, UserMemory, JsonList TypeDecorator
    backend/db/session.py    — engine + SessionLocal + get_db() dependency
    backend/db/init_db.py    — create_all() called at startup

  Memory:
    backend/memory/sql_store.py  — SQL implementations of get/update user memory
    backend/memory/store.py      — updated: routes to sql_store (drops JSON-file impl)
```

---

## Implementation Order

Dependencies must be respected — each step only imports from steps before it.

1. `backend/requirements.txt` — add new packages
2. `backend/config.py` — add new env vars
3. `backend/db/models.py` — ORM models
4. `backend/db/session.py` — DB engine + session factory
5. `backend/db/init_db.py` — table creation
6. `backend/auth/utils.py` — password hashing + JWT helpers
7. `backend/auth/dependencies.py` — FastAPI auth dependency
8. `backend/memory/sql_store.py` — SQL memory CRUD
9. `backend/memory/store.py` — replace JSON impl
10. `backend/api/auth_routes.py` — auth endpoints
11. `backend/api/memory_routes.py` — memory endpoints
12. `backend/main.py` — register routers, init_db on startup, validate JWT secret
13. `.env.example` — document new vars

---

## Step 1 — `backend/requirements.txt`

Add three packages. Pin loosely so pip resolves compatible versions.

```
sqlalchemy>=2.0.0
passlib[bcrypt]>=1.7.4
python-jose[cryptography]>=3.3.0
```

---

## Step 2 — `backend/config.py`

Add to the `Settings` class (import side-effect: startup fails loudly if `JWT_SECRET_KEY` is absent):

```python
# Auth / DB (spec Section 7)
DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./tripgraph.db")
JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "")
JWT_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", "10080"))

def __post_init__(self):
    if not self.JWT_SECRET_KEY:
        raise RuntimeError(
            "JWT_SECRET_KEY is not set. Add it to .env — "
            "generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
        )
```

`Settings` is currently a plain class (not a dataclass), so use `__init__` instead:

```python
class Settings:
    ...
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "")

    def __init__(self):
        if not self.JWT_SECRET_KEY:
            raise RuntimeError(
                "JWT_SECRET_KEY is not set. Add it to .env — "
                "generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
            )

settings = Settings()
```

This satisfies **AC 12** — startup fails clearly without the secret.

---

## Step 3 — `backend/db/models.py` (new file)

```python
import json
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.types import TypeDecorator


class JsonList(TypeDecorator):
    """Store a Python list as a JSON string in a TEXT column."""
    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return "[]"
        return json.dumps(value, ensure_ascii=False)

    def process_result_value(self, value, dialect):
        if not value:
            return []
        try:
            return json.loads(value)
        except Exception:
            return []


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    memory: Mapped["UserMemory"] = relationship(
        "UserMemory", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )


class UserMemory(Base):
    __tablename__ = "user_memory"

    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    preferred_origins: Mapped[list] = mapped_column(JsonList, nullable=False, default=list)
    preferred_destinations: Mapped[list] = mapped_column(JsonList, nullable=False, default=list)
    budget_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    budget_max: Mapped[int | None] = mapped_column(Integer, nullable=True)
    preferred_hotel_tier: Mapped[str | None] = mapped_column(String(50), nullable=True)
    activity_preferences: Mapped[list] = mapped_column(JsonList, nullable=False, default=list)
    avoidances: Mapped[list] = mapped_column(JsonList, nullable=False, default=list)
    travel_style: Mapped[str | None] = mapped_column(String(100), nullable=True)
    past_trips: Mapped[list] = mapped_column(JsonList, nullable=False, default=list)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    user: Mapped["User"] = relationship("User", back_populates="memory")
```

---

## Step 4 — `backend/db/session.py` (new file)

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from backend.config import settings

# SQLite needs check_same_thread=False for FastAPI's threaded request handling.
# For PostgreSQL, remove connect_args.
_connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(settings.DATABASE_URL, connect_args=_connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """FastAPI dependency that yields a DB session and ensures it is closed."""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

---

## Step 5 — `backend/db/init_db.py` (new file)

```python
from backend.db.models import Base
from backend.db.session import engine


def create_tables() -> None:
    """Create all tables if they don't exist. Safe to call on every startup."""
    Base.metadata.create_all(bind=engine)
```

---

## Step 6 — `backend/auth/utils.py` (new file)

```python
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from backend.config import settings

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
_ALGORITHM = "HS256"


def hash_password(plain: str) -> str:
    return _pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd_context.verify(plain, hashed)


def create_access_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=_ALGORITHM)


def decode_access_token(token: str) -> int | None:
    """Decode a JWT and return user_id (int), or None on any failure."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[_ALGORITHM])
        sub = payload.get("sub")
        if sub is None:
            return None
        return int(sub)
    except (JWTError, ValueError):
        return None
```

---

## Step 7 — `backend/auth/dependencies.py` (new file)

Two dependencies — one that raises on missing token, one that returns `None` for optional auth:

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from backend.auth.utils import decode_access_token
from backend.db.models import User
from backend.db.session import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Require a valid token. Raises 401 if missing, expired, or for an inactive user."""
    _401 = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise _401
    user_id = decode_access_token(token)
    if user_id is None:
        raise _401
    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise _401
    return user


def get_optional_user(
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User | None:
    """Return the user if a valid token is present, else None (anonymous)."""
    if not token:
        return None
    user_id = decode_access_token(token)
    if user_id is None:
        return None
    user = db.get(User, user_id)
    return user if (user and user.is_active) else None
```

---

## Step 8 — `backend/memory/sql_store.py` (new file)

Mirrors the exact dict shape returned by the old JSON store so the planning pipeline sees no difference.

```python
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from backend.db.models import UserMemory
from backend.db.session import SessionLocal

_DEFAULT: dict = {
    "user_id": None,
    "preferred_origins": [],
    "preferred_destinations": [],
    "budget_range": {"min": 0, "max": 0},
    "preferred_hotel_tier": None,
    "activity_preferences": [],
    "avoidances": [],
    "travel_style": None,
    "past_trips": [],
}


def _row_to_dict(row: UserMemory, user_id: int) -> dict:
    return {
        "user_id": user_id,
        "preferred_origins": row.preferred_origins,
        "preferred_destinations": row.preferred_destinations,
        "budget_range": {"min": row.budget_min or 0, "max": row.budget_max or 0},
        "preferred_hotel_tier": row.preferred_hotel_tier,
        "activity_preferences": row.activity_preferences,
        "avoidances": row.avoidances,
        "travel_style": row.travel_style,
        "past_trips": row.past_trips,
    }


def get_user_memory(user_id: int) -> dict:
    """Load memory for user_id from the DB. Returns empty default on any error."""
    try:
        with SessionLocal() as db:
            row = db.get(UserMemory, user_id)
            if row is None:
                return dict(_DEFAULT) | {"user_id": user_id}
            return _row_to_dict(row, user_id)
    except Exception as e:
        print(f"  ⚠️  SQL memory read failed for {user_id}: {e}")
        return dict(_DEFAULT)


def update_user_memory(user_id: int, updates: dict) -> None:
    """Merge updates into the user's DB memory row. Preserves existing data."""
    if not user_id or not updates:
        return
    try:
        with SessionLocal() as db:
            row = db.get(UserMemory, user_id)
            if row is None:
                row = UserMemory(user_id=user_id)
                db.add(row)

            for key, value in updates.items():
                if value is None or value == [] or value == {}:
                    continue  # never overwrite with empty

                if key == "preferred_origins":
                    row.preferred_origins = value
                elif key == "preferred_destinations":
                    row.preferred_destinations = value
                elif key == "budget_range" and isinstance(value, dict):
                    row.budget_min = value.get("min") or row.budget_min
                    row.budget_max = value.get("max") or row.budget_max
                elif key == "preferred_hotel_tier":
                    row.preferred_hotel_tier = value
                elif key == "activity_preferences":
                    row.activity_preferences = value
                elif key == "avoidances":
                    row.avoidances = value
                elif key == "travel_style":
                    row.travel_style = value
                elif key == "past_trips" and isinstance(value, list):
                    existing = row.past_trips or []
                    row.past_trips = existing + [v for v in value if v not in existing]

            row.updated_at = datetime.now(timezone.utc)
            db.commit()
    except Exception as e:
        print(f"  ⚠️  SQL memory write failed for {user_id}: {e}")
```

---

## Step 9 — `backend/memory/store.py`

Replace the JSON-file implementation. The public function signatures stay identical so all callers (`memory_agent_node`, `workflow.py`, etc.) need no changes.

`user_id` changes from `str` to `int | str` — the SQL store accepts int; legacy callers passing a string get it coerced.

```python
"""
User memory store — SQL-backed (SQLite by default, PostgreSQL-ready).

Public API matches the old JSON-file store so all callers are unchanged:
  get_user_memory(user_id) -> dict
  update_user_memory(user_id, updates) -> None
"""


def _coerce_id(user_id) -> int | None:
    """Coerce str user_id to int for DB lookup. Returns None on failure."""
    if user_id is None:
        return None
    try:
        return int(user_id)
    except (ValueError, TypeError):
        return None


def get_user_memory(user_id) -> dict:
    uid = _coerce_id(user_id)
    if uid is None:
        from backend.memory.sql_store import _DEFAULT
        return dict(_DEFAULT)
    from backend.memory.sql_store import get_user_memory as _get
    return _get(uid)


def update_user_memory(user_id, updates: dict) -> None:
    uid = _coerce_id(user_id)
    if uid is None:
        return
    from backend.memory.sql_store import update_user_memory as _update
    _update(uid, updates)
```

---

## Step 10 — `backend/api/auth_routes.py` (new file)

```python
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from backend.auth.dependencies import get_current_user
from backend.auth.utils import create_access_token, hash_password, verify_password
from backend.db.models import User, UserMemory
from backend.db.session import get_db

router = APIRouter(prefix="/api/auth", tags=["Auth"])


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    display_name: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class RegisterResponse(TokenResponse):
    user_id: int
    email: str
    display_name: str | None


class MeResponse(BaseModel):
    user_id: int
    email: str
    display_name: str | None
    created_at: datetime


@router.post("/register", response_model=RegisterResponse, status_code=201)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=body.email,
        hashed_password=hash_password(body.password),
        display_name=body.display_name,
        created_at=datetime.now(timezone.utc),
    )
    db.add(user)
    db.flush()  # populate user.id before creating memory row

    db.add(UserMemory(user_id=user.id))
    db.commit()
    db.refresh(user)

    return RegisterResponse(
        user_id=user.id,
        email=user.email,
        display_name=user.display_name,
        access_token=create_access_token(user.id),
    )


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email).first()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    return TokenResponse(access_token=create_access_token(user.id))


@router.get("/me", response_model=MeResponse)
def me(current_user: User = Depends(get_current_user)):
    return MeResponse(
        user_id=current_user.id,
        email=current_user.email,
        display_name=current_user.display_name,
        created_at=current_user.created_at,
    )
```

---

## Step 11 — `backend/api/memory_routes.py` (new file)

```python
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Any

from backend.auth.dependencies import get_current_user
from backend.db.models import User
from backend.memory.store import get_user_memory, update_user_memory

router = APIRouter(prefix="/api", tags=["Memory"])


class MemoryPatch(BaseModel):
    preferred_origins: list[str] | None = None
    preferred_destinations: list[str] | None = None
    budget_range: dict[str, int] | None = None
    preferred_hotel_tier: str | None = None
    activity_preferences: list[str] | None = None
    avoidances: list[str] | None = None
    travel_style: str | None = None
    past_trips: list[Any] | None = None


@router.get("/memory")
def get_memory(current_user: User = Depends(get_current_user)) -> dict:
    return get_user_memory(current_user.id)


@router.patch("/memory")
def patch_memory(
    body: MemoryPatch,
    current_user: User = Depends(get_current_user),
) -> dict:
    updates = body.model_dump(exclude_none=True)
    update_user_memory(current_user.id, updates)
    return get_user_memory(current_user.id)
```

---

## Step 12 — `backend/main.py`

Three changes — all additive, no removals:

**1. Register new routers** (after existing `include_router` calls):
```python
from backend.api.auth_routes import router as auth_router
from backend.api.memory_routes import router as memory_router

app.include_router(auth_router)
app.include_router(memory_router)
```

**2. Call `create_tables()` on startup** (in the `_print_integration_banner` event or a new startup event):
```python
@app.on_event("startup")
async def _init_database():
    from backend.db.init_db import create_tables
    create_tables()
```

**3. Existing routes that pass `user_id` in the body** are already backward-compatible — they call `get_user_memory(user_id)` through `store.py`, which now routes to SQL. No changes needed to `chat_routes.py` or `itinerary_routes.py`.

---

## Step 13 — `.env.example`

Add three lines:

```
DATABASE_URL=sqlite:///./tripgraph.db
JWT_SECRET_KEY=change-me-to-a-random-32-char-string
JWT_EXPIRE_MINUTES=10080
```

---

## Output Schema

### `GET /api/memory` response
```json
{
  "user_id": 42,
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

### `POST /api/auth/register` response (201)
```json
{
  "user_id": 42,
  "email": "user@example.com",
  "display_name": "Aman",
  "access_token": "<JWT>",
  "token_type": "bearer"
}
```

---

## File Layout

```
backend/
├── auth/
│   ├── __init__.py
│   ├── utils.py           # hash_password, verify_password, create/decode token
│   └── dependencies.py    # get_current_user, get_optional_user
├── db/
│   ├── __init__.py
│   ├── models.py          # User, UserMemory ORM, JsonList TypeDecorator
│   ├── session.py         # engine, SessionLocal, get_db()
│   └── init_db.py         # create_tables()
├── memory/
│   ├── sql_store.py       # NEW — SQL implementation of get/update memory
│   └── store.py           # REPLACED — thin router, same public API
├── api/
│   ├── auth_routes.py     # NEW — /api/auth/* endpoints
│   └── memory_routes.py   # NEW — /api/memory endpoints
├── config.py              # MODIFIED — add DATABASE_URL, JWT_SECRET_KEY, JWT_EXPIRE_MINUTES
├── main.py                # MODIFIED — register routers, init_db on startup
└── requirements.txt       # MODIFIED — add sqlalchemy, passlib[bcrypt], python-jose
```

---

## Acceptance Criteria Coverage

| AC | Statement | Implementation |
|----|-----------|----------------|
| 1 | Register creates user + memory row, returns JWT | `auth_routes.py` register handler: `db.flush()` → `UserMemory()` → `create_access_token()` |
| 2 | Duplicate email returns 400 | `auth_routes.py`: query before insert, raise `HTTPException(400)` |
| 3 | Login with correct credentials returns JWT | `auth_routes.py` login handler: `verify_password()` → `create_access_token()` |
| 4 | Wrong password returns 401 | Same handler: single `HTTPException(401)` for both bad email and bad password |
| 5 | `/api/auth/me` requires valid token | `get_current_user` dependency on `me` route |
| 6 | Expired/tampered token raises 401 | `decode_access_token()` catches `JWTError` → returns None → `get_current_user` raises 401 |
| 7 | Memory persists across requests | `sql_store.py`: commits to SQLite, `get_user_memory` reads same row |
| 8 | Merge doesn't overwrite with empty | `sql_store.update_user_memory`: `if value is None or value == [] or value == {}: continue` |
| 9 | `past_trips` appends without duplicating | `sql_store`: `existing + [v for v in value if v not in existing]` |
| 10 | Planning pipeline unchanged | `store.py` public API is identical; callers unchanged; `user_id` coerced int→str internally |
| 11 | Memory failure is non-fatal | Both `get_user_memory` and `update_user_memory` in `sql_store.py` wrap all DB calls in `try/except`, log warning, return default |
| 12 | Startup fails without JWT secret | `Settings.__init__` raises `RuntimeError` if `JWT_SECRET_KEY` is empty |
