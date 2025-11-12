from starlette.status import HTTP_200_OK, HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN, HTTP_500_INTERNAL_SERVER_ERROR

from typing import Annotated

from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import (
    APIRouter,
    Request,
    Response,
    Depends,
    HTTPException,
    security
)




router = APIRouter()
authentication_schema = security.HTTPBearer()


from src.api.responses import response
from src.core.database.queries.insert import insert_user_account
from src.utils.controls import MEDIA_TYPE
from src.core.database.session import database
from src.utils.logger import logger

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from starlette.status import *
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from src.core.database.session import database
from src.core.database.queries.select import (
    validate_user_authentication,
    select_user_by_username,
    select_user_full_name_by_user_account_id,
    select_user_role_name_by_user_role_id,
    select_user_presence_by_user_account_id
)
from src.core.database.queries.alter import update_last_login_date, update_user_online_status

from src.core.schemas.sign_in_request import (SignInRequest, SignUpRequest)

from src.core.security.tokens import (
    JWTBearer,
    create_access_token,
    verify_access_token
)
from src.core.security.presence import touch_presence

router = APIRouter()


@router.post(
    path='/sign-in',
    status_code=HTTP_200_OK,
    tags=['Authentication'],
    summary='Iniciar sesión de usuario',
    description='Autentica a un usuario registrado y retorna un token de acceso JWT.',
    response_description='Token de acceso generado exitosamente.'
)
async def sign_in(
    payload: SignInRequest,
    request: Request,
    session: Annotated[AsyncSession, Depends(database)]
):
    logger.info(msg=f'{request.client.host}:{request.client.port}')

    try:
        authentication = await validate_user_authentication(session=session, username=payload.username, password=payload.password)
        if not authentication:
            return response(
                response_type=2,
                status_code=HTTP_401_UNAUTHORIZED,
                media_type=MEDIA_TYPE,
                content={'message': 'Invalid credentials'}
            )

        user_account_id = authentication.id
        user_role_id = authentication.user_role_id
        user_full_name = await select_user_full_name_by_user_account_id(session=session, user_account_id=user_account_id)
        user_role_name = await select_user_role_name_by_user_role_id(session=session, user_role_id=user_role_id)

        user_access_token = create_access_token(
            credential={
                'userAccountID': str(user_account_id),
                'userRoleID': str(user_role_id),
                'username': str(authentication.username),
            }
        )

        await update_last_login_date(session=session, user_account_id=authentication.id)
        await update_user_online_status(session=session, user_account_id=authentication.id, is_online=True)

        content = jsonable_encoder(obj={
            'client'            : request.client.host,
            'userAccessToken'   : user_access_token,
            'userAccountID'     : user_account_id,
            'userFullName'      : user_full_name,
            'userRoleName'      : user_role_name,
            'isOnline'          : True,
        })

        return response(
            response_type=2,
            status_code=HTTP_200_OK,
            media_type=MEDIA_TYPE,
            content=content
        )

    except Exception as exception:
        logger.exception(msg=f'{request.client.host}:{request.client.port}: {exception}')

        return response(
            response_type=2,
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            media_type=MEDIA_TYPE,
            content={'message': 'Internal Server Error'}
        )



@router.post(
    path='/sign-up',
    status_code=HTTP_201_CREATED,
    tags=['Authentication'],
    description=(
        ''
    ),
    summary='',
)
async def sign_up(request: Request, payload: SignUpRequest, session: AsyncSession = Depends(database)):
    try:
        query_value = await select_user_by_username(session=session, username=payload.UserAccount.username)
        if query_value:
            return response(
                response_type=2,
                status_code=HTTP_400_BAD_REQUEST,
                media_type=MEDIA_TYPE,
                content={'message': 'Try with another username.'}
            )

        content = jsonable_encoder(
            obj=await insert_user_account(session=session, schema=payload)
        )

        return response(
            response_type=2,
            status_code=HTTP_201_CREATED if content else HTTP_422_UNPROCESSABLE_ENTITY,
            media_type=MEDIA_TYPE,
            content={'status': 'success', 'data' : content} if content else {'status': 'error', 'data' : None}
        )
    except Exception as exception:
        logger.exception(msg=f'{request.client.host}:{request.client.port}: {exception}')

        return response(
            response_type=2,
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            media_type=MEDIA_TYPE,
            content={'message': 'Internal Server Error'}
        )


@router.post(
    path='/verify/session',
    tags=['Authentication'],
    dependencies=[Depends(JWTBearer()), Depends(touch_presence)]
)
async def verify_session(Authorization: str, request: Request, session: AsyncSession = Depends(database)):
    try:
        decoded_token = verify_access_token(token=Authorization, output=True)

        user_account_id = UUID(decoded_token['userAccountID'])
        user_role_id = UUID(decoded_token['userRoleID'])

        user_full_name = await select_user_full_name_by_user_account_id(session=session, user_account_id=user_account_id)
        user_role_name = await select_user_role_name_by_user_role_id(session=session, user_role_id=user_role_id)

        presence = await select_user_presence_by_user_account_id(session=session, user_account_id=user_account_id)

        content = jsonable_encoder(obj={
            'client'            : request.client.host,
            'userAccessToken'   : Authorization,
            'userAccountID'     : user_account_id,
            'userFullName'      : user_full_name,
            'userRoleName'      : user_role_name,
            'isOnline'          : bool(getattr(presence, 'is_online', False)),
            'lastSeen'          : getattr(presence, 'last_seen', None),
        })

        return response(
            response_type=2,
            status_code=HTTP_200_OK,
            media_type=MEDIA_TYPE,
            content=content
        )
    except Exception as exception:
        logger.exception(msg=f'{request.client.host}:{request.client.port}: {exception}')

        return response(
            response_type=2,
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            media_type=MEDIA_TYPE,
            content={'message': 'Internal Server Error'}
        )

    except Exception as exception:
        logger.exception(msg=f'{request.client.host}:{request.client.port}: {exception}')

        return response(
            response_type=2,
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            media_type=MEDIA_TYPE,
            content={'message': 'Internal Server Error'}
        )


@router.post(
    path='/sign-out',
    status_code=HTTP_200_OK,
    tags=['Authentication'],
    dependencies=[Depends(JWTBearer())],
    summary='Cerrar sesión de usuario',
    description='Marca al usuario como offline y finaliza su sesión lógica.'
)
async def sign_out(Authorization: str, request: Request, session: AsyncSession = Depends(database)):
    try:
        decoded_token = verify_access_token(token=Authorization, output=True)
        user_account_id = UUID(decoded_token['userAccountID'])

        await update_user_online_status(session=session, user_account_id=user_account_id, is_online=False)

        content = jsonable_encoder(obj={
            'client'        : request.client.host,
            'userAccountID' : user_account_id,
            'isOnline'      : False
        })

        return response(
            response_type=2,
            status_code=HTTP_200_OK,
            media_type=MEDIA_TYPE,
            content=content
        )

    except Exception as exception:
        logger.exception(msg=f'{request.client.host}:{request.client.port}: {exception}')

        return response(
            response_type=2,
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            media_type=MEDIA_TYPE,
            content={'message': 'Internal Server Error'}
        )

    except Exception as exception:
        logger.exception(msg=f'{request.client.host}:{request.client.port}: {exception}')

        return response(
            response_type=2,
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            media_type=MEDIA_TYPE,
            content={'message': 'Internal Server Error'}
        )
