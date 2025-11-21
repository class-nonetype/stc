"""Utility to initialize database tables using the async engine."""

from __future__ import annotations

import asyncio

from src.core.database.base import Base
from src.core.database.engine import engine


async def main() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


if __name__ == "__main__":
    asyncio.run(main())
