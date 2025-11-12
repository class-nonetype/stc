from typing import Annotated
from uuid import UUID as _UUID

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from starlette.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_500_INTERNAL_SERVER_ERROR,
)

from src.api.responses import response
from src.core.database.session import database
from src.core.schemas.social import (
    PostCreateRequest,
    PostUpdateRequest,
    PostResponse,
    PostAttachmentResponse,
    PostsListResponse,
)
from src.core.security.tokens import JWTBearer, verify_access_token
from src.core.services.social import (
    NotAllowed,
    PostNotFound,
    create_post,
    update_post,
    delete_post,
    like_post,
    unlike_post,
    follow_user,
    unfollow_user,
    get_post_by_id,
    list_posts,
)
from src.utils.controls import MEDIA_TYPE
from src.utils.logger import logger


router = APIRouter()
jwt_bearer = JWTBearer()


def _user_id_from_request_token(token: str) -> _UUID:
    payload = verify_access_token(token=token, output=True)
    return _UUID(payload['userAccountID'])


def _build_post_response(post) -> PostResponse:
    attachments = []
    for attachment in getattr(post, 'attachments', []) or []:
        upload = getattr(attachment, 'upload', None)
        attachments.append(
            PostAttachmentResponse(
                upload_id=attachment.upload_id,
                file_url=getattr(upload, 'file_url', None),
                file_name=getattr(upload, 'file_name', None),
                file_size=getattr(upload, 'file_size', None),
                file_uuid_name=getattr(upload, 'file_uuid_name', None),
            )
        )
    return PostResponse(
        id=post.id,
        author_id=post.author_id,
        content=post.content,
        created_at=post.created_at,
        updated_at=post.updated_at,
        deleted=post.deleted,
        attachments=attachments,
    )


@router.get(path='/posts')
async def get_posts(
    request: Request,
    session: Annotated[Session, Depends(database)],
    author_id: _UUID | None = None,
    limit: int = 20,
    offset: int = 0,
):
    """Lista publicaciones. Puede filtrar por `author_id`."""
    logger.info(msg=f"{request.client.host}:{request.client.port}")
    try:
        posts = list_posts(session=session, author_id=author_id, limit=limit, offset=offset)
        payload = [_build_post_response(post) for post in posts]
        content = PostsListResponse(posts=payload)
        return response(
            response_type=2,
            status_code=HTTP_200_OK,
            media_type=MEDIA_TYPE,
            content={'status': 'success', 'data': content.model_dump(mode='json')},
        )
    except Exception as exception:
        logger.exception(msg=f"{request.client.host}:{request.client.port}: {exception}")
        return response(
            response_type=2,
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            media_type=MEDIA_TYPE,
            content={'message': 'Internal Server Error'},
        )


@router.get(path='/posts/{post_id}')
async def get_post(
    post_id: _UUID,
    request: Request,
    session: Annotated[Session, Depends(database)],
):
    """Obtiene una publicación por ID."""
    logger.info(msg=f"{request.client.host}:{request.client.port}")
    try:
        post = get_post_by_id(session=session, post_id=post_id)
        if post is None:
            return response(
                response_type=2,
                status_code=HTTP_404_NOT_FOUND,
                media_type=MEDIA_TYPE,
                content={'status': 'error', 'message': 'Post not found'},
            )
        data = _build_post_response(post).model_dump(mode='json')
        return response(
            response_type=2,
            status_code=HTTP_200_OK,
            media_type=MEDIA_TYPE,
            content={'status': 'success', 'data': data},
        )
    except Exception as exception:
        logger.exception(msg=f"{request.client.host}:{request.client.port}: {exception}")
        return response(
            response_type=2,
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            media_type=MEDIA_TYPE,
            content={'message': 'Internal Server Error'},
        )


@router.post(path='/posts')
async def post_post(
    payload: PostCreateRequest,
    request: Request,
    session: Annotated[Session, Depends(database)],
    token: Annotated[str, Depends(jwt_bearer)],
):
    """Crea una publicación (puede incluir IDs de archivos previamente subidos)."""
    logger.info(msg=f"{request.client.host}:{request.client.port}")
    try:
        user_id = _user_id_from_request_token(token)
        post = create_post(
            session=session,
            author_id=user_id,
            content=payload.content,
            attachment_ids=payload.attachment_ids,
        )
        data = _build_post_response(post).model_dump(mode='json')
        return response(
            response_type=2,
            status_code=HTTP_201_CREATED,
            media_type=MEDIA_TYPE,
            content={'status': 'success', 'data': data},
        )
    except Exception as exception:
        logger.exception(msg=f"{request.client.host}:{request.client.port}: {exception}")
        return response(
            response_type=2,
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            media_type=MEDIA_TYPE,
            content={'message': 'Internal Server Error'},
        )


@router.patch(path='/posts/{post_id}')
async def patch_post(
    post_id: _UUID,
    payload: PostUpdateRequest,
    request: Request,
    session: Annotated[Session, Depends(database)],
    token: Annotated[str, Depends(jwt_bearer)],
):
    """Modifica el contenido y/o adjuntos de una publicación (solo autor)."""
    logger.info(msg=f"{request.client.host}:{request.client.port}")
    try:
        user_id = _user_id_from_request_token(token)
        post = update_post(
            session=session,
            post_id=post_id,
            requester_id=user_id,
            content=payload.content,
            attachment_ids=payload.attachment_ids,
        )
        data = _build_post_response(post).model_dump(mode='json')
        return response(
            response_type=2,
            status_code=HTTP_200_OK,
            media_type=MEDIA_TYPE,
            content={'status': 'success', 'data': data},
        )
    except PostNotFound:
        return response(
            response_type=2,
            status_code=HTTP_404_NOT_FOUND,
            media_type=MEDIA_TYPE,
            content={'status': 'error', 'message': 'Post not found'},
        )
    except NotAllowed as exception:
        return response(
            response_type=2,
            status_code=HTTP_400_BAD_REQUEST,
            media_type=MEDIA_TYPE,
            content={'status': 'error', 'message': str(exception)},
        )
    except Exception as exception:
        logger.exception(msg=f"{request.client.host}:{request.client.port}: {exception}")
        return response(
            response_type=2,
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            media_type=MEDIA_TYPE,
            content={'message': 'Internal Server Error'},
        )


@router.delete(path='/posts/{post_id}')
async def delete_post_endpoint(
    post_id: _UUID,
    request: Request,
    session: Annotated[Session, Depends(database)],
    token: Annotated[str, Depends(jwt_bearer)],
):
    """Elimina (soft delete) una publicación (solo autor)."""
    logger.info(msg=f"{request.client.host}:{request.client.port}")
    try:
        user_id = _user_id_from_request_token(token)
        post = delete_post(session=session, post_id=post_id, requester_id=user_id)
        data = _build_post_response(post).model_dump(mode='json')
        return response(
            response_type=2,
            status_code=HTTP_200_OK,
            media_type=MEDIA_TYPE,
            content={'status': 'success', 'data': data},
        )
    except PostNotFound:
        return response(
            response_type=2,
            status_code=HTTP_404_NOT_FOUND,
            media_type=MEDIA_TYPE,
            content={'status': 'error', 'message': 'Post not found'},
        )
    except NotAllowed as exception:
        return response(
            response_type=2,
            status_code=HTTP_400_BAD_REQUEST,
            media_type=MEDIA_TYPE,
            content={'status': 'error', 'message': str(exception)},
        )
    except Exception as exception:
        logger.exception(msg=f"{request.client.host}:{request.client.port}: {exception}")
        return response(
            response_type=2,
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            media_type=MEDIA_TYPE,
            content={'message': 'Internal Server Error'},
        )


@router.post(path='/posts/{post_id}/like')
async def post_like_post(
    post_id: _UUID,
    request: Request,
    session: Annotated[Session, Depends(database)],
    token: Annotated[str, Depends(jwt_bearer)],
):
    """Da like a una publicación (idempotente)."""
    logger.info(msg=f"{request.client.host}:{request.client.port}")
    try:
        user_id = _user_id_from_request_token(token)
        like = like_post(session=session, post_id=post_id, user_id=user_id)
        return response(
            response_type=2,
            status_code=HTTP_201_CREATED,
            media_type=MEDIA_TYPE,
            content={'status': 'success', 'data': {'id': str(like.id)}},
        )
    except PostNotFound:
        return response(
            response_type=2,
            status_code=HTTP_404_NOT_FOUND,
            media_type=MEDIA_TYPE,
            content={'status': 'error', 'message': 'Post not found'},
        )
    except Exception as exception:
        logger.exception(msg=f"{request.client.host}:{request.client.port}: {exception}")
        return response(
            response_type=2,
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            media_type=MEDIA_TYPE,
            content={'message': 'Internal Server Error'},
        )


@router.delete(path='/posts/{post_id}/like')
async def delete_like_post(
    post_id: _UUID,
    request: Request,
    session: Annotated[Session, Depends(database)],
    token: Annotated[str, Depends(jwt_bearer)],
):
    """Quita el like de una publicación (idempotente)."""
    logger.info(msg=f"{request.client.host}:{request.client.port}")
    try:
        user_id = _user_id_from_request_token(token)
        unlike_post(session=session, post_id=post_id, user_id=user_id)
        return response(
            response_type=2,
            status_code=HTTP_200_OK,
            media_type=MEDIA_TYPE,
            content={'status': 'success', 'data': {'unliked': True}},
        )
    except Exception as exception:
        logger.exception(msg=f"{request.client.host}:{request.client.port}: {exception}")
        return response(
            response_type=2,
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            media_type=MEDIA_TYPE,
            content={'message': 'Internal Server Error'},
        )


@router.post(path='/users/{user_id}/follow')
async def post_follow_user(
    user_id: _UUID,
    request: Request,
    session: Annotated[Session, Depends(database)],
    token: Annotated[str, Depends(jwt_bearer)],
):
    """Sigue a un usuario (idempotente)."""
    logger.info(msg=f"{request.client.host}:{request.client.port}")
    try:
        follower_id = _user_id_from_request_token(token)
        follow = follow_user(session=session, follower_id=follower_id, followee_id=user_id)
        return response(
            response_type=2,
            status_code=HTTP_201_CREATED,
            media_type=MEDIA_TYPE,
            content={'status': 'success', 'data': {'id': str(follow.id)}},
        )
    except NotAllowed as exception:
        return response(
            response_type=2,
            status_code=HTTP_400_BAD_REQUEST,
            media_type=MEDIA_TYPE,
            content={'status': 'error', 'message': str(exception)},
        )
    except Exception as exception:
        logger.exception(msg=f"{request.client.host}:{request.client.port}: {exception}")
        return response(
            response_type=2,
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            media_type=MEDIA_TYPE,
            content={'message': 'Internal Server Error'},
        )


@router.delete(path='/users/{user_id}/follow')
async def delete_follow_user(
    user_id: _UUID,
    request: Request,
    session: Annotated[Session, Depends(database)],
    token: Annotated[str, Depends(jwt_bearer)],
):
    """Deja de seguir a un usuario (idempotente)."""
    logger.info(msg=f"{request.client.host}:{request.client.port}")
    try:
        follower_id = _user_id_from_request_token(token)
        unfollow_user(session=session, follower_id=follower_id, followee_id=user_id)
        return response(
            response_type=2,
            status_code=HTTP_200_OK,
            media_type=MEDIA_TYPE,
            content={'status': 'success', 'data': {'unfollowed': True}},
        )
    except Exception as exception:
        logger.exception(msg=f"{request.client.host}:{request.client.port}: {exception}")
        return response(
            response_type=2,
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            media_type=MEDIA_TYPE,
            content={'message': 'Internal Server Error'},
        )
