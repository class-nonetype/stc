from fastapi import (
    APIRouter,
    Response,
    HTTPException,
    Request,
    UploadFile,
    File,
    Depends
)
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from pathlib import Path
from typing import (Optional, Annotated)
from starlette.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_413_REQUEST_ENTITY_TOO_LARGE,
    HTTP_415_UNSUPPORTED_MEDIA_TYPE,
    HTTP_422_UNPROCESSABLE_ENTITY,
    HTTP_500_INTERNAL_SERVER_ERROR)
from sqlalchemy.orm import Session


from src.utils.controls import MEDIA_TYPE
from src.core.security.tokens import JWTBearer, verify_access_token
from src.core.database.queries.select import (
    select_uploaded_files,
    select_uploaded_file_by_id,
    select_uploaded_files_by_user_account_id
)
from src.core.schemas.sign_in_request import FileToUpload
from src.core.database.session import database
from src.core.database.queries.insert import insert_upload_file
from src.utils import (
    UUID,
    logger,
    generate_uuid_v4,
    UPLOADS_DIRECTORY_PATH,
    PROFILE_PHOTOS_DIRECTORY_PATH,
    ALLOWED_FILE_EXTENSIONS, MAX_FILE_SIZE,
    API_PREFIX
)


from src.api.responses import response

router = APIRouter()

@router.post(
    path='/upload',
    tags=['Upload'],
    dependencies=[Depends(JWTBearer())]
)
async def post_upload_file(request: Request,
                           session: Annotated[Session, Depends(database)],
                           media_file: Optional[UploadFile] = File(...)):
    logger.info(f'{request.client.host}:{request.client.port}')

    if media_file:
        file_extension = media_file.filename.split('.')[-1]
        if not file_extension.lower() in ALLOWED_FILE_EXTENSIONS:
            return response(
                response_type=2,
                status_code=HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                media_type=MEDIA_TYPE,
                content={'message': f'Unsupported file type: {file_extension}.'}
            )

        try:
            file_uuid_name = '{0}'.format(generate_uuid_v4())
            file_name = '{0}.{1}'.format(file_uuid_name, file_extension)
            file_path = Path(UPLOADS_DIRECTORY_PATH, file_name)
            file_url = API_PREFIX['static'] + '/' + file_name

            with open(file=file_path, mode='wb') as file:
                file_content = await media_file.read()
                file.write(file_content)
                file_size = len(file_content)
                if file_size > MAX_FILE_SIZE:
                    return response(
                        response_type=2,
                        status_code=HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        media_type=MEDIA_TYPE,
                        content={'message': f"File too large. Max size allowed is {MAX_FILE_SIZE / (1024 * 1024)}mb"}
                    )

            content = jsonable_encoder(obj=insert_upload_file(
                session=session,
                payload=FileToUpload(
                    # Nota: el endpoint de carga genérico asigna un usuario aleatorio.
                    # Para cargas de perfil use el endpoint dedicado más abajo.
                    user_account_id=generate_uuid_v4(),
                    file_path=file_path,
                    file_url=file_url,
                    file_size=file_size,
                    file_name=media_file.filename,
                    file_uuid_name=file_uuid_name
                )
            ))

            return response(
                response_type=2,
                status_code=HTTP_201_CREATED if content else HTTP_422_UNPROCESSABLE_ENTITY,
                media_type=MEDIA_TYPE,
                content={'status': 'success', 'data': content} if content else {'status': 'error', 'data': None}
            )

        except Exception as exception:
            logger.exception(msg=f'{request.client.host}:{request.client.port}: {exception}')

            return response(
                response_type=2,
                status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                media_type=MEDIA_TYPE,
                content={'message': 'Internal Server Error'}
            )




@router.get(
    path='/uploads/{user_account_id}',
    tags=['Upload'],
    dependencies=[Depends(JWTBearer())]
)
async def get_upload_files_by_user_account_id(user_account_id: UUID, request: Request, session: Annotated[Session, Depends(database)]):
    logger.info(f'{request.client.host}:{request.client.port}')

    try:
        content = jsonable_encoder(obj=select_uploaded_files_by_user_account_id(session=session, user_account_id=user_account_id))

        return response(
            response_type=2,
            status_code=HTTP_200_OK if content else HTTP_404_NOT_FOUND,
            media_type=MEDIA_TYPE,
            content={'status': 'success', 'content': content} if content else {'status': 'error', 'data': None}
        )

    except Exception as exception:
        logger.exception(msg=f'{request.client.host}:{request.client.port}: {exception}')

        return response(
            response_type=2,
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            media_type=MEDIA_TYPE,
            content={'message': 'Internal Server Error'}
        )


@router.get(
    path='/uploads/{uploaded_file_id}',
    tags=['Upload'],
    dependencies=[Depends(JWTBearer())]
)
async def get_upload_file_by_id(uploaded_file_id: UUID, request: Request, session: Annotated[Session, Depends(database)]):
    logger.info(f'{request.client.host}:{request.client.port}')

    try:
        content = jsonable_encoder(obj=select_uploaded_file_by_id(session=session, uploaded_file_id=uploaded_file_id))
        return response(
            response_type=2,
            status_code=HTTP_200_OK if content else HTTP_404_NOT_FOUND,
            media_type=MEDIA_TYPE,
            content={'status': 'success', 'content': content} if content else {'status': 'error', 'data': None}
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
    path='/upload/profile-photo',
    tags=['Upload'],
    dependencies=[Depends(JWTBearer())]
)
async def post_profile_photo(
    request: Request,
    session: Annotated[Session, Depends(database)],
    media_file: Optional[UploadFile] = File(...)
):
    """Sube una foto de perfil al directorio específico del usuario.

    - Directorio: /static/uploads/profile_photos/{user_id}/
    - URL pública: {API_PREFIX['static']}/profile_photos/{user_id}/{file}
    """
    logger.info(f"{request.client.host}:{request.client.port}")

    if media_file is None:
        return response(
            response_type=2,
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            media_type=MEDIA_TYPE,
            content={'message': 'media_file is required'}
        )

    file_extension = media_file.filename.split('.')[-1]
    if not file_extension.lower() in ('png', 'jpg', 'jpeg'):
        return response(
            response_type=2,
            status_code=HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            media_type=MEDIA_TYPE,
            content={'message': f'Unsupported image type: {file_extension}.'}
        )

    try:
        token = request.headers.get('Authorization')
        if token and token.lower().startswith('bearer '):
            token = token[7:]
        payload = verify_access_token(token=token, output=True)
        user_id = UUID(payload['userAccountID'])

        # Construye el directorio específico por usuario y guarda el archivo
        user_dir = PROFILE_PHOTOS_DIRECTORY_PATH / str(user_id)
        if not user_dir.exists():
            user_dir.mkdir(parents=True, exist_ok=True)

        file_uuid_name = f"{generate_uuid_v4()}"
        file_name = f"{file_uuid_name}.{file_extension}"
        file_path = user_dir / file_name
        file_url = f"{API_PREFIX['static']}/profile_photos/{user_id}/{file_name}"

        with open(file=file_path, mode='wb') as file:
            file_content = await media_file.read()
            file.write(file_content)
            file_size = len(file_content)
            if file_size > MAX_FILE_SIZE:
                return response(
                    response_type=2,
                    status_code=HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    media_type=MEDIA_TYPE,
                    content={'message': f"File too large. Max size allowed is {MAX_FILE_SIZE / (1024 * 1024)}mb"}
                )

        content = jsonable_encoder(obj=insert_upload_file(
            session=session,
            payload=FileToUpload(
                user_account_id=user_id,
                file_path=file_path,
                file_url=file_url,
                file_size=file_size,
                file_name=media_file.filename,
                file_uuid_name=file_uuid_name
            )
        ))

        return response(
            response_type=2,
            status_code=HTTP_201_CREATED,
            media_type=MEDIA_TYPE,
            content={'status': 'success', 'data': content}
        )

    except HTTPException as exception:
        raise exception
    except Exception as exception:
        logger.exception(msg=f"{request.client.host}:{request.client.port}: {exception}")
        return response(
            response_type=2,
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            media_type=MEDIA_TYPE,
            content={'message': 'Internal Server Error'}
        )


@router.get(
    path='/uploads',
    tags=['Upload'],
    dependencies=[Depends(JWTBearer())]
)
async def get_upload_files(request: Request, session: Annotated[Session, Depends(database)]):
    logger.info(f'{request.client.host}:{request.client.port}')

    try:
        content = jsonable_encoder(obj=select_uploaded_files(session=session))

        return response(
            response_type=2,
            status_code=HTTP_200_OK if content else HTTP_404_NOT_FOUND,
            media_type=MEDIA_TYPE,
            content={'status': 'success', 'content': content} if content else {'status': 'error', 'data': None}
        )

    except Exception as exception:
        logger.exception(msg=f'{request.client.host}:{request.client.port}: {exception}')

        return response(
            response_type=2,
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            media_type=MEDIA_TYPE,
            content={'message': 'Internal Server Error'}
        )
