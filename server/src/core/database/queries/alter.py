from __future__ import annotations

from uuid import UUID

from sqlalchemy import and_, select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database.models.types import StatusTypes
from src.core.database.models.tickets import Tickets
from src.core.database.models import UserAccounts
from src.utils import get_datetime, logger

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



async def update_ticket(session: AsyncSession, context: str, ticket_id: UUID, object_id: UUID = None) -> (bool | None):
    try:
        match context:
            case 'status':
                statement = (
                    update(Tickets)
                    .where(Tickets.id == ticket_id, Tickets.is_active.is_(True))
                    .values(status_type_id=object_id, updated_at=get_datetime())
                )

                await session.execute(statement)
                await session.commit()

                return True


            case 'manager':
                # estado 'En proceso'
                status_query = (
                    select(StatusTypes.id)
                    .where(
                        StatusTypes.description.is_not(None),
                        func.lower(StatusTypes.description) == 'en proceso'
                    )
                    .limit(1)
                )

                result = await session.execute(status_query)
                status_id = result.scalar_one_or_none()

                if not status_id:
                    return None

                statement = (
                    update(Tickets)
                    .where(Tickets.id == ticket_id, Tickets.is_active.is_(True))
                    .values(
                        manager_id=object_id,
                        status_type_id=status_id,
                        updated_at=get_datetime())
                )

                await session.execute(statement)
                await session.commit()

                return True


            case 'read':
                statement = (
                    update(Tickets)
                    .where(Tickets.id == ticket_id, Tickets.is_readed.is_(False))
                    .values(is_readed=True, updated_at=get_datetime())
                )

                await session.execute(statement)
                await session.commit()

                return True

    except Exception as exception:
        logger.exception(msg=exception)
        await session.rollback()
        return False

