from __future__ import annotations

from typing import Literal
from uuid import UUID

from sqlalchemy import and_, asc, desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.core.database.models import *


async def select_user_by_username(session: AsyncSession, username: str) -> UserAccounts | None:
    statement = (
        select(UserAccounts)
        .select_from(UserAccounts)
        .options(
            joinedload(UserAccounts.user_profile_relationship),
            joinedload(UserAccounts.team_relationship),
        )
        .where(and_(UserAccounts.username == username, UserAccounts.active == True))  # noqa: E712
    )
    result = await session.execute(statement)
    return result.scalars().first()


async def select_user_by_user_account_id(
    session: AsyncSession,
    user_account_id: UUID,
) -> UserAccounts | None:
    statement = (
        select(UserAccounts)
        .select_from(UserAccounts)
        .where(and_(UserAccounts.id == user_account_id, UserAccounts.active == True))  # noqa: E712
    )
    result = await session.execute(statement)
    return result.scalars().first()

async def select_team_by_user_account_id(
    session: AsyncSession,
    user_account_id: UUID,
) -> Teams | None:
    statement = (
        select(Teams)
        .select_from(UserAccounts)
        .join(Teams, Teams.id == UserAccounts.team_id)
        .where(UserAccounts.id == user_account_id)
        .correlate(None)
    )
    result = await session.execute(statement)
    return result.scalar_one_or_none()



async def select_user_full_name_by_user_account_id(session: AsyncSession, user_account_id) -> str | None:
    statement = (
        select(UserProfiles.full_name)
        .select_from(UserAccounts)
        .join(UserProfiles, UserProfiles.id == UserAccounts.user_profile_id)
        .where(UserAccounts.id == user_account_id)
        .correlate(None)
    )
    result = await session.execute(statement)
    return result.scalar_one_or_none()


'''async def select_user_role_name_by_user_role_id(
    session: AsyncSession,
    user_role_id: UUID,
) -> str | None:
    statement = select(UserRoles.description).where(UserRoles.id == user_role_id).correlate(None)
    result = await session.execute(statement)
    return result.scalar_one_or_none()
'''

async def validate_user_authentication(
    session: AsyncSession,
    username: str,
    password: str,
) -> UserAccounts | Literal[False]:
    user_account = await select_user_by_username(session=session, username=username)

    if not user_account or not user_account.verify_password(password) or not user_account.active:
        return False

    return user_account


'''async def select_all_user_roles(session: AsyncSession) -> list[UserRoles]:
    statement = select(UserRoles)
    result = await session.execute(statement)
    return list(result.scalars().all())
'''


async def select_request_type_description_by_id(session: AsyncSession, request_type_id: UUID,):
    statement = (
        select(RequestTypes)
        .select_from(RequestTypes)
        .where(RequestTypes.id == request_type_id)
    )
    result = await session.execute(statement)
    
    object_model = result.scalars().first()
    
    return object_model.description if object_model else None

async def select_priority_type_description_by_id(session: AsyncSession, priority_type_id: UUID,):
    statement = (
        select(PriorityTypes)
        .select_from(PriorityTypes)
        .where(PriorityTypes.id == priority_type_id)
    )
    result = await session.execute(statement)
    
    object_model = result.scalars().first()
    
    return object_model.description if object_model else None


async def select_status_type_description_by_id(session: AsyncSession, status_type_id: UUID,):
    statement = (
        select(StatusTypes)
        .select_from(StatusTypes)
        .where(StatusTypes.id == status_type_id)
    )
    result = await session.execute(statement)
    object_model = result.scalars().first()
    
    return object_model.description if object_model else None





async def select_total_tickets_by_team_id(
    session: AsyncSession,
    team_id: UUID,
) -> UserAccounts | None:
    statement = (
        select(Tickets)
        .select_from(Tickets)
        .where(and_(Tickets.team_id == team_id, Tickets.active == True))
    )
    result = await session.execute(statement)




async def select_all_tickets_by_requester_id(session: AsyncSession, requester_id: UUID):
    statement = (
        select(Tickets)
        .select_from(Tickets)
        .where(and_(Tickets.requester_id == requester_id, Tickets.is_active == True))
    )
    result = await session.execute(statement)
    data = [
        {
            'id': object_model.id,
            'code': object_model.code,
            'note': object_model.note,
            'requestTypeId': object_model.request_type_id,
            'request': await select_request_type_description_by_id(session=session, request_type_id=object_model.request_type_id),
            'priorityTypeId': object_model.priority_type_id,
            'priority': await select_priority_type_description_by_id(session=session, priority_type_id=object_model.priority_type_id),
            'statusTypeId': object_model.status_type_id,
            'status': await select_status_type_description_by_id(session=session, status_type_id=object_model.status_type_id),
            
            # id del solicitante
            'requesterId': object_model.requester_id,

            # id de la persona que toma el ticket
            'managerId': object_model.manager_id if object_model.manager_id is not None else None,
            'manager': await select_user_full_name_by_user_account_id(session=session, user_account_id=object_model.manager_id) if object_model.manager_id is not None else None,

            'requester': await select_user_full_name_by_user_account_id(session=session, user_account_id=object_model.requester_id),
            'teamId': object_model.team_id,
            'duetAt': object_model.due_at,
            'resolvedAt': object_model.resolved_at,
            'closedAt': object_model.closed_at,
            'deletedAt': object_model.deleted_at,
            'createdAt': object_model.created_at,
            'updatedAt': object_model.updated_at,
            'isResolved': object_model.is_resolved,
            'attachments': await select_all_tickets_attachments_by_ticket_id(session=session, ticket_id=object_model.id)

        } for object_model in result.all()
    ]

    return data



async def select_ticket_attachments_by_ticket_id(session: AsyncSession, ticket_id: UUID):
    statement = (
        select(TicketAttachments)
        .where(
            TicketAttachments.ticket_id == ticket_id,
        )
    )
    result = await session.execute(statement)
    tickets = result.scalars().all()
    
    data = []
    


async def select_all_tickets_by_requester_id(session: AsyncSession, requester_id: UUID):
    statement = (
        select(Tickets)
        .where(
            Tickets.requester_id == requester_id,
            Tickets.is_active.is_(True),  # mejor que == True
        )
        .order_by(asc(Tickets.created_at))
    )
    result = await session.execute(statement)
    object_models = result.scalars().all()
    data = [
        {
            'id': object_model.id,
            'code': object_model.code,
            'note': object_model.note,
            'requestTypeId': object_model.request_type_id,
            'request': await select_request_type_description_by_id(session=session, request_type_id=object_model.request_type_id),  # si es async
            'priorityTypeId': object_model.priority_type_id,
            'priority': await select_priority_type_description_by_id(session=session, priority_type_id=object_model.priority_type_id),
            'statusTypeId': object_model.status_type_id,
            'status': await select_status_type_description_by_id(session=session, status_type_id=object_model.status_type_id),
            'requesterId': object_model.requester_id,
            #'assigneeId': object_model.assignee_id,
            'requester': await select_user_full_name_by_user_account_id(session=session, user_account_id=object_model.requester_id),
            #'assignee': await select_user_full_name_by_user_account_id(session=session, user_account_id=object_model.assignee_id) if object_model.assignee_id else None,
            
            # id de la persona que toma el ticket
            'managerId': object_model.manager_id if object_model.manager_id is not None else None,
            'manager': await select_user_full_name_by_user_account_id(session=session, user_account_id=object_model.manager_id) if object_model.manager_id is not None else None,

            'teamId': object_model.team_id,
            'duetAt': object_model.due_at.strftime('%d/%m/%Y %H:%M:%S %p') if object_model.due_at is not None else None,
            'resolvedAt': object_model.resolved_at.strftime('%d/%m/%Y %H:%M:%S %p') if object_model.resolved_at is not None else None,
            'closedAt': object_model.closed_at.strftime('%d/%m/%Y %H:%M:%S %p') if object_model.closed_at is not None else None,
            'deletedAt': object_model.deleted_at.strftime('%d/%m/%Y %H:%M:%S %p') if object_model.deleted_at is not None else None,
            'createdAt': object_model.created_at.strftime('%d/%m/%Y %H:%M:%S %p') if object_model.created_at is not None else None,
            'updatedAt': object_model.updated_at.strftime('%d/%m/%Y %H:%M:%S %p') if object_model.updated_at is not None else None,
            'isResolved': object_model.is_resolved,
            'isReaded': object_model.is_readed,
            'attachments': await select_all_tickets_attachments_by_ticket_id(session=session, ticket_id=object_model.id)

        } for object_model in object_models
    ]
    
    return data


async def select_all_tickets_by_assignee_id(session: AsyncSession, assignee_id: UUID):
    statement = (
        select(Tickets)
        .where(
            Tickets.assignee_id == assignee_id,
            Tickets.is_active.is_(True),  # mejor que == True
        )
        .order_by(asc(Tickets.created_at))
    )
    result = await session.execute(statement)
    object_models = result.scalars().all()
    data = [
        {
            'id': object_model.id,
            'code': object_model.code,
            'note': object_model.note,
            'requestTypeId': object_model.request_type_id,
            'request': await select_request_type_description_by_id(session=session, request_type_id=object_model.request_type_id),  # si es async
            'priorityTypeId': object_model.priority_type_id,
            'priority': await select_priority_type_description_by_id(session=session, priority_type_id=object_model.priority_type_id),
            'statusTypeId': object_model.status_type_id,
            'status': await select_status_type_description_by_id(session=session, status_type_id=object_model.status_type_id),

            'requesterId': object_model.requester_id,
            'requester': await select_user_full_name_by_user_account_id(session=session, user_account_id=object_model.requester_id),
            
            'managerId': object_model.manager_id if object_model.manager_id is not None else None,
            'manager': await select_user_full_name_by_user_account_id(session=session, user_account_id=object_model.manager_id) if object_model.manager_id is not None else None,

            'teamId': object_model.team_id,
            'duetAt': object_model.due_at.strftime('%d/%m/%Y %H:%M:%S %p') if object_model.due_at is not None else None,
            'resolvedAt': object_model.resolved_at.strftime('%d/%m/%Y %H:%M:%S %p') if object_model.resolved_at is not None else None,
            'closedAt': object_model.closed_at.strftime('%d/%m/%Y %H:%M:%S %p') if object_model.closed_at is not None else None,
            'deletedAt': object_model.deleted_at.strftime('%d/%m/%Y %H:%M:%S %p') if object_model.deleted_at is not None else None,
            'createdAt': object_model.created_at.strftime('%d/%m/%Y %H:%M:%S %p') if object_model.created_at is not None else None,
            'updatedAt': object_model.updated_at.strftime('%d/%m/%Y %H:%M:%S %p') if object_model.updated_at is not None else None,
            'isResolved': object_model.is_resolved,
            'isReaded': object_model.is_readed,
            'attachments': await select_all_tickets_attachments_by_ticket_id(session=session, ticket_id=object_model.id)
        } for object_model in object_models
    ]
    
    return data


async def select_all_tickets_attachments_by_ticket_id(session: AsyncSession, ticket_id: UUID):
    statement = (
        select(TicketAttachments)
        .where(TicketAttachments.ticket_id == ticket_id)
        .order_by(asc(TicketAttachments.created_at))
    )
    result = await session.execute(statement)
    object_models = result.scalars().all()
    
    data = [
        {
            'id': object_model.id,
            'ticketId': object_model.ticket_id,
            'fileName': object_model.file_name,
            'fileStorageName': object_model.file_uuid_name,
            'filePath': object_model.file_path,
            'fileSize': object_model.file_size,
            'mimeType': object_model.mime_type,
            'createdAt': object_model.created_at.strftime('%d/%m/%Y %H:%M:%S %p') if object_model.created_at is not None else None,
        } for object_model in object_models
    ]
    
    return data
    
async def select_all_tickets_for_manager(session: AsyncSession):
    statement = (
        select(Tickets)
        .where(Tickets.is_active.is_(True))
        .order_by(asc(Tickets.created_at))
    )

    result = await session.execute(statement)
    object_models = result.scalars().all()

    data = [
        {
            'id': object_model.id,
            'code': object_model.code,
            'note': object_model.note,
            'requestTypeId': object_model.request_type_id,
            'request': await select_request_type_description_by_id(session=session, request_type_id=object_model.request_type_id),  # si es async
            'priorityTypeId': object_model.priority_type_id,
            'priority': await select_priority_type_description_by_id(session=session, priority_type_id=object_model.priority_type_id),
            'statusTypeId': object_model.status_type_id,
            'status': await select_status_type_description_by_id(session=session, status_type_id=object_model.status_type_id),
            'requesterId': object_model.requester_id,
            'requester': await select_user_full_name_by_user_account_id(session=session, user_account_id=object_model.requester_id),
            
            'managerId': object_model.manager_id if object_model.manager_id is not None else None,
            'manager': await select_user_full_name_by_user_account_id(session=session, user_account_id=object_model.manager_id) if object_model.manager_id is not None else None,

            'teamId': object_model.team_id,
            'duetAt': object_model.due_at.strftime('%d/%m/%Y %H:%M:%S %p') if object_model.due_at is not None else None,
            'resolvedAt': object_model.resolved_at.strftime('%d/%m/%Y %H:%M:%S %p') if object_model.resolved_at is not None else None,
            'closedAt': object_model.closed_at.strftime('%d/%m/%Y %H:%M:%S %p') if object_model.closed_at is not None else None,
            'deletedAt': object_model.deleted_at.strftime('%d/%m/%Y %H:%M:%S %p') if object_model.deleted_at is not None else None,
            'createdAt': object_model.created_at.strftime('%d/%m/%Y %H:%M:%S %p') if object_model.created_at is not None else None,
            'updatedAt': object_model.updated_at.strftime('%d/%m/%Y %H:%M:%S %p') if object_model.updated_at is not None else None,
            'isResolved': object_model.is_resolved,
            'isReaded': object_model.is_readed,
            'attachments': await select_all_tickets_attachments_by_ticket_id(session=session, ticket_id=object_model.id)
        } for object_model in object_models
    ]
    
    return data







async def select_all_finished_tickets_by_requester_id(session: AsyncSession, requester_id: UUID):
    statement = (
        select(Tickets)
        .where(
            Tickets.requester_id == requester_id,
            Tickets.is_active.is_(True),
            Tickets.is_resolved.is_(True)
        )
        .order_by(asc(Tickets.created_at))
    )
    result = await session.execute(statement)
    object_models = result.scalars().all()

    data = [
        {
            'id': object_model.id,
            'code': object_model.code,
            'note': object_model.note,
            'requestTypeId': object_model.request_type_id,
            'request': await select_request_type_description_by_id(session=session, request_type_id=object_model.request_type_id),  # si es async
            'priorityTypeId': object_model.priority_type_id,
            'priority': await select_priority_type_description_by_id(session=session, priority_type_id=object_model.priority_type_id),
            'statusTypeId': object_model.status_type_id,
            'status': await select_status_type_description_by_id(session=session, status_type_id=object_model.status_type_id),
            'requesterId': object_model.requester_id,
            'managerId': object_model.manager_id if object_model.manager_id is not None else None,
            'manager': await select_user_full_name_by_user_account_id(session=session, user_account_id=object_model.manager_id) if object_model.manager_id is not None else None,

            'requester': await select_user_full_name_by_user_account_id(session=session, user_account_id=object_model.requester_id),
            'teamId': object_model.team_id,
            'duetAt': object_model.due_at.strftime('%d/%m/%Y %H:%M:%S %p') if object_model.due_at is not None else None,
            'resolvedAt': object_model.resolved_at.strftime('%d/%m/%Y %H:%M:%S %p') if object_model.resolved_at is not None else None,
            'closedAt': object_model.closed_at.strftime('%d/%m/%Y %H:%M:%S %p') if object_model.closed_at is not None else None,
            'deletedAt': object_model.deleted_at.strftime('%d/%m/%Y %H:%M:%S %p') if object_model.deleted_at is not None else None,
            'createdAt': object_model.created_at.strftime('%d/%m/%Y %H:%M:%S %p') if object_model.created_at is not None else None,
            'updatedAt': object_model.updated_at.strftime('%d/%m/%Y %H:%M:%S %p') if object_model.updated_at is not None else None,
            'isResolved': object_model.is_resolved,
            'isReaded': object_model.is_readed,
            'attachments': await select_all_tickets_attachments_by_ticket_id(session=session, ticket_id=object_model.id)
        } for object_model in object_models
    ]

    return data

async def select_count_tickets_by_requester_id(session: AsyncSession, requester_id: UUID, status: str) -> int:
    statement = (
        select(Tickets)
        .select_from(Tickets)
        .join(StatusTypes, StatusTypes.id == Tickets.status_type_id)
        .where(
            Tickets.requester_id == requester_id,
            StatusTypes.description == status
        )
    )
    result = await session.execute(statement)
    object_models = result.scalars().all()

    data = {'count': len(object_models) if object_models else 0}
    
    return data


async def select_count_tickets_for_manager(session: AsyncSession, status: str) -> int:
    statement = (
        select(Tickets)
        .select_from(Tickets)
        .join(StatusTypes, StatusTypes.id == Tickets.status_type_id)
        .where(StatusTypes.description == status)
    )
    result = await session.execute(statement)
    object_models = result.scalars().all()

    data = {'count': len(object_models) if object_models else 0}
    
    return data


















async def select_all_tickets(
    session: AsyncSession,
    team_id: UUID,
) -> UserAccounts | None:
    statement = (
        select(Tickets)
        .select_from(Tickets)
        .where(and_(Tickets.team_id == team_id, Tickets.active == True))
    )
    result = await session.execute(statement)
    return result.scalars().all()


async def select_all_request_types(
    session: AsyncSession
) -> RequestTypes | None:
    statement = (
        select(RequestTypes)
        .select_from(RequestTypes)
    )
    result = await session.execute(statement)
    return result.scalars().all()


async def select_all_priority_types(
    session: AsyncSession
) -> PriorityTypes | None:
    statement = (
        select(PriorityTypes)
        .select_from(PriorityTypes)
    )
    result = await session.execute(statement)
    return result.scalars().all()


async def select_all_status_types(
    session: AsyncSession
) -> StatusTypes | None:
    statement = (
        select(StatusTypes)
        .select_from(StatusTypes)
    )
    result = await session.execute(statement)
    return result.scalars().all()


async def select_all_teams(
    session: AsyncSession
) -> Teams | None:
    statement = (
        select(Teams)
        .select_from(Teams)
    )
    result = await session.execute(statement)
    return result.scalars().all()




async def select_all_support_users(session: AsyncSession) -> list[dict]:
    statement = (
        select(
            UserAccounts.id.label("user_id"),
            UserAccounts.username,
            UserProfiles.full_name,
        )
        .select_from(UserAccounts)
        .join(Teams, Teams.id == UserAccounts.team_id)
        .join(UserProfiles, UserProfiles.id == UserAccounts.user_profile_id)
        .where(
            UserProfiles.is_active.is_(True),
            Teams.description == "Soporte",
        )
        .correlate(None)
    )

    result = await session.execute(statement)

    payload: list[dict] = [
        {"id": str(user_id), "username": username, "full_name": full_name}
        for user_id, username, full_name in result.all()
    ]
    return payload


async def select_ticket_attachment_by_id(session: AsyncSession, attachment_id: UUID) -> TicketAttachments | None:
    statement = (
        select(TicketAttachments)
        .select_from(TicketAttachments)
        .where(TicketAttachments.id == attachment_id)
    )
    result = await session.execute(statement)
    return result.scalars().first()


async def select_ticket_attachments_by_ticket_id(session: AsyncSession, ticket_id: UUID) -> list[TicketAttachments]:
    statement = (
        select(TicketAttachments)
        .select_from(TicketAttachments)
        .where(TicketAttachments.ticket_id == ticket_id)
        .order_by(TicketAttachments.created_at.asc())
    )
    result = await session.execute(statement)
    return list(result.scalars().all())




'''async def select_all_group_types(
    session: AsyncSession
) -> GroupTypes | None:
    statement = (
        select(GroupTypes)
    )
    result = await session.execute(statement)
    return result.scalars().all()
'''
