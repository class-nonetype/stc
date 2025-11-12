from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.utils.logger import logger
from src.core.database.engine import engine

SETTINGS = {
    "autoflush": False,
    "bind": engine,
    "expire_on_commit": False,
}

session = async_sessionmaker(class_=AsyncSession, **SETTINGS)


async def database() -> AsyncGenerator[AsyncSession, None]:
    async with session() as database:
        try:
            yield database
        except Exception as exception:
            await database.rollback()
            logger.exception(exception)
            raise
