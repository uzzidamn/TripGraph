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
    display_name: str | None = None


class MeResponse(BaseModel):
    user_id: int
    email: str
    display_name: str | None = None
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
    db.flush()  # populate user.id before creating the memory row

    db.add(UserMemory(user_id=user.id))
    db.commit()
    db.refresh(user)

    return RegisterResponse(
        user_id=user.id,
        email=user.email,
        display_name=user.display_name,
        access_token=create_access_token(user.id),
    )


@router.post("/login", response_model=RegisterResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email).first()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    return RegisterResponse(
        user_id=user.id,
        email=user.email,
        display_name=user.display_name,
        access_token=create_access_token(user.id),
    )


@router.get("/me", response_model=MeResponse)
def me(current_user: User = Depends(get_current_user)):
    return MeResponse(
        user_id=current_user.id,
        email=current_user.email,
        display_name=current_user.display_name,
        created_at=current_user.created_at,
    )
