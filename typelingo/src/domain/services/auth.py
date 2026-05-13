from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
from jose import JWTError, jwt

from src.config import settings

_ALGORITHM = "HS256"


def hash_password(plaintext: str) -> str:
    return bcrypt.hashpw(plaintext.encode(), bcrypt.gensalt()).decode()


def verify_password(plaintext: str, hashed: str) -> bool:
    return bcrypt.checkpw(plaintext.encode(), hashed.encode())


def create_access_token(
    subject: str,
    extra: dict[str, Any] | None = None,
) -> str:
    expire = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
    payload: dict[str, Any] = {"sub": subject, "exp": expire, **(extra or {})}
    return str(jwt.encode(payload, settings.secret_key, algorithm=_ALGORITHM))


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        return dict(jwt.decode(token, settings.secret_key, algorithms=[_ALGORITHM]))
    except JWTError as exc:
        raise ValueError(f"invalid token: {exc}") from exc
