from fastapi import (
    APIRouter,
    Request,
    Depends
)
from fastapi.encoders import jsonable_encoder

from src.core.database.session import database
from src.utils.logger import logger

from starlette.status import *

from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

router = APIRouter()


from src.core.schemas.sign_in_request import CreateUserRole
from src.core.database.queries.select import (select_all_user_roles, select_all_user_acounts)
from src.core.database.queries.insert import insert_user_role

from src.utils.controls import MEDIA_TYPE


from src.api.responses import response

@router.post(path='/create/user-role')
async def post_user_role(payload: CreateUserRole, request: Request, session: Annotated[AsyncSession, Depends(database)]):

    logger.info(msg=f'{request.client.host}:{request.client.port}')

    try:
        object_model = jsonable_encoder(obj=await insert_user_role(session=session, payload=payload))

        return response(
            response_type=2,
            status_code=HTTP_200_OK,
            media_type=MEDIA_TYPE,
            content={'status': 'success', 'data': object_model}
        ) if object_model else response(
            response_type=2,
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            media_type=MEDIA_TYPE,
            content={'status': 'error'}
        )
    except Exception as exception:
        logger.exception(msg=f'{request.client.host}:{request.client.port}: {exception}')

        return response(
            response_type=2,
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            media_type=MEDIA_TYPE,
            content={'message': 'Internal Server Error'}
        )




@router.get(path='/select/user-roles')
async def get_user_roles(request: Request, session: Annotated[AsyncSession, Depends(database)]):
    logger.info(msg=f'{request.client.host}:{request.client.port}')
    try:
        data = jsonable_encoder(await select_all_user_roles(session=session))

        return response(
            response_type=2,
            status_code=HTTP_200_OK,
            media_type=MEDIA_TYPE,
            content={'status': 'success', 'data': data}
        ) if data else response(
            response_type=2,
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            media_type=MEDIA_TYPE,
            content={'status': 'error'}
        )

    except Exception as exception:
        logger.exception(msg=f'{request.client.host}:{request.client.port}: {exception}')

        return response(
            response_type=2,
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            media_type=MEDIA_TYPE,
            content={'message': 'Internal Server Error'}
        )

@router.get(path='/select/users')
async def get_user_accounts(request: Request, session: Annotated[AsyncSession, Depends(database)]):
    logger.info(msg=f'{request.client.host}:{request.client.port}')
    try:
        data = jsonable_encoder(await select_all_user_acounts(session=session))

        return response(
            response_type=2,
            status_code=HTTP_200_OK,
            media_type=MEDIA_TYPE,
            content={'status': 'success', 'data': data}
        ) if data else response(
            response_type=2,
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            media_type=MEDIA_TYPE,
            content={'status': 'error'}
        )

    except Exception as exception:
        logger.exception(msg=f'{request.client.host}:{request.client.port}: {exception}')

        return response(
            response_type=2,
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            media_type=MEDIA_TYPE,
            content={'message': 'Internal Server Error'}
        )
