from fastapi import (
    APIRouter,
    Request,
    Depends,
    security
)
from fastapi.encoders import jsonable_encoder

from src.api.responses import response
from src.utils.controls import MEDIA_TYPE
from src.core.schemas.sign_in_request import SignInRequest
from src.core.schemas.sign_up_request import SignUpRequest
from src.core.database.session import database
from src.core.database.queries.select import (
    validate_user_authentication,
    select_user_by_username,
    select_user_full_name_by_user_account_id,
    select_team_by_user_account_id,
    select_user_by_user_account_id,
)
from src.core.database.queries.insert import insert_user_account
from src.core.database.queries.alter import update_last_login_date
from src.core.security.tokens import (
    JWTBearer,
    create_access_token,
    verify_access_token,
    revoke_access_token,
)

from src.utils.logger import logger

from uuid import UUID
from starlette.status import *

from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

router = APIRouter()
authentication_schema = security.HTTPBearer()


@router.post(path='/sign-in')
async def sign_in(
    payload: SignInRequest,
    request: Request,
    session: Annotated[AsyncSession, Depends(database)]
):
    authentication = await validate_user_authentication(
        session=session,
        username=payload.username,
        password=payload.password,
    )
    if not authentication:
        return response(
            response_type=2,
            status_code=HTTP_401_UNAUTHORIZED,
            media_type=MEDIA_TYPE,
            content={'message': 'Invalid credentials'}
        )

    user_account_id = authentication.id
    team_id = authentication.team_id
    
    team = await select_team_by_user_account_id(
        session=session,
        user_account_id=user_account_id,
    )
    
    user_full_name = await select_user_full_name_by_user_account_id(
        session=session,
        user_account_id=user_account_id,
    )
    user_access_token = await create_access_token(
        credential={
            'userAccountId': str(user_account_id),
            'teamId': str(team_id),
            'teamName': str(team.description)
        }
    )

    await update_last_login_date(session=session, user_account_id=authentication.id)

    content = jsonable_encoder(
        obj={
            'client' : request.client.host,
            'accessToken' : user_access_token,
            'username': str(authentication.username),
            'userFullName' : str(user_full_name),
            'team': str(team.description)
        }
    )

    return response(
        response_type=2,
        status_code=HTTP_200_OK,
        media_type=MEDIA_TYPE,
        content=content
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
        object_model = await select_user_by_username(
            session=session,
            username=payload.UserAccount.username,
        )
        if object_model:
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
)
async def verify_session(
    token: Annotated[str, Depends(JWTBearer())],
    request: Request,
    session: Annotated[AsyncSession, Depends(database)],
):
    try:
        decoded_token = verify_access_token(token=token, output=True)

        user_account_id = UUID(decoded_token['userAccountId'])

        user_account = await select_user_by_user_account_id(
            session=session,
            user_account_id=user_account_id,
        )
        if not user_account:
            return response(
                response_type=2,
                status_code=HTTP_401_UNAUTHORIZED,
                media_type=MEDIA_TYPE,
                content={'message': 'Invalid credentials'}
            )

        team = await select_team_by_user_account_id(
            session=session,
            user_account_id=user_account_id,
        )

        user_full_name = await select_user_full_name_by_user_account_id(
            session=session,
            user_account_id=user_account_id,
        )

        content = jsonable_encoder(obj={
            'client': request.client.host,
            'accessToken': token,
            'username': str(user_account.username),
            'userFullName': str(user_full_name) if user_full_name else None,
            'team': str(team.description) if team else None
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
    path='/refresh-token',
    tags=['Authentication'],
)
async def refresh_token(
    token: Annotated[str, Depends(JWTBearer())],
    request: Request,
):
    try:
        decoded_token = verify_access_token(token=token, output=True)

        refreshed_access_token = await create_access_token(
            credential={
                'userAccountId': decoded_token['userAccountId'],
                'teamId': decoded_token['teamId'],
            }
        )

        content = jsonable_encoder(obj={
            'client': request.client.host,
            'accessToken': refreshed_access_token
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
    path='/sign-out',
    tags=['Authentication'],
)
async def sign_out(
    token: Annotated[str, Depends(JWTBearer())],
    request: Request,
):
    try:
        decoded_token = verify_access_token(token=token, output=True)
        revoke_access_token(token=token)

        content = jsonable_encoder(obj={
            'client': request.client.host,
            'userAccountId': decoded_token['userAccountId'],
            'teamId': decoded_token['teamId'],
            'message': 'Session closed successfully.'
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
