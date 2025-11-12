from uuid import UUID

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database.session import database
from src.core.security.tokens import JWTBearer, verify_access_token
from src.core.database.queries.alter import update_user_online_status


async def touch_presence(
    Authorization: str = Depends(JWTBearer()),
    session: AsyncSession = Depends(database)
) -> None:
    """Dependency to bump user presence last_seen and mark online.

    Should be added alongside JWTBearer in route dependencies.
    """
    decoded = verify_access_token(token=Authorization, output=True)
    user_account_id = UUID(decoded['userAccountID'])
    # Mark online and update last_seen without altering route responses
    await update_user_online_status(session=session, user_account_id=user_account_id, is_online=True)
