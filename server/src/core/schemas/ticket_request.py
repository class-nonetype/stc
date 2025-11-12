from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID
from pydantic import (
    BaseModel,
    ConfigDict,
    AwareDatetime,
    Field,
    field_validator,
    model_validator,
)


class TicketRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str = Field(..., min_length=1, max_length=32)
    #title: str = Field(..., min_length=1, max_length=100)
    note: str = Field('', min_length=0)

    request_type_id: UUID
    priority_type_id: UUID
    status_type_id: UUID
    requester_id: UUID
    assignee_id: UUID | None = None
    team_id: UUID | None = None
    
    

    # fecha límite (opcional)
    due_at: AwareDatetime | None = None

    # fecha de resolución (la suele poner el sistema)
    resolved_at: AwareDatetime | None = None

    # fecha de cierre (la suele poner el sistema)
    closed_at: AwareDatetime | None = None

    # Acepta datetimes naive y los vuelve UTC-aware
    @field_validator('due_at', 'resolved_at', 'closed_at', mode='before')
    @classmethod
    def _ensure_tzaware(cls, v):
        if v is None: return v
        if isinstance(v, datetime) and v.tzinfo is None: return v.replace(tzinfo=timezone.utc)
        return v

    @model_validator(mode='after')
    def _temporal_consistency(self):
        # Si hay closed_at debe existir resolved_at y no ser anterior
        if self.closed_at and not self.resolved_at: raise ValueError('closed_at requiere resolved_at')
        if self.closed_at and self.closed_at < self.resolved_at: raise ValueError('closed_at no puede ser anterior a resolved_at')
        return self
