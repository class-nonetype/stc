from src.core.database.base import Base
from src.core.database.engine import engine
from src.core.database.models import *
import asyncio

# NOTE:
# Table creation is not triggered at import time to avoid blocking async drivers.
# Use migrations or run Base.metadata.create_all() explicitly from a sync engine,
# or via async engine with conn.run_sync(Base.metadata.create_all).
async def init() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


asyncio.run(init())