from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.interfaces.repositories import IUserRepository
from src.domain.models.user import User
from src.infrastructure.database.models import UserORM


class PostgresUserRepository(IUserRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, user_id: UUID) -> User | None:
        row = await self._session.get(UserORM, user_id)
        return _to_domain(row) if row else None

    async def get_by_email(self, email: str) -> User | None:
        result = await self._session.execute(select(UserORM).where(UserORM.email == email))
        row = result.scalar_one_or_none()
        return _to_domain(row) if row else None

    async def save(self, user: User) -> None:
        row = await self._session.get(UserORM, user.id)
        if row is None:
            self._session.add(_to_orm(user))
        else:
            row.email = user.email
            row.display_name = user.display_name
            row.hashed_password = user.hashed_password
            row.is_guest = user.is_guest
            row.guest_expires_at = user.guest_expires_at
            row.updated_at = user.updated_at

    async def delete_expired_guests(self) -> int:
        result = await self._session.execute(
            delete(UserORM).where(
                UserORM.is_guest.is_(True),
                UserORM.guest_expires_at <= datetime.now(UTC),
            )
        )
        return result.rowcount


def _to_domain(row: UserORM) -> User:
    return User(
        id=row.id,
        email=row.email,
        display_name=row.display_name,
        hashed_password=row.hashed_password,
        is_guest=row.is_guest,
        guest_expires_at=row.guest_expires_at,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _to_orm(user: User) -> UserORM:
    return UserORM(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        hashed_password=user.hashed_password,
        is_guest=user.is_guest,
        guest_expires_at=user.guest_expires_at,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )
