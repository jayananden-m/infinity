from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.dependencies import get_current_user_id, get_db
from src.domain.models.user import User
from src.domain.services.auth import (
    create_access_token,
    hash_password,
    verify_password,
)
from src.infrastructure.database.repositories.user_repository import (
    PostgresUserRepository,
)
from src.observability.logging import get_logger

router = APIRouter(prefix="/auth", tags=["auth"])
_log = get_logger(__name__)


class RegisterRequest(BaseModel):
    email: EmailStr
    display_name: str
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"  # — not a password, OAuth2 field name


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    body: RegisterRequest,
    session: AsyncSession = Depends(get_db),
) -> TokenResponse:
    repo = PostgresUserRepository(session)
    if await repo.get_by_email(body.email):
        raise HTTPException(status.HTTP_409_CONFLICT, detail="email already registered")
    user = User.create(body.email, body.display_name, hash_password(body.password))
    await repo.save(user)
    _log.info("user.registered", user_id=str(user.id))
    return TokenResponse(access_token=create_access_token(str(user.id)))


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    session: AsyncSession = Depends(get_db),
) -> TokenResponse:
    repo = PostgresUserRepository(session)
    user = await repo.get_by_email(body.email)
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="invalid credentials")
    _log.info("user.login", user_id=str(user.id))
    return TokenResponse(access_token=create_access_token(str(user.id)))


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    user_id: UUID = Depends(get_current_user_id),
) -> TokenResponse:
    """Issue a fresh access token in exchange for a still-valid one."""
    return TokenResponse(access_token=create_access_token(str(user_id)))


@router.post("/guest", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def create_guest(
    session: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Create a temporary guest user and return a JWT. Guest accounts expire after 7 days."""
    user = User.create_guest()
    repo = PostgresUserRepository(session)
    await repo.save(user)
    _log.info("user.guest_created", user_id=str(user.id))
    return TokenResponse(access_token=create_access_token(str(user.id)))
