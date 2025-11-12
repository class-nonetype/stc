from __future__ import annotations

from uuid import UUID

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database.models import UserAccounts
from src.utils import get_datetime


async def update_last_login_date(session: AsyncSession, user_account_id: UUID) -> bool:
    try:
        stmt = (
            update(UserAccounts)
            .where(and_(UserAccounts.id == user_account_id, UserAccounts.active == True))  # noqa: E712
            .values(last_login_date=get_datetime())
        )
        await session.execute(stmt)
        await session.commit()
        return True
    except Exception:  # pylint: disable=broad-except
        await session.rollback()
        return False

