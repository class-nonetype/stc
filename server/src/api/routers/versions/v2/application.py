from datetime import datetime, timedelta
from pathlib import Path
from uuid import UUID, uuid4
from typing import Annotated

from collections.abc import AsyncGenerator, Sequence


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

from src.core.schemas.ticket_request import TicketRequest

from src.core.database.queries.insert import insert_ticket
from src.core.database.queries.helpers import insert_object_model
from src.core.database.session import database
from src.core.database.queries.select import (
    select_all_tickets_by_requester_id,
    select_count_finished_tickets_by_requester_id,
    select_all_request_types,
    select_all_priority_types,
    select_all_status_types,
    select_all_teams,
    select_all_support_users,
    select_ticket_attachment_by_id,
)
from src.core.database.models import TicketAttachments
from src.utils.paths import TICKETS_ATTACHMENTS_DIRECTORY_PATH



router = APIRouter()





@router.get('/tickets')
async def get_all_tickets():
    statuses = ['open', 'in_progress', 'on_hold', 'resolved', 'closed', 'cancelled']
    priorities = ['low', 'medium', 'high', 'urgent']
    ticket_types = ['bug', 'feature', 'task', 'incident', 'question', 'support']
    subjects = [
        'Error en inicio de sesión',
        'Solicitud de acceso a sistema',
        'Actualización de software',
        'Reporte de incidencia en producción',
        'Pregunta sobre facturación',
        'Solicitud de soporte general',
        'Error intermitente en API',
        'Mejora de panel administrativo',
        'Revisión de contrato de servicio',
        'Sincronización fallida con CRM',
    ]
    requester_first_names = ['María', 'Juan', 'Luis', 'Carla', 'Pedro', 'Camila', 'Andrés', 'Paula', 'Sofía', 'Diego']
    requester_last_names = ['Torres', 'Ramírez', 'González', 'Fernández', 'Martínez', 'Pérez', 'López', 'Duarte', 'Silva', 'Rivas']

    base_datetime = datetime.utcnow()
    items = []

    total_tickets = 600
    for index in range(1, total_tickets + 1):
        status = statuses[index % len(statuses)]
        priority = priorities[index % len(priorities)]
        ticket_type = ticket_types[index % len(ticket_types)]
        subject = subjects[index % len(subjects)]

        requester_first = requester_first_names[index % len(requester_first_names)]
        requester_last = requester_last_names[(index // len(requester_first_names)) % len(requester_last_names)]
        requester_name = f'{requester_first} {requester_last}'
        requester_id = str(uuid4())

        created_at = base_datetime - timedelta(days=index // 5, hours=index % 24, minutes=(index * 3) % 60)
        updated_at = created_at + timedelta(hours=(index * 2) % 72)

        ticket_id = str(uuid4())
        code = f'TCK-{index:04d}'

        items.append({
            'id': ticket_id,
            'code': code,
            'title': subject,
            'description': (
                f'{subject}. Este es un ticket generado de manera ficticia para pruebas de interfaz. '
                f'Prioridad {priority.upper()} con estado {status.replace("_", " ").title()}. '
                f'Indice interno {index}.'
            ),
            'status': status,
            'priority': priority,
            'type': ticket_type,
            'requester': {
                'id': requester_id,
                'displayName': requester_name,
                'email': f'{requester_first.lower()}.{requester_last.lower()}@example.com',
                'avatarUrl': None,
            },
            'assignee': {
                'id': str(uuid4()),
                'displayName': f'Agente {index % 25 + 1}',
                'email': f'agente{index % 25 + 1}@support.local',
                'avatarUrl': None,
            },
            'tags': ['demo', priority, ticket_type],
            'createdAt': created_at.isoformat(timespec='seconds') + 'Z',
            'updatedAt': updated_at.isoformat(timespec='seconds') + 'Z',
        })

    return {
        'items': items,
        'total': total_tickets,
    }


@router.get('/select/all/tickets/{requester_id}')
async def get_all_tickets_by_requester_id(request: Request, session: Annotated[AsyncGenerator, Depends(database)],  requester_id: UUID):
    data = await select_all_tickets_by_requester_id(session=session, requester_id=requester_id)
    return {'data': data}


@router.get('/select/total/tickets/{requester_id}')
async def get_total_tickets(request: Request, session: Annotated[AsyncGenerator, Depends(database)],  requester_id: UUID):
    data = await select_count_finished_tickets_by_requester_id(session=session, requester_id=requester_id)
    return {'data': data}


@router.get(path='/select/all/request-types')
async def get_all_request_types(request: Request, session: Annotated[AsyncGenerator, Depends(database)]):
    data = await select_all_request_types(session)
    return {'data': data}

@router.get(path='/select/all/priority-types')
async def get_all_priority_types(request: Request, session: Annotated[AsyncGenerator, Depends(database)]):
    data = await select_all_priority_types(session)
    return {'data': data}


@router.get(path='/select/all/status-types')
async def get_all_status_types(request: Request, session: Annotated[AsyncGenerator, Depends(database)]):
    data = await select_all_status_types(session)
    return {'data': data}


@router.get(path='/select/all/teams')
async def get_all_teams(request: Request, session: Annotated[AsyncGenerator, Depends(database)]):
    data = await select_all_teams(session)
    return {'data': data}

@router.get(path='/select/all/support-users')
async def get_all_support_users(request: Request, session: Annotated[AsyncGenerator, Depends(database)]):
    data = await select_all_support_users(session)
    return {'data': data}


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
    assignee_id: str | None = Form(None),
    team_id: str | None = Form(None),
    due_at: str | None = Form(None),
    resolved_at: str | None = Form(None),
    closed_at: str | None = Form(None),
    attachments: Sequence[UploadFile] | None = File(None),
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
                'file_path': attachment.file_path.as_posix(),
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
        assignee_id=_optional_uuid(assignee_id, 'assignee_id'),
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
        uploads=list(attachments or []),
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






