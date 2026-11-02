import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ChatSource(BaseModel):
    document_title: str
    section: str
    page_number: int
    version: str
    region: str
    category: str
    similarity_score: float


class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    region: Optional[str] = None
    conversation_id: Optional[str] = None
    top_k: int = Field(default=5, ge=1, le=10)


class ChatResponse(BaseModel):
    answer: str
    confidence: str  # "high" | "medium" | "low" | "none"
    sources: List[ChatSource]
    requires_hr: bool
    conversation_id: str
    query: str
    region: str
    refusal: bool = False
    processing_time_ms: Optional[int] = None


class ConversationMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str
    sources: Optional[List[ChatSource]] = None
    confidence: Optional[str] = None
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


class ConversationResponse(BaseModel):
    id: uuid.UUID
    title: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    messages: List[ConversationMessage] = []

    model_config = ConfigDict(from_attributes=True)


class ConversationSummary(BaseModel):
    id: uuid.UUID
    title: Optional[str]
    created_at: datetime
    updated_at: datetime
    message_count: int = 0

    model_config = ConfigDict(from_attributes=True)
