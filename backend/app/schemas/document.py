import uuid
from datetime import date, datetime
from typing import Any, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class DocumentBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    category: str = Field(..., min_length=1, max_length=100)
    region: str = Field(..., min_length=1, max_length=100)
    employee_type: str = Field("All", max_length=100)
    version: str = Field("1.0", max_length=50)
    effective_date: date
    expiration_date: Optional[date] = None


class DocumentCreate(DocumentBase):
    status: str = "active"


class DocumentUpdate(BaseModel):
    title: Optional[str] = None
    category: Optional[str] = None
    region: Optional[str] = None
    employee_type: Optional[str] = None
    version: Optional[str] = None
    effective_date: Optional[date] = None
    expiration_date: Optional[date] = None
    status: Optional[str] = None


class DocumentResponse(DocumentBase):
    id: uuid.UUID
    status: str
    file_path: str
    file_type: str
    file_size_bytes: int
    processing_status: str
    error_message: Optional[str] = None
    uploaded_by: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentChunkResponse(BaseModel):
    id: uuid.UUID
    document_id: uuid.UUID
    chunk_index: int
    chunk_text: str
    page_number: int
    section: str
    token_count: int
    embedding_id: Optional[str] = None
    chunk_metadata: Optional[dict[str, Any]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentLibraryItem(BaseModel):
    id: uuid.UUID
    title: str
    category: str
    region: str
    version: str
    effective_date: date
    status: str
    file_type: str
    file_size_bytes: int

    model_config = ConfigDict(from_attributes=True)
