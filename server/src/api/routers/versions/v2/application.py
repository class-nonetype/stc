from datetime import datetime, timedelta
from pathlib import Path
from uuid import UUID, uuid4
from typing import Annotated

from collections.abc import AsyncGenerator, Sequence

from starlette.status import *

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
    status,
)
from fastapi.encoders import jsonable_encoder
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.responses import response
from src.core.schemas.ticket_request import TicketRequest

from src.core.database.queries.insert import insert_request_type, insert_ticket
from src.core.database.queries.helpers import insert_object_model
from src.core.database.session import database


from src.core.database.queries.alter import update_ticket
from src.core.database.queries.select import (
    select_all_tickets_by_requester_id,
    select_all_tickets_for_manager,
    select_count_tickets_by_requester_id,
    select_count_tickets_for_manager,
    select_all_request_types,
    select_all_priority_types,
    select_all_status_types,
    select_all_teams,
    select_all_support_users,
    select_ticket_attachment_by_id,
)
from src.core.database.models import TicketAttachments
from src.utils.paths import TICKETS_ATTACHMENTS_DIRECTORY_PATH

from src.utils.logger import logger

router = APIRouter()


# id solicitante
@router.get('/select/all/tickets/requester/{requester_id}')
async def get_all_tickets_by_requester_id(request: Request,
                                          session: Annotated[AsyncSession, Depends(database)], 
                                          requester_id: UUID):
    data = await select_all_tickets_by_requester_id(session=session, requester_id=requester_id)

    return response(
        response_type=2,
        status_code=HTTP_200_OK,
        content={'data': data}
    )

# id usuario asignado
#@router.get('/select/all/tickets/assignee/{assignee_id}')
#async def get_all_tickets_by_assignee_id(request: Request,
#                                         session: Annotated[AsyncSession, Depends(database)], 
#                                         assignee_id: UUID):
#    data = await select_all_tickets_by_assignee_id(session=session, assignee_id=assignee_id)
#    return {'data': data}


# encargado
@router.get('/select/all/tickets/manager')
async def get_all_tickets_for_manager(request: Request, session: Annotated[AsyncSession, Depends(database)]):
    data = await select_all_tickets_for_manager(session=session)
    return {'data': data}




@router.get('/select/total/tickets/requester/{requester_id}')
async def get_total_tickets_by_requester_id(request: Request, session: Annotated[AsyncSession, Depends(database)], requester_id: UUID, status: str):
    data = await select_count_tickets_by_requester_id(session=session, requester_id=requester_id, status=status)
    return {'data': data}


@router.get('/select/total/tickets/manager')
async def get_total_tickets_for_manager(request: Request, session: Annotated[AsyncSession, Depends(database)], status: str):
    data = await select_count_tickets_for_manager(session=session, status=status)
    return {'data': data}












@router.get(path='/select/all/types/request')
async def get_all_request_types(request: Request, session: Annotated[AsyncSession, Depends(database)]):
    data = await select_all_request_types(session)
    return {'data': data}

@router.get(path='/select/all/types/priority')
async def get_all_priority_types(request: Request, session: Annotated[AsyncSession, Depends(database)]):
    data = await select_all_priority_types(session)
    return {'data': data}


@router.get(path='/select/all/types/status')
async def get_all_status_types(request: Request, session: Annotated[AsyncSession, Depends(database)]):
    data = await select_all_status_types(session)
    return {'data': data}


@router.get(path='/select/all/teams')
async def get_all_teams(request: Request, session: Annotated[AsyncSession, Depends(database)]):
    data = await select_all_teams(session)
    return {'data': data}

@router.get(path='/select/all/users/support')
async def get_all_support_users(request: Request, session: Annotated[AsyncSession, Depends(database)]):
    data = await select_all_support_users(session)
    return {'data': data}






@router.put(path='/update/ticket/{ticket_id}/status/{status_id}')
async def put_ticket_status(request: Request,
                            session: Annotated[AsyncSession, Depends(database)],
                            ticket_id: UUID,
                            status_id: UUID):
    operation = await update_ticket(
        session=session,
        context='status',
        ticket_id=ticket_id,
        object_id=status_id)
    
    if operation is None:
        return response(response_type=1, status_code=HTTP_404_NOT_FOUND)
    
    if operation is False:
        return response(response_type=1, status_code=HTTP_422_UNPROCESSABLE_ENTITY)

    return response(
        response_type=1,
        status_code=HTTP_200_OK,
    )

@router.put(path='/update/ticket/{ticket_id}/manager/{manager_id}')
async def put_ticket_manager(request: Request,
                             session: Annotated[AsyncSession, Depends(database)],
                             ticket_id: UUID,
                             manager_id: UUID):
    operation = await update_ticket(
        session=session,
        context='manager',
        ticket_id=ticket_id,
        object_id=manager_id)
    
    if operation is None:
        return response(response_type=1, status_code=HTTP_404_NOT_FOUND)
    
    if operation is False:
        return response(response_type=1, status_code=HTTP_422_UNPROCESSABLE_ENTITY)

    return response(
        response_type=1,
        status_code=HTTP_200_OK,
    )

@router.put(path='/update/ticket/{ticket_id}/read')
async def put_ticket_read_status(request: Request,
                                 session: Annotated[AsyncSession, Depends(database)],
                                 ticket_id: UUID):
    operation = await update_ticket(
        session=session,
        context='read',
        ticket_id=ticket_id)
    
    if operation is None:
        return response(response_type=1, status_code=HTTP_404_NOT_FOUND)
    
    if operation is False:
        return response(response_type=1, status_code=HTTP_422_UNPROCESSABLE_ENTITY)

    return response(
        response_type=1,
        status_code=HTTP_200_OK,
    )















@router.post(path='/create/ticket', status_code=status.HTTP_201_CREATED)
async def post_ticket(
    request: Request,
    session: Annotated[AsyncGenerator, Depends(database)],
    code: str = Form(...),
    note: str = Form(''),
    request_type_id: str = Form(...),
    priority_type_id: str = Form(...),
    status_type_id: str = Form(...),
    requester_id: str = Form(...),
    #assignee_id: str = Form(...),
    team_id: str | None = Form(None),
    due_at: str | None = Form(None),
    resolved_at: str | None = Form(None),
    closed_at: str | None = Form(None),
    attachments: (UploadFile | list[UploadFile] | Sequence[UploadFile] | None) = File(None),
):
    def _parse_uuid(value: str, field: str) -> UUID:
        try:
            return UUID(value)
        except (TypeError, ValueError) as exc:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"'{field}' no es un UUID valido") from exc


    def _optional_uuid(value: str | None, field: str = 'id') -> UUID | None:
        if value is None or not value.strip():
            return None
        return _parse_uuid(value, field)


    def _optional_str(value: str | None) -> str | None:
        if value is None:
            return None
        trimmed = value.strip()
        return trimmed or None


    def _normalize_uploads(value: UploadFile | Sequence[UploadFile] | None) -> list[UploadFile]:
        if value is None:
            return []
        if isinstance(value, (list, tuple)):
            return [v for v in value if v is not None]
        # cualquier cosa que no sea lista/tuple, trátala como un único archivo
        return [value]


    async def _handle_ticket_attachments(
        session: AsyncGenerator,
        ticket_id: UUID,
        uploads: list[UploadFile],
        request: Request,
    ) -> list[dict]:
        if not uploads: return []

        ticket_directory = Path(TICKETS_ATTACHMENTS_DIRECTORY_PATH / str(ticket_id))
        ticket_directory.mkdir(parents=True, exist_ok=True)

        payload: list[dict] = []
        for upload in uploads:
            filename = Path(upload.filename or 'archivo').name
            if not filename:
                upload.file.close()
                continue

            contents = await upload.read()
            
            file_uuid_name = f"{uuid4().hex}{Path(filename).suffix}"
            
            file_path = Path(ticket_directory / file_uuid_name)
            file_path.write_bytes(contents)

            attachment = await insert_object_model(
                session=session,
                base_model=TicketAttachments,
                data_model={
                    'ticket_id': ticket_id,
                    'file_name': filename,
                    'file_uuid_name': file_uuid_name,
                    'file_path': file_path.as_posix(),
                    'mime_type': upload.content_type,
                    'file_size': len(contents),
                },
            )
            payload.append({
                'id': str(attachment.id),
                'file_name': attachment.file_name,
                'file_uuid_name': attachment.file_uuid_name,
                'file_path': attachment.file_path,
                'mime_type': attachment.mime_type,
                'file_size': attachment.file_size,
                'url': request.url_for(
                    'download_ticket_attachment',
                    ticket_id=str(attachment.ticket_id),
                    attachment_id=str(attachment.id),
                ),
            })
            upload.file.close()

        return payload


    schema = TicketRequest(
        code=code,
        note=note,
        request_type_id=_parse_uuid(request_type_id, 'request_type_id'),
        priority_type_id=_parse_uuid(priority_type_id, 'priority_type_id'),
        status_type_id=_parse_uuid(status_type_id, 'status_type_id'),
        requester_id=_parse_uuid(requester_id, 'requester_id'),
        #assignee_id=_parse_uuid(assignee_id, 'assignee_id'),
        team_id=_optional_uuid(team_id, 'team_id'),
        due_at=_optional_str(due_at),
        resolved_at=_optional_str(resolved_at),
        closed_at=_optional_str(closed_at),
    )

    object_model = await insert_ticket(session=session, schema=schema)
    if not object_model:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='No se pudo crear el ticket')

    attachments_payload = await _handle_ticket_attachments(
        session=session,
        ticket_id=object_model.id,
        uploads=_normalize_uploads(attachments),
        request=request,
    )

    ticket_payload = jsonable_encoder(object_model)
    ticket_payload['attachments'] = attachments_payload
    return ticket_payload


@router.get(
    path='/download/ticket/{ticket_id}/attachments/{attachment_id}',
    name='download_ticket_attachment',
)
async def download_ticket_attachment(
    ticket_id: UUID,
    attachment_id: UUID,
    session: Annotated[AsyncGenerator, Depends(database)],
):
    attachment = await select_ticket_attachment_by_id(session=session, attachment_id=attachment_id)
    if not attachment or attachment.ticket_id != ticket_id: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Adjunto no encontrado')

    file_path = Path(TICKETS_ATTACHMENTS_DIRECTORY_PATH / str(ticket_id) / attachment.file_uuid_name)

    if not file_path.exists(): raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Archivo no disponible')

    return FileResponse(
        path=file_path,
        filename=attachment.file_name,
        media_type=attachment.mime_type or 'application/octet-stream',
    )






@router.post(path='/create/types/request')
async def post_request_type(request: Request,
                         session: Annotated[AsyncSession, Depends(database)],
                         description: str = Form(...),):

    logger.info(msg=f'{request.client.host}:{request.client.port}')

    try:
        object_model = await insert_request_type(session=session, description=description)

        return response(
            response_type=2,
            status_code=HTTP_200_OK,
            media_type='application/json',
            content={'status': True}
        ) if object_model else response(
            response_type=2,
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            media_type='application/json',
            content={'status': 'error'}
        )

    except Exception as exception:
        logger.exception(msg=f'{request.client.host}:{request.client.port}: {exception}')

        return response(
            response_type=2,
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            media_type='application/json',
            content={'message': 'Internal Server Error'}
        )
