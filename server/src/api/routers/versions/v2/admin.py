from fastapi import (
    APIRouter,
    Request,
    Depends
)
from fastapi.encoders import jsonable_encoder

from src.core.database.queries.select import select_all_teams
from src.core.schemas.sign_up_request import *
from src.api.responses import response
from src.utils.controls import MEDIA_TYPE
from src.core.database.session import database
from src.utils.logger import logger

from starlette.status import *

from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

router = APIRouter()


from src.core.database.queries.insert import insert_user_account


@router.post(path='/create/users')
async def create_users(session: AsyncSession = Depends(database)):
    for team in await select_all_teams(session=session):
        if team.description == 'Soporte':
            support_group_id = team.id

        elif team.description == 'Asesoría':
            audit_group_id = team.id

    # asesoria
    __ = await insert_user_account(
        session=session,
        schema=SignUpRequest(
            UserProfile=UserProfile(
                full_name='mariel andrea pineda soto',
                email='mpineda@consejodeauditoria.gob.cl',
                is_active=True),
            UserAccount=UserAccount(
                username='mpineda',
                password='12345678'),
            TeamGroup=TeamGroup(id=audit_group_id)
        )
    )

    #__ = await insert_user_account(
    #    session=session,
    #    schema=SignUpRequest(
    #        UserProfile=UserProfile(
    #            full_name='liliana leonor vivanco riquelme',
    #            email='lvivanco@consejodeauditoria.gob.cl',
    #            is_active=True),
    #        UserAccount=UserAccount(
    #            username='lvivanco',
    #            password='12345678'),
    #        TeamGroup=TeamGroup(id=audit_group_id)
    #    )
    #)

    #__ = await insert_user_account(
    #    session=session,
    #    schema=SignUpRequest(
    #        UserProfile=UserProfile(
    #            full_name='coco riquelme',
    #            email='criquelme@consejodeauditoria.gob.cl',
    #            is_active=True),
    #        UserAccount=UserAccount(
    #            username='criquelme',
    #            password='12345678'),
    #        TeamGroup=TeamGroup(id=audit_group_id)
    #    )
    #)


    #__ = await insert_user_account(
    #    session=session,
    #    schema=SignUpRequest(
    #        UserProfile=UserProfile(
    #            full_name='javiera ignacia riquelme gutierrez',
    #            email='jriquelme@consejodeauditoria.gob.cl',
    #            is_active=True),
    #        UserAccount=UserAccount(
    #            username='jriquelme',
    #            password='12345678'),
    #        TeamGroup=TeamGroup(id=audit_group_id)
    #    )
    #)



    # soporte
    __ = await insert_user_account(
        session=session,
        schema=SignUpRequest(
            UserProfile=UserProfile(
                full_name='daniel robinson santelices candia',
                email='dsantelices@consejodeauditoria.gob.cl',
                is_active=True),
            UserAccount=UserAccount(
                username='dsantelices',
                password='12345678'),
            TeamGroup=TeamGroup(id=support_group_id)
        )
    )

    __ = await insert_user_account(
        session=session,
        schema=SignUpRequest(
            UserProfile=UserProfile(
                full_name='luis osorio rubilar',
                email='losorio@consejodeauditoria.gob.cl',
                is_active=True),
            UserAccount=UserAccount(
                username='losorio',
                password='12345678'),
            TeamGroup=TeamGroup(id=support_group_id)
        )
    )

    #__ = await insert_user_account(
    #    session=session,
    #    schema=SignUpRequest(
    #        UserProfile=UserProfile(
    #            full_name='blues antonio riquelme',
    #            email='briquelme@consejodeauditoria.gob.cl',
    #            is_active=True),
    #        UserAccount=UserAccount(
    #            username='briquelme',
    #            password='12345678'),
    #        TeamGroup=TeamGroup(id=support_group_id)
    #    )
    #)

    __ = await insert_user_account(
        session=session,
        schema=SignUpRequest(
            UserProfile=UserProfile(
                full_name='gonzalo mauricio vivanco zepeda',
                email='gvivanco@consejodeauditoria.gob.cl',
                is_active=True),
            UserAccount=UserAccount(
                username='gvivanco',
                password='12345678'),
            TeamGroup=TeamGroup(id=support_group_id)
        )
    )

