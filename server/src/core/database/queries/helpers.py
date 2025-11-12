from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError, SQLAlchemyError


from src.core.database.models import *


async def insert_object_model(
    session: AsyncSession,
    base_model: (UserAccounts
                 | UserProfiles
                 | Tickets
                 | RequestTypes
                 | PriorityTypes
                 | StatusTypes
                 | Teams
                 | TicketAttachments),
    data_model: dict
):
    object_model = base_model(**data_model)
    session.add(object_model)

    try:
        await session.flush()
        await session.commit()

    except IntegrityError:
        await session.rollback()
        raise

    except SQLAlchemyError:
        await session.rollback()
        raise

    await session.refresh(object_model)

    return object_model
