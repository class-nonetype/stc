from __future__ import annotations

from typing import Final

from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from src.utils import (DATABASE_URL, DATABASE_DRIVERS)



def _ensure_async_driver(database_url: str) -> str:
    url = make_url(database_url)

    if "+" in url.drivername: return database_url

    try:

        updated = url.set(drivername=DATABASE_DRIVERS[url.drivername])

    except KeyError as exc:
        raise ValueError(
            f"Unsupported driver '{url.drivername}' for async usage. "
            "Provide an async-capable DATABASE_URL."
        ) from exc

    return updated.render_as_string(hide_password=False)


ASYNC_DATABASE_URL: Final[str] = _ensure_async_driver(DATABASE_URL)

engine: AsyncEngine = create_async_engine(
    url=ASYNC_DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
)

__all__ = (
    "ASYNC_DATABASE_URL",
    "engine",
)
