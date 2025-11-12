from __future__ import annotations

import uuid

from bcrypt import gensalt, hashpw
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database.queries.helpers import insert_object_model
from src.core.database.models import *

from src.core.schemas.ticket_request import TicketRequest
from src.core.schemas.sign_up_request import SignUpRequest
from src.utils import generate_uuid_v4, logger
from sqlalchemy.exc import IntegrityError


async def insert_ticket(session: AsyncSession, schema: TicketRequest) -> Tickets:

    return await insert_object_model(
        session=session,
        base_model=Tickets,
        data_model={
            'code': schema.code.strip().upper(),
            'note': (schema.note or '').strip(),

            'request_type_id': schema.request_type_id,
            'priority_type_id': schema.priority_type_id,
            'status_type_id': schema.status_type_id,
            'requester_id': schema.requester_id,
            'team_id': schema.team_id,

            'due_at': schema.due_at,
            'resolved_at': schema.resolved_at,
            'closed_at': schema.closed_at,
        }
    )


async def insert_user_account(session: AsyncSession, schema: SignUpRequest) -> dict | bool:
    user_profile = await insert_object_model(
        session=session,
        base_model=UserProfiles,
        data_model={
            'full_name': schema.UserProfile.full_name.upper(),
            'email': schema.UserProfile.email
        }
    )

    user_account = await insert_object_model(
        session=session,
        base_model=UserAccounts,
        data_model={
            'user_profile_id': user_profile.id,
            'team_id': schema.TeamGroup.id,
            'username': schema.UserAccount.username,
            'password': hashpw(schema.UserAccount.password.encode("utf-8"), gensalt()).decode("utf-8"),
        }
    )

    return {
        'userProfileId': user_account.user_profile_id,
        'teamGroupId': user_account.team_id,
        'username': user_account.username,
    }

'''

async def insert_user_account(session: AsyncSession, schema: SignUpRequest) -> dict | bool:
    try:
        user_profile = UserProfiles(
            full_name=schema.UserProfile.full_name.upper(),
            email=schema.UserProfile.email
        )
        session.add(user_profile)
        try:
            await session.flush()

        except IntegrityError:
            await session.rollback()
            raise

        await session.commit()
        await session.refresh(user_profile)

        user_account = UserAccounts(
            user_profile_id=user_profile.id,
            team_id=schema.TeamGroup.id,
            username=schema.UserAccount.username,
            password=hashpw(schema.UserAccount.password.encode("utf-8"), gensalt()).decode("utf-8"),
        )

        session.add(user_account)
        try:
            await session.flush()

        except IntegrityError:
            await session.rollback()
            raise

        await session.commit()
        await session.refresh(user_account)

        return {
            "userProfileId": user_account.user_profile_id,
            "teamGroupId": user_account.team_id,
            "username": user_account.username,
        }

    except Exception as exception:  # pylint: disable=broad-except
        await session.rollback()
        logger.error(msg=exception)
        return False




async def insert_user_role(
    session: AsyncSession,
    value: str | None = None,
    description: str | None = None,
    payload=None,
) -> dict | bool:
    try:
        if payload is not None:
            value = getattr(payload, "value", value)
            description = getattr(payload, "description", description)

        if value is None:
            raise ValueError("User role value is required")

        user_role = UserRoles(
            id=generate_uuid_v4(),
            value=value,
            description=description,
        )

        session.add(user_role)
        await session.commit()
        await session.refresh(user_role)

        return {
            "id": user_role.id,
            "value": user_role.value,
            "description": user_role.description,
        }
    except Exception as exception:  # pylint: disable=broad-except
        await session.rollback()
        logger.error(msg=exception)
        return False
'''
