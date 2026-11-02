import os
import shutil
import uuid
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, List, Optional

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_role
from app.db.models import (
    AuditLog,
    Document,
    DocumentChunk,
    DocumentStatus,
    ProcessingStatus,
    User,
    UserRole,
)
from app.db.session import get_db
from app.rag.ingestion import trigger_document_processing
from app.rag.vector_db import vector_db
from app.schemas.document import (
    DocumentChunkResponse,
    DocumentLibraryItem,
    DocumentResponse,
    DocumentUpdate,
)

router = APIRouter(tags=["Documents"])

STORAGE_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data" / "documents"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt", ".md"}
MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB


# ==========================================
# HR Admin Document Endpoints
# ==========================================
@router.post("/admin/documents", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: str = Form(...),
    category: str = Form(...),
    region: str = Form(...),
    employee_type: str = Form("All"),
    version: str = Form("1.0"),
    effective_date: str = Form(...),
    expiration_date: Optional[str] = Form(None),
    current_user: User = Depends(require_role(UserRole.HR_ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Upload and schedule processing for an HR policy document (PDF, DOCX, TXT)."""
    # 1. Validate file extension
    file_ext = Path(file.filename or "").suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{file_ext}'. Allowed formats: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    # 2. Parse dates
    try:
        parsed_eff_date = date.fromisoformat(effective_date)
        parsed_exp_date = date.fromisoformat(expiration_date) if expiration_date else None
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid date format (expected YYYY-MM-DD): {e}",
        )

    # 3. Save file to disk
    doc_id = uuid.uuid4()
    safe_filename = f"{doc_id}_{Path(file.filename or 'doc').name}"
    saved_path = STORAGE_DIR / safe_filename

    file_size = 0
    with open(saved_path, "wb") as buffer:
        while chunk := await file.read(1024 * 1024):  # 1MB chunks
            file_size += len(chunk)
            if file_size > MAX_FILE_SIZE_BYTES:
                saved_path.unlink(missing_ok=True)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="File exceeds maximum allowed size of 25MB",
                )
            buffer.write(chunk)

    # 4. Create Document record in DB
    doc = Document(
        id=doc_id,
        title=title,
        category=category,
        region=region,
        employee_type=employee_type,
        version=version,
        effective_date=parsed_eff_date,
        expiration_date=parsed_exp_date,
        status=DocumentStatus.ACTIVE.value,
        file_path=str(saved_path),
        file_type=file_ext.lstrip("."),
        file_size_bytes=file_size,
        processing_status=ProcessingStatus.QUEUED.value,
        uploaded_by=current_user.id,
    )
    db.add(doc)

    # 5. Create audit log
    audit = AuditLog(
        id=uuid.uuid4(),
        user_id=current_user.id,
        action="DOCUMENT_UPLOAD",
        resource_type="document",
        resource_id=str(doc.id),
        details={"title": title, "region": region, "version": version, "filename": file.filename},
    )
    db.add(audit)

    await db.commit()
    await db.refresh(doc)

    # 6. Trigger background processing pipeline
    trigger_document_processing(str(doc.id), background_tasks=background_tasks)

    return DocumentResponse.model_validate(doc)


@router.get("/admin/documents", response_model=List[DocumentResponse])
async def list_documents(
    region: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    current_user: User = Depends(require_role(UserRole.HR_ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """List all documents with optional region, category, and status filters."""
    query = select(Document).order_by(desc(Document.created_at))

    if region:
        query = query.where(Document.region == region)
    if category:
        query = query.where(Document.category == category)
    if status_filter:
        query = query.where(Document.status == status_filter)

    result = await db.execute(query)
    docs = result.scalars().all()
    return [DocumentResponse.model_validate(d) for d in docs]


@router.get("/admin/documents/{doc_id}", response_model=DocumentResponse)
async def get_document(
    doc_id: uuid.UUID,
    current_user: User = Depends(require_role(UserRole.HR_ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Retrieve full details of a specific policy document."""
    result = await db.execute(select(Document).where(Document.id == doc_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentResponse.model_validate(doc)


@router.put("/admin/documents/{doc_id}", response_model=DocumentResponse)
@router.patch("/admin/documents/{doc_id}", response_model=DocumentResponse)
async def update_document(
    doc_id: uuid.UUID,
    updates: DocumentUpdate,
    current_user: User = Depends(require_role(UserRole.HR_ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Update metadata for an existing document and synchronize Qdrant payloads."""
    result = await db.execute(select(Document).where(Document.id == doc_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    update_data = updates.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(doc, field, val)

    doc.updated_at = datetime.now(timezone.utc)

    # Synchronize vector database chunk payloads if metadata changed
    payload_updates: dict[str, Any] = {}
    if "region" in update_data:
        payload_updates["region"] = update_data["region"]
    if "category" in update_data:
        payload_updates["category"] = update_data["category"]
    if "employee_type" in update_data:
        payload_updates["employee_type"] = update_data["employee_type"]
    if "status" in update_data:
        payload_updates["status"] = update_data["status"]
    if "version" in update_data:
        payload_updates["version"] = update_data["version"]
    if "effective_date" in update_data:
        payload_updates["effective_date"] = update_data["effective_date"].isoformat() if update_data["effective_date"] else None
    if "expiration_date" in update_data:
        payload_updates["expiration_date"] = update_data["expiration_date"].isoformat() if update_data["expiration_date"] else None

    if payload_updates:
        try:
            vector_db.update_document_metadata(str(doc.id), payload_updates)
        except Exception:
            pass

    # Audit log
    audit = AuditLog(
        id=uuid.uuid4(),
        user_id=current_user.id,
        action="DOCUMENT_UPDATE",
        resource_type="document",
        resource_id=str(doc_id),
        details={"updated_fields": list(update_data.keys()), "title": doc.title},
    )
    db.add(audit)
    await db.commit()
    await db.refresh(doc)
    return DocumentResponse.model_validate(doc)


@router.delete("/admin/documents/{doc_id}")
async def delete_document(
    doc_id: uuid.UUID,
    current_user: User = Depends(require_role(UserRole.HR_ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Delete document, cascading delete chunks, vectors from Qdrant, and file on disk."""
    result = await db.execute(select(Document).where(Document.id == doc_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # 1. Delete points in Qdrant
    vector_db.delete_by_document_id(str(doc.id))

    # 2. Delete file on disk
    if doc.file_path and os.path.exists(doc.file_path):
        try:
            os.remove(doc.file_path)
        except Exception:
            pass

    # 3. Delete from DB
    await db.delete(doc)

    # 4. Audit Log
    audit = AuditLog(
        id=uuid.uuid4(),
        user_id=current_user.id,
        action="DOCUMENT_DELETE",
        resource_type="document",
        resource_id=str(doc_id),
        details={"title": doc.title},
    )
    db.add(audit)
    await db.commit()

    return {"message": f"Document '{doc.title}' deleted successfully."}


@router.post("/admin/documents/{doc_id}/activate", response_model=DocumentResponse)
async def activate_document(
    doc_id: uuid.UUID,
    current_user: User = Depends(require_role(UserRole.HR_ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Activate document and deactivate superseded older versions with the same title and region."""
    result = await db.execute(select(Document).where(Document.id == doc_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    doc.status = DocumentStatus.ACTIVE.value
    doc.updated_at = datetime.now(timezone.utc)
    vector_db.set_document_status(str(doc.id), DocumentStatus.ACTIVE.value)

    # Deactivate older active versions of the same policy
    superseded = await db.execute(
        select(Document).where(
            Document.title == doc.title,
            Document.region == doc.region,
            Document.category == doc.category,
            Document.id != doc.id,
            Document.status == DocumentStatus.ACTIVE.value,
        )
    )
    for old in superseded.scalars().all():
        old.status = DocumentStatus.INACTIVE.value
        old.updated_at = datetime.now(timezone.utc)
        vector_db.set_document_status(str(old.id), DocumentStatus.INACTIVE.value)

    # Audit log
    audit = AuditLog(
        id=uuid.uuid4(),
        user_id=current_user.id,
        action="DOCUMENT_ACTIVATE",
        resource_type="document",
        resource_id=str(doc_id),
        details={"title": doc.title, "version": doc.version},
    )
    db.add(audit)
    await db.commit()
    await db.refresh(doc)
    return DocumentResponse.model_validate(doc)


@router.post("/admin/documents/{doc_id}/deactivate", response_model=DocumentResponse)
async def deactivate_document(
    doc_id: uuid.UUID,
    current_user: User = Depends(require_role(UserRole.HR_ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Deactivate document so it will not be retrieved for employee queries."""
    result = await db.execute(select(Document).where(Document.id == doc_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    doc.status = DocumentStatus.INACTIVE.value
    doc.updated_at = datetime.now(timezone.utc)
    vector_db.set_document_status(str(doc.id), DocumentStatus.INACTIVE.value)

    audit = AuditLog(
        id=uuid.uuid4(),
        user_id=current_user.id,
        action="DOCUMENT_DEACTIVATE",
        resource_type="document",
        resource_id=str(doc_id),
        details={"title": doc.title, "version": doc.version},
    )
    db.add(audit)
    await db.commit()
    await db.refresh(doc)
    return DocumentResponse.model_validate(doc)


@router.get("/admin/documents/{doc_id}/chunks", response_model=List[DocumentChunkResponse])
async def get_document_chunks(
    doc_id: uuid.UUID,
    current_user: User = Depends(require_role(UserRole.HR_ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Inspect chunk records, page attribution, and embedding vector IDs for a document."""
    result = await db.execute(
        select(DocumentChunk)
        .where(DocumentChunk.document_id == doc_id)
        .order_by(DocumentChunk.chunk_index)
    )
    chunks = result.scalars().all()
    return [DocumentChunkResponse.model_validate(ch) for ch in chunks]


# ==========================================
# Employee Knowledge Library Endpoint
# ==========================================
@router.get("/documents/library", response_model=List[DocumentLibraryItem])
async def get_knowledge_library(
    region: Optional[str] = Query(None),
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """List approved active documents relevant to the employee's region (or Global)."""
    user_region = region or (current_user.region if current_user else "India")

    query = (
        select(Document)
        .where(
            Document.status == DocumentStatus.ACTIVE.value,
            Document.region.in_([user_region, "Global"]),
        )
        .order_by(Document.category, Document.title)
    )
    result = await db.execute(query)
    docs = result.scalars().all()
    return [DocumentLibraryItem.model_validate(d) for d in docs]


@router.get("/admin/documents/{doc_id}/download")
async def download_document(
    doc_id: uuid.UUID,
    current_user: User = Depends(require_role(UserRole.HR_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Download or preview the original uploaded policy document (PDF, DOCX, TXT)."""
    result = await db.execute(select(Document).where(Document.id == doc_id))
    doc = result.scalar_one_or_none()
    if not doc or not doc.file_path or not os.path.exists(doc.file_path):
        raise HTTPException(status_code=404, detail="Document file not found on disk")

    filename = Path(doc.file_path).name
    if "_" in filename:
        clean_filename = filename.split("_", 1)[1]
    else:
        clean_filename = filename

    media_type = "application/pdf" if doc.file_type == "pdf" else "application/octet-stream"
    return FileResponse(
        path=doc.file_path,
        filename=clean_filename,
        media_type=media_type,
    )


@router.post("/admin/documents/{doc_id}/retry", response_model=DocumentResponse)
async def retry_document_processing(
    doc_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_role(UserRole.HR_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Retry failed or stuck document ingestion pipeline."""
    result = await db.execute(select(Document).where(Document.id == doc_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    doc.processing_status = ProcessingStatus.QUEUED.value
    doc.error_message = None
    doc.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(doc)

    trigger_document_processing(str(doc.id), background_tasks=background_tasks)
    return DocumentResponse.model_validate(doc)


@router.post("/admin/documents/{doc_id}/reindex", response_model=DocumentResponse)
async def reindex_document(
    doc_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_role(UserRole.HR_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Re-extract, re-chunk, and re-embed an existing document."""
    result = await db.execute(select(Document).where(Document.id == doc_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    doc.processing_status = ProcessingStatus.QUEUED.value
    doc.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(doc)

    trigger_document_processing(str(doc.id), background_tasks=background_tasks)
    return DocumentResponse.model_validate(doc)


@router.post("/admin/documents/reindex-all")
async def reindex_all_documents(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_role(UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Reindex all active documents across all regions (e.g. following embedding model upgrade)."""
    result = await db.execute(
        select(Document).where(Document.status == DocumentStatus.ACTIVE.value)
    )
    docs = result.scalars().all()
    for doc in docs:
        doc.processing_status = ProcessingStatus.QUEUED.value
        trigger_document_processing(str(doc.id), background_tasks=background_tasks)

    await db.commit()
    return {"message": f"Queued {len(docs)} active documents for reindexing."}

