import uuid
from datetime import datetime
from typing import Any, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class TicketCreate(BaseModel):
    question: str = Field(..., min_length=3, max_length=2000)
    conversation_id: Optional[uuid.UUID] = None
    confidence: Optional[str] = "low"
    retrieved_sources: Optional[List[dict[str, Any]]] = None
    priority: Optional[str] = "medium"


class TicketUpdate(BaseModel):
    status: Optional[str] = None  # open, in_progress, resolved, closed
    priority: Optional[str] = None
    assigned_to: Optional[uuid.UUID] = None
    resolution_notes: Optional[str] = None


class TicketResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    conversation_id: Optional[uuid.UUID] = None
    question: str
    status: str
    priority: str
    confidence: str
    assigned_to: Optional[uuid.UUID] = None
    retrieved_sources: Optional[List[dict[str, Any]]] = None
    resolution_notes: Optional[str] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class TicketReplyRequest(BaseModel):
    reply: str = Field(..., min_length=2)
    status: Optional[str] = "resolved"

