from fastapi import Form
from datetime import datetime, timezone
from pydantic import BaseModel, ConfigDict, field_validator
from uuid import UUID

class TicketRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str
    note: str = ''

    request_type_id: UUID
    priority_type_id: UUID
    status_type_id: UUID
    requester_id: UUID
    assignee_id: UUID
    team_id: UUID | None = None

    due_at: datetime | None = None
    resolved_at: datetime | None = None
    closed_at: datetime | None = None

    @field_validator('due_at', 'resolved_at', 'closed_at', mode='before')
    @classmethod
    def _tzaware(cls, v):
        if isinstance(v, datetime) and v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v

    # Parsear multipart -> modelo
    @classmethod
    def as_form(
        cls,
        code: str = Form(...),
        note: str = Form(''),
        request_type_id: UUID = Form(...),
        priority_type_id: UUID = Form(...),
        status_type_id: UUID = Form(...),
        requester_id: UUID = Form(...),
        assignee_id: UUID | None = Form(None),
        team_id: UUID | None = Form(None),
        due_at: datetime | None = Form(None),
        resolved_at: datetime | None = Form(None),
        closed_at: datetime | None = Form(None),
    ) -> "TicketRequest":
        return cls(
            code=code, note=note,
            request_type_id=request_type_id, priority_type_id=priority_type_id,
            status_type_id=status_type_id, requester_id=requester_id,
            assignee_id=assignee_id, team_id=team_id,
            due_at=due_at, resolved_at=resolved_at, closed_at=closed_at,
        )
