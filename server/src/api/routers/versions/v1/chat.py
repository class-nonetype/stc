from asyncio import Lock
from typing import Annotated, Dict
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    WebSocket,
    WebSocketDisconnect
)
from sqlalchemy.orm import Session
from starlette.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_500_INTERNAL_SERVER_ERROR
)

from src.api.responses import response
from src.core.database.models.chat import ChatThread
from src.core.database.session import database, session as SessionLocal
from src.core.schemas.chat import (
    AddParticipantsRequest,
    DirectConversationCreateRequest,
    DirectMessageRequest,
    MessageUpdateRequest,
    MessageAttachmentResponse,
    MessageCreateRequest,
    MessageResponse,
    MessagesPageResponse,
    SocketMessagePayload,
    ThreadCreateRequest,
    ThreadListResponse,
    ThreadParticipantResponse,
    ThreadResponse
)
from src.core.security.tokens import JWTBearer, verify_access_token
from src.core.services.chat import (
    AttachmentNotFound,
    MessageNotFound,
    NotAllowed,
    ParticipantNotFound,
    SelfMessagingNotAllowed,
    ThreadNotFound,
    add_participants,
    create_message,
    edit_message,
    create_thread,
    get_last_message,
    get_or_create_direct_thread,
    list_direct_conversations,
    list_direct_messages,
    list_messages,
    list_threads,
    send_direct_message,
    soft_delete_all_messages,
    soft_delete_message
)
from src.utils.controls import MEDIA_TYPE
from src.utils.logger import logger


router = APIRouter()
jwt_bearer = JWTBearer()


class ConnectionManager:
    def __init__(self) -> None:
        self.connections: Dict[UUID, Dict[UUID, WebSocket]] = {}
        self._lock = Lock()

    async def connect(self, thread_id: UUID, user_id: UUID, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            thread_connections = self.connections.setdefault(thread_id, {})
            thread_connections[user_id] = websocket

    async def disconnect(self, thread_id: UUID, user_id: UUID) -> None:
        async with self._lock:
            thread_connections = self.connections.get(thread_id, {})
            thread_connections.pop(user_id, None)
            if not thread_connections:
                self.connections.pop(thread_id, None)

    async def broadcast(self, thread_id: UUID, payload: dict) -> None:
        async with self._lock:
            targets = list(self.connections.get(thread_id, {}).values())
        for websocket in targets:
            try:
                await websocket.send_json(payload)
            except Exception:
                continue


manager = ConnectionManager()


def _get_user_id_from_token(token: str) -> UUID:
    payload = verify_access_token(token=token, output=True)
    return UUID(payload['userAccountID'])


def _build_message_response(message) -> MessageResponse:
    sender_username = getattr(message.sender, 'username', None)
    attachments = []
    for attachment in getattr(message, 'attachments', []) or []:
        upload = getattr(attachment, 'upload', None)
        attachments.append(
            MessageAttachmentResponse(
                upload_id=attachment.upload_id,
                file_url=getattr(upload, 'file_url', None),
                file_name=getattr(upload, 'file_name', None),
                file_size=getattr(upload, 'file_size', None),
                file_uuid_name=getattr(upload, 'file_uuid_name', None)
            )
        )
    return MessageResponse(
        id=message.id,
        thread_id=message.thread_id,
        sender_id=message.sender_id,
        sender_username=sender_username,
        content=message.content,
        created_at=message.created_at,
        edited_at=message.edited_at,
        attachments=attachments
    )


def _build_thread_response(session: Session, thread, current_user_id: UUID | None = None) -> ThreadResponse:
    participants = []
    for participant in thread.participants:
        username = getattr(participant.user, 'username', None)
        participants.append(
            ThreadParticipantResponse(
                user_account_id=participant.user_account_id,
                username=username,
                joined_at=participant.joined_at,
                active=participant.active
            )
        )

    other_participant_id = None
    if thread.is_direct and current_user_id is not None:
        for participant in participants:
            if participant.user_account_id != current_user_id:
                other_participant_id = participant.user_account_id
                break

    last_message_obj = get_last_message(session=session, thread_id=thread.id)
    last_message = _build_message_response(last_message_obj) if last_message_obj else None

    return ThreadResponse(
        id=thread.id,
        is_direct=thread.is_direct,
        title=thread.title,
        created_by_id=thread.created_by_id,
        created_at=thread.created_at,
        updated_at=thread.updated_at,
        participants=participants,
        last_message=last_message,
        other_participant_id=other_participant_id
    )


@router.post(path='/threads')
async def post_thread(
    payload: ThreadCreateRequest,
    request: Request,
    session: Annotated[Session, Depends(database)],
    token: Annotated[str, Depends(jwt_bearer)]
):
    logger.info(msg=f'{request.client.host}:{request.client.port}')

    try:
        creator_id = _get_user_id_from_token(token)
        thread = create_thread(
            session=session,
            creator_id=creator_id,
            participant_ids=payload.participant_ids,
            title=payload.title,
            is_direct=False
        )
        data = _build_thread_response(session, thread, current_user_id=creator_id).model_dump(mode='json')

        return response(
            response_type=2,
            status_code=HTTP_201_CREATED,
            media_type=MEDIA_TYPE,
            content={'status': 'success', 'data': data}
        )
    except ParticipantNotFound as exception:
        return response(
            response_type=2,
            status_code=HTTP_400_BAD_REQUEST,
            media_type=MEDIA_TYPE,
            content={'status': 'error', 'message': str(exception)}
        )
    except Exception as exception:
        logger.exception(msg=f'{request.client.host}:{request.client.port}: {exception}')
        return response(
            response_type=2,
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            media_type=MEDIA_TYPE,
            content={'message': 'Internal Server Error'}
        )


@router.post(path='/threads/{thread_id}/participants')
async def post_thread_participants(
    thread_id: UUID,
    payload: AddParticipantsRequest,
    request: Request,
    session: Annotated[Session, Depends(database)],
    token: Annotated[str, Depends(jwt_bearer)]
):
    logger.info(msg=f'{request.client.host}:{request.client.port}')

    try:
        _ = _get_user_id_from_token(token)
        thread = add_participants(session=session, thread_id=thread_id, user_ids=payload.user_ids)
        data = _build_thread_response(session, thread).model_dump(mode='json')

        return response(
            response_type=2,
            status_code=HTTP_200_OK,
            media_type=MEDIA_TYPE,
            content={'status': 'success', 'data': data}
        )
    except ThreadNotFound:
        return response(
            response_type=2,
            status_code=HTTP_404_NOT_FOUND,
            media_type=MEDIA_TYPE,
            content={'status': 'error', 'message': 'Thread not found'}
        )
    except ParticipantNotFound as exception:
        return response(
            response_type=2,
            status_code=HTTP_400_BAD_REQUEST,
            media_type=MEDIA_TYPE,
            content={'status': 'error', 'message': str(exception)}
        )
    except Exception as exception:
        logger.exception(msg=f'{request.client.host}:{request.client.port}: {exception}')
        return response(
            response_type=2,
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            media_type=MEDIA_TYPE,
            content={'message': 'Internal Server Error'}
        )


@router.get(path='/threads')
async def get_threads(
    request: Request,
    session: Annotated[Session, Depends(database)],
    token: Annotated[str, Depends(jwt_bearer)],
    limit: int = 20,
    offset: int = 0,
    include_direct: bool = False
):
    logger.info(msg=f'{request.client.host}:{request.client.port}')

    try:
        user_id = _get_user_id_from_token(token)
        threads = list_threads(session=session, user_id=user_id, limit=limit, offset=offset)
        if not include_direct:
            threads = [thread for thread in threads if not thread.is_direct]

        payload = [
            _build_thread_response(session, thread, current_user_id=user_id)
            for thread in threads
        ]

        content = ThreadListResponse(threads=payload)

        return response(
            response_type=2,
            status_code=HTTP_200_OK,
            media_type=MEDIA_TYPE,
            content={'status': 'success', 'data': content.model_dump(mode='json')}
        )
    except Exception as exception:
        logger.exception(msg=f'{request.client.host}:{request.client.port}: {exception}')
        return response(
            response_type=2,
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            media_type=MEDIA_TYPE,
            content={'message': 'Internal Server Error'}
        )


@router.get(path='/threads/{thread_id}/messages')
async def get_thread_messages(
    thread_id: UUID,
    request: Request,
    session: Annotated[Session, Depends(database)],
    token: Annotated[str, Depends(jwt_bearer)],
    limit: int = 50,
    before: UUID | None = None
):
    logger.info(msg=f'{request.client.host}:{request.client.port}')

    try:
        user_id = _get_user_id_from_token(token)
        thread = session.get(ChatThread, thread_id)
        if thread is None:
            return response(
                response_type=2,
                status_code=HTTP_404_NOT_FOUND,
                media_type=MEDIA_TYPE,
                content={'status': 'error', 'message': 'Thread not found'}
            )

        messages = list_messages(
            session=session,
            thread_id=thread_id,
            user_id=user_id,
            limit=limit,
            before=before
        )

        thread_payload = _build_thread_response(session, thread, current_user_id=user_id)
        messages_payload = [_build_message_response(message) for message in messages]

        page = MessagesPageResponse(
            thread_id=thread_id,
            other_participant_id=thread_payload.other_participant_id if thread.is_direct else None,
            messages=messages_payload
        )

        return response(
            response_type=2,
            status_code=HTTP_200_OK,
            media_type=MEDIA_TYPE,
            content={'status': 'success', 'data': page.model_dump(mode='json')}
        )
    except ParticipantNotFound as exception:
        return response(
            response_type=2,
            status_code=HTTP_404_NOT_FOUND,
            media_type=MEDIA_TYPE,
            content={'status': 'error', 'message': str(exception)}
        )
    except Exception as exception:
        logger.exception(msg=f'{request.client.host}:{request.client.port}: {exception}')
        return response(
            response_type=2,
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            media_type=MEDIA_TYPE,
            content={'message': 'Internal Server Error'}
        )


@router.post(path='/threads/{thread_id}/messages')
async def post_thread_message(
    thread_id: UUID,
    payload: MessageCreateRequest,
    request: Request,
    session: Annotated[Session, Depends(database)],
    token: Annotated[str, Depends(jwt_bearer)]
):
    logger.info(msg=f'{request.client.host}:{request.client.port}')

    try:
        user_id = _get_user_id_from_token(token)
        message = create_message(
            session=session,
            thread_id=thread_id,
            sender_id=user_id,
            content=payload.content,
            attachment_ids=payload.attachment_ids
        )
        data = _build_message_response(message).model_dump(mode='json')

        await manager.broadcast(thread_id, {'event': 'message', 'data': data})

        return response(
            response_type=2,
            status_code=HTTP_201_CREATED,
            media_type=MEDIA_TYPE,
            content={'status': 'success', 'data': data}
        )
    except ThreadNotFound:
        return response(
            response_type=2,
            status_code=HTTP_404_NOT_FOUND,
            media_type=MEDIA_TYPE,
            content={'status': 'error', 'message': 'Thread not found'}
        )
    except AttachmentNotFound as exception:
        return response(
            response_type=2,
            status_code=HTTP_400_BAD_REQUEST,
            media_type=MEDIA_TYPE,
            content={'status': 'error', 'message': str(exception)}
        )
    except ParticipantNotFound as exception:
        return response(
            response_type=2,
            status_code=HTTP_400_BAD_REQUEST,
            media_type=MEDIA_TYPE,
            content={'status': 'error', 'message': str(exception)}
        )
    except Exception as exception:
        logger.exception(msg=f'{request.client.host}:{request.client.port}: {exception}')
        return response(
            response_type=2,
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            media_type=MEDIA_TYPE,
            content={'message': 'Internal Server Error'}
        )


@router.websocket(path='/ws/chat/{thread_id}')
async def websocket_chat(websocket: WebSocket, thread_id: UUID):
    token = websocket.headers.get('Authorization')
    if token and token.lower().startswith('bearer '):
        token = token[7:]
    else:
        token = websocket.query_params.get('token')

    if not token:
        await websocket.close(code=4401)
        return

    try:
        user_id = _get_user_id_from_token(token)
    except HTTPException:
        await websocket.close(code=4401)
        return

    db_session = SessionLocal()

    try:
        list_messages(session=db_session, thread_id=thread_id, user_id=user_id, limit=1)
        await manager.connect(thread_id, user_id, websocket)

        while True:
            payload = await websocket.receive_json()
            message_payload = SocketMessagePayload(**payload)
            message = create_message(
                session=db_session,
                thread_id=thread_id,
                sender_id=user_id,
                content=message_payload.content,
                attachment_ids=message_payload.attachment_ids
            )
            data = _build_message_response(message).model_dump(mode='json')
            await manager.broadcast(thread_id, {'event': 'message', 'data': data})

    except WebSocketDisconnect:
        pass
    except AttachmentNotFound as exception:
        await websocket.send_json({'event': 'error', 'message': str(exception)})
        await websocket.close()
    except ParticipantNotFound as exception:
        await websocket.send_json({'event': 'error', 'message': str(exception)})
        await websocket.close()
    except Exception as exception:
        logger.exception(msg=f'WebSocket error: {exception}')
        await websocket.close()
    finally:
        await manager.disconnect(thread_id, user_id)
        db_session.close()




@router.post(path='/direct/conversations')
async def post_direct_conversation(
    payload: DirectConversationCreateRequest,
    request: Request,
    session: Annotated[Session, Depends(database)],
    token: Annotated[str, Depends(jwt_bearer)]
):
    logger.info(msg=f"{request.client.host}:{request.client.port}")

    try:
        user_id = _get_user_id_from_token(token)
        thread = get_or_create_direct_thread(
            session=session,
            user_a_id=user_id,
            user_b_id=payload.recipient_id
        )
        data = _build_thread_response(session, thread, current_user_id=user_id).model_dump(mode='json')

        return response(
            response_type=2,
            status_code=HTTP_200_OK,
            media_type=MEDIA_TYPE,
            content={"status": "success", "data": data}
        )
    except SelfMessagingNotAllowed as exception:
        return response(
            response_type=2,
            status_code=HTTP_400_BAD_REQUEST,
            media_type=MEDIA_TYPE,
            content={"status": "error", "message": str(exception)}
        )
    except ParticipantNotFound as exception:
        return response(
            response_type=2,
            status_code=HTTP_404_NOT_FOUND,
            media_type=MEDIA_TYPE,
            content={"status": "error", "message": str(exception)}
        )
    except Exception as exception:
        logger.exception(msg=f"{request.client.host}:{request.client.port}: {exception}")
        return response(
            response_type=2,
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            media_type=MEDIA_TYPE,
            content={"message": "Internal Server Error"}
        )


@router.post(path='/direct/messages')
async def post_direct_message(
    payload: DirectMessageRequest,
    request: Request,
    session: Annotated[Session, Depends(database)],
    token: Annotated[str, Depends(jwt_bearer)]
):
    logger.info(msg=f'{request.client.host}:{request.client.port}')

    try:
        sender_id = _get_user_id_from_token(token)
        message, thread = send_direct_message(
            session=session,
            sender_id=sender_id,
            recipient_id=payload.recipient_id,
            content=payload.content,
            attachment_ids=payload.attachment_ids
        )
        message_payload = _build_message_response(message)
        thread_payload = _build_thread_response(session, thread, current_user_id=sender_id)

        await manager.broadcast(thread.id, {'event': 'message', 'data': message_payload.model_dump(mode='json')})

        return response(
            response_type=2,
            status_code=HTTP_201_CREATED,
            media_type=MEDIA_TYPE,
            content={
                'status': 'success',
                'data': {
                    'message': message_payload.model_dump(mode='json'),
                    'thread': thread_payload.model_dump(mode='json')
                }
            }
        )
    except SelfMessagingNotAllowed as exception:
        return response(
            response_type=2,
            status_code=HTTP_400_BAD_REQUEST,
            media_type=MEDIA_TYPE,
            content={'status': 'error', 'message': str(exception)}
        )
    except AttachmentNotFound as exception:
        return response(
            response_type=2,
            status_code=HTTP_400_BAD_REQUEST,
            media_type=MEDIA_TYPE,
            content={'status': 'error', 'message': str(exception)}
        )
    except ParticipantNotFound as exception:
        return response(
            response_type=2,
            status_code=HTTP_404_NOT_FOUND,
            media_type=MEDIA_TYPE,
            content={'status': 'error', 'message': str(exception)}
        )
    except Exception as exception:
        logger.exception(msg=f'{request.client.host}:{request.client.port}: {exception}')
        return response(
            response_type=2,
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            media_type=MEDIA_TYPE,
            content={'message': 'Internal Server Error'}
        )


@router.get(path='/direct/messages/{recipient_id}')
async def get_direct_messages(
    recipient_id: UUID,
    request: Request,
    session: Annotated[Session, Depends(database)],
    token: Annotated[str, Depends(jwt_bearer)],
    limit: int = 50,
    before: UUID | None = None
):
    logger.info(msg=f'{request.client.host}:{request.client.port}')

    try:
        user_id = _get_user_id_from_token(token)
        messages, thread = list_direct_messages(
            session=session,
            user_id=user_id,
            other_user_id=recipient_id,
            limit=limit,
            before=before
        )

        thread_payload = _build_thread_response(session, thread, current_user_id=user_id)
        messages_payload = [_build_message_response(message) for message in messages]

        page = MessagesPageResponse(
            thread_id=thread.id,
            other_participant_id=thread_payload.other_participant_id,
            messages=messages_payload
        )

        return response(
            response_type=2,
            status_code=HTTP_200_OK,
            media_type=MEDIA_TYPE,
            content={'status': 'success', 'data': page.model_dump(mode='json')}
        )
    except ThreadNotFound as exception:
        return response(
            response_type=2,
            status_code=HTTP_404_NOT_FOUND,
            media_type=MEDIA_TYPE,
            content={'status': 'error', 'message': str(exception)}
        )
    except ParticipantNotFound as exception:
        return response(
            response_type=2,
            status_code=HTTP_404_NOT_FOUND,
            media_type=MEDIA_TYPE,
            content={'status': 'error', 'message': str(exception)}
        )
    except Exception as exception:
        logger.exception(msg=f'{request.client.host}:{request.client.port}: {exception}')
        return response(
            response_type=2,
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            media_type=MEDIA_TYPE,
            content={'message': 'Internal Server Error'}
        )


@router.get(path='/direct/conversations')
async def get_direct_conversations(
    request: Request,
    session: Annotated[Session, Depends(database)],
    token: Annotated[str, Depends(jwt_bearer)],
    limit: int = 20,
    offset: int = 0
):
    logger.info(msg=f'{request.client.host}:{request.client.port}')

    try:
        user_id = _get_user_id_from_token(token)
        threads = list_direct_conversations(
            session=session,
            user_id=user_id,
            limit=limit,
            offset=offset
        )

        payload = [
            _build_thread_response(session, thread, current_user_id=user_id)
            for thread in threads
        ]

        content = ThreadListResponse(threads=payload)

        return response(
            response_type=2,
            status_code=HTTP_200_OK,
            media_type=MEDIA_TYPE,
            content={'status': 'success', 'data': content.model_dump(mode='json')}
        )
    except Exception as exception:
        logger.exception(msg=f'{request.client.host}:{request.client.port}: {exception}')
        return response(
            response_type=2,
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            media_type=MEDIA_TYPE,
            content={'message': 'Internal Server Error'}
        )


@router.websocket(path='/ws/direct/{recipient_id}')
async def websocket_direct_chat(websocket: WebSocket, recipient_id: UUID):
    token = websocket.headers.get('Authorization')
    if token and token.lower().startswith('bearer '):
        token = token[7:]
    else:
        token = websocket.query_params.get('token')

    if not token:
        await websocket.close(code=4401)
        return

    try:
        user_id = _get_user_id_from_token(token)
    except HTTPException:
        await websocket.close(code=4401)
        return

    db_session = SessionLocal()

    try:
        thread = get_or_create_direct_thread(
            session=db_session,
            user_a_id=user_id,
            user_b_id=recipient_id
        )

        await manager.connect(thread.id, user_id, websocket)

        while True:
            payload = await websocket.receive_json()
            message_payload = SocketMessagePayload(**payload)
            message = create_message(
                session=db_session,
                thread_id=thread.id,
                sender_id=user_id,
                content=message_payload.content,
                attachment_ids=message_payload.attachment_ids
            )
            data = _build_message_response(message).model_dump(mode='json')
            await manager.broadcast(thread.id, {'event': 'message', 'data': data})

    except WebSocketDisconnect:
        pass
    except SelfMessagingNotAllowed as exception:
        await websocket.send_json({'event': 'error', 'message': str(exception)})
        await websocket.close()
    except AttachmentNotFound as exception:
        await websocket.send_json({'event': 'error', 'message': str(exception)})
        await websocket.close()
    except ParticipantNotFound as exception:
        await websocket.send_json({'event': 'error', 'message': str(exception)})
        await websocket.close()
    except Exception as exception:
        logger.exception(msg=f'WebSocket error: {exception}')
        await websocket.close()
    finally:
        if 'thread' in locals():
            await manager.disconnect(thread.id, user_id)
        db_session.close()


@router.delete(path='/threads/{thread_id}/messages')
async def delete_thread_messages(
    thread_id: UUID,
    request: Request,
    session: Annotated[Session, Depends(database)],
    token: Annotated[str, Depends(jwt_bearer)]
):
    """Elimina (soft delete) todos los mensajes del hilo. En chats directos, cualquiera de los participantes puede hacerlo; en grupos, solo el creador del hilo."""
    logger.info(msg=f'{request.client.host}:{request.client.port}')

    try:
        user_id = _get_user_id_from_token(token)
        deleted_count = soft_delete_all_messages(session=session, thread_id=thread_id, requester_id=user_id)

        # Broadcast bulk deletion event to connected clients
        await manager.broadcast(thread_id, {'event': 'messages_deleted', 'data': {'deleted': deleted_count}})

        return response(
            response_type=2,
            status_code=HTTP_200_OK,
            media_type=MEDIA_TYPE,
            content={'status': 'success', 'data': {'deleted': deleted_count}}
        )
    except ThreadNotFound:
        return response(
            response_type=2,
            status_code=HTTP_404_NOT_FOUND,
            media_type=MEDIA_TYPE,
            content={'status': 'error', 'message': 'Thread not found'}
        )
    except (ParticipantNotFound, NotAllowed) as exception:
        return response(
            response_type=2,
            status_code=HTTP_400_BAD_REQUEST,
            media_type=MEDIA_TYPE,
            content={'status': 'error', 'message': str(exception)}
        )
    except Exception as exception:
        logger.exception(msg=f'{request.client.host}:{request.client.port}: {exception}')
        return response(
            response_type=2,
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            media_type=MEDIA_TYPE,
            content={'message': 'Internal Server Error'}
        )


@router.delete(path='/threads/{thread_id}/messages/{message_id}')
async def delete_thread_message(
    thread_id: UUID,
    message_id: UUID,
    request: Request,
    session: Annotated[Session, Depends(database)],
    token: Annotated[str, Depends(jwt_bearer)]
):
    """Elimina (soft delete) un mensaje específico del hilo si el solicitante está autorizado."""
    logger.info(msg=f'{request.client.host}:{request.client.port}')

    try:
        user_id = _get_user_id_from_token(token)
        message = soft_delete_message(
            session=session,
            thread_id=thread_id,
            message_id=message_id,
            requester_id=user_id
        )
        data = _build_message_response(message).model_dump(mode='json')

        # Notify clients that a message was deleted
        await manager.broadcast(thread_id, {'event': 'message_deleted', 'data': {'id': str(message_id), 'thread_id': str(thread_id)}})

        return response(
            response_type=2,
            status_code=HTTP_200_OK,
            media_type=MEDIA_TYPE,
            content={'status': 'success', 'data': data}
        )
    except ThreadNotFound:
        return response(
            response_type=2,
            status_code=HTTP_404_NOT_FOUND,
            media_type=MEDIA_TYPE,
            content={'status': 'error', 'message': 'Thread not found'}
        )
    except MessageNotFound:
        return response(
            response_type=2,
            status_code=HTTP_404_NOT_FOUND,
            media_type=MEDIA_TYPE,
            content={'status': 'error', 'message': 'Message not found'}
        )
    except (ParticipantNotFound, NotAllowed) as exception:
        return response(
            response_type=2,
            status_code=HTTP_400_BAD_REQUEST,
            media_type=MEDIA_TYPE,
            content={'status': 'error', 'message': str(exception)}
        )
    except Exception as exception:
        logger.exception(msg=f'{request.client.host}:{request.client.port}: {exception}')
        return response(
            response_type=2,
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            media_type=MEDIA_TYPE,
            content={'message': 'Internal Server Error'}
        )


@router.patch(path='/threads/{thread_id}/messages/{message_id}')
async def patch_thread_message(
    thread_id: UUID,
    message_id: UUID,
    payload: MessageUpdateRequest,
    request: Request,
    session: Annotated[Session, Depends(database)],
    token: Annotated[str, Depends(jwt_bearer)]
):
    """Modifica el contenido de un mensaje si el autor está dentro del tiempo permitido de edición."""
    logger.info(msg=f'{request.client.host}:{request.client.port}')

    try:
        user_id = _get_user_id_from_token(token)
        message = edit_message(
            session=session,
            thread_id=thread_id,
            message_id=message_id,
            requester_id=user_id,
            new_content=payload.content
        )
        data = _build_message_response(message).model_dump(mode='json')
        await manager.broadcast(thread_id, {'event': 'message_edited', 'data': data})
        return response(
            response_type=2,
            status_code=HTTP_200_OK,
            media_type=MEDIA_TYPE,
            content={'status': 'success', 'data': data}
        )
    except ThreadNotFound:
        return response(
            response_type=2,
            status_code=HTTP_404_NOT_FOUND,
            media_type=MEDIA_TYPE,
            content={'status': 'error', 'message': 'Thread not found'}
        )
    except MessageNotFound:
        return response(
            response_type=2,
            status_code=HTTP_404_NOT_FOUND,
            media_type=MEDIA_TYPE,
            content={'status': 'error', 'message': 'Message not found'}
        )
    except (ParticipantNotFound, NotAllowed) as exception:
        return response(
            response_type=2,
            status_code=HTTP_400_BAD_REQUEST,
            media_type=MEDIA_TYPE,
            content={'status': 'error', 'message': str(exception)}
        )
    except Exception as exception:
        logger.exception(msg=f'{request.client.host}:{request.client.port}: {exception}')
        return response(
            response_type=2,
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            media_type=MEDIA_TYPE,
            content={'message': 'Internal Server Error'}
        )
