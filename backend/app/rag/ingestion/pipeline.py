import logging
import uuid
from typing import Any, List, Optional
from datetime import datetime, timezone

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.db.models import Document, DocumentChunk, DocumentStatus, ProcessingStatus
from app.db.session import AsyncSessionLocal, SyncSessionLocal
from app.rag.embeddings import get_embedding_provider
from app.rag.processing import clean_text, chunk_text, extract_document
from app.rag.vector_db import vector_db

logger = logging.getLogger(__name__)


async def async_process_document(
    document_id: str | uuid.UUID,
    db_session: Optional[AsyncSession] = None,
) -> bool:
    """Asynchronous document processing pipeline for FastAPI and tests."""
    doc_uuid = uuid.UUID(str(document_id))
    session = db_session or AsyncSessionLocal()
    should_close = db_session is None

    try:
        res = await session.execute(select(Document).where(Document.id == doc_uuid))
        doc = res.scalar_one_or_none()
        if not doc:
            logger.error("Document not found: %s", document_id)
            return False

        # 1. Update status to PROCESSING
        doc.processing_status = ProcessingStatus.PROCESSING.value
        doc.error_message = None
        await session.commit()

        # 2. Extract content page by page
        pages = extract_document(doc.file_path, doc.file_type)
        if not pages:
            raise ValueError("No text could be extracted from document.")

        all_chunks = []
        chunk_idx = 0

        # 3. Clean and token-aware chunk each page
        for page in pages:
            cleaned = clean_text(page.text)
            if not cleaned:
                continue

            chunks = chunk_text(
                cleaned,
                page_number=page.page_number,
                section=page.section,
            )
            for ch in chunks:
                ch.chunk_index = chunk_idx
                chunk_idx += 1
                all_chunks.append(ch)

        if not all_chunks:
            raise ValueError("Document cleaning and chunking resulted in empty content.")

        # 4. Generate embeddings in batch
        texts_to_embed = [ch.text for ch in all_chunks]
        embedder = get_embedding_provider()
        embeddings = embedder.embed_batch(texts_to_embed)

        # 5. Clean prior chunks in Qdrant & Postgres
        vector_db.delete_by_document_id(str(doc.id))
        await session.execute(delete(DocumentChunk).where(DocumentChunk.document_id == doc.id))

        qdrant_points = []
        db_chunks = []

        for ch, emb in zip(all_chunks, embeddings):
            chunk_uuid = uuid.uuid4()
            embedding_id = str(chunk_uuid)

            payload = {
                "document_id": str(doc.id),
                "document_title": doc.title,
                "region": doc.region,
                "category": doc.category,
                "employee_type": doc.employee_type or "All",
                "version": doc.version,
                "page_number": ch.page_number,
                "section": ch.section,
                "effective_date": doc.effective_date.isoformat(),
                "expiration_date": doc.expiration_date.isoformat() if doc.expiration_date else None,
                "status": doc.status,
                "chunk_text": ch.text,
            }

            qdrant_points.append({
                "id": embedding_id,
                "vector": emb,
                "payload": payload,
            })

            db_chunks.append(
                DocumentChunk(
                    id=chunk_uuid,
                    document_id=doc.id,
                    chunk_index=ch.chunk_index,
                    chunk_text=ch.text,
                    page_number=ch.page_number,
                    section=ch.section,
                    token_count=ch.token_count,
                    embedding_id=embedding_id,
                    chunk_metadata=payload,
                )
            )

        # 6. Upsert to Qdrant
        vector_db.upsert_chunks(qdrant_points)

        # 7. Save chunks to DB
        session.add_all(db_chunks)

        # 8. Version Management: Deactivate older active versions
        if doc.status == DocumentStatus.ACTIVE.value:
            superseded_res = await session.execute(
                select(Document).where(
                    Document.title == doc.title,
                    Document.region == doc.region,
                    Document.category == doc.category,
                    Document.id != doc.id,
                    Document.status == DocumentStatus.ACTIVE.value,
                )
            )
            superseded_docs = superseded_res.scalars().all()

            for old_doc in superseded_docs:
                old_doc.status = DocumentStatus.INACTIVE.value
                vector_db.set_document_status(str(old_doc.id), DocumentStatus.INACTIVE.value)
                logger.info(
                    "Deactivated older version %s of document '%s' (region: %s)",
                    old_doc.version,
                    old_doc.title,
                    old_doc.region,
                )

        # 9. Mark READY
        doc.processing_status = ProcessingStatus.READY.value
        doc.updated_at = datetime.now(timezone.utc)
        await session.commit()
        logger.info("Successfully processed document async: %s (%d chunks)", doc.title, len(db_chunks))
        return True

    except Exception as e:
        logger.exception("Failed to process document async %s: %s", document_id, e)
        await session.rollback()
        try:
            res = await session.execute(select(Document).where(Document.id == doc_uuid))
            doc = res.scalar_one_or_none()
            if doc:
                doc.processing_status = ProcessingStatus.FAILED.value
                doc.error_message = str(e)
                await session.commit()
        except Exception:
            pass
        return False
    finally:
        if should_close:
            await session.close()


def process_document_sync(document_id: str | uuid.UUID, db_session: Optional[Session] = None) -> bool:
    """Full synchronous document processing pipeline with database and Qdrant updates."""
    doc_uuid = uuid.UUID(str(document_id))
    session = db_session or SyncSessionLocal()
    should_close = db_session is None

    try:
        doc = session.execute(select(Document).where(Document.id == doc_uuid)).scalar_one_or_none()
        if not doc:
            logger.error("Document not found: %s", document_id)
            return False

        doc.processing_status = ProcessingStatus.PROCESSING.value
        doc.error_message = None
        session.commit()

        pages = extract_document(doc.file_path, doc.file_type)
        if not pages:
            raise ValueError("No text could be extracted from document.")

        all_chunks = []
        chunk_idx = 0

        for page in pages:
            cleaned = clean_text(page.text)
            if not cleaned:
                continue

            chunks = chunk_text(
                cleaned,
                page_number=page.page_number,
                section=page.section,
            )
            for ch in chunks:
                ch.chunk_index = chunk_idx
                chunk_idx += 1
                all_chunks.append(ch)

        if not all_chunks:
            raise ValueError("Document cleaning and chunking resulted in empty content.")

        texts_to_embed = [ch.text for ch in all_chunks]
        embedder = get_embedding_provider()
        embeddings = embedder.embed_batch(texts_to_embed)

        qdrant_points = []
        db_chunks = []

        vector_db.delete_by_document_id(str(doc.id))
        session.execute(delete(DocumentChunk).where(DocumentChunk.document_id == doc.id))

        for ch, emb in zip(all_chunks, embeddings):
            chunk_uuid = uuid.uuid4()
            embedding_id = str(chunk_uuid)

            payload = {
                "document_id": str(doc.id),
                "document_title": doc.title,
                "region": doc.region,
                "category": doc.category,
                "employee_type": doc.employee_type or "All",
                "version": doc.version,
                "page_number": ch.page_number,
                "section": ch.section,
                "effective_date": doc.effective_date.isoformat(),
                "expiration_date": doc.expiration_date.isoformat() if doc.expiration_date else None,
                "status": doc.status,
                "chunk_text": ch.text,
            }

            qdrant_points.append({
                "id": embedding_id,
                "vector": emb,
                "payload": payload,
            })

            db_chunks.append(
                DocumentChunk(
                    id=chunk_uuid,
                    document_id=doc.id,
                    chunk_index=ch.chunk_index,
                    chunk_text=ch.text,
                    page_number=ch.page_number,
                    section=ch.section,
                    token_count=ch.token_count,
                    embedding_id=embedding_id,
                    chunk_metadata=payload,
                )
            )

        vector_db.upsert_chunks(qdrant_points)
        session.add_all(db_chunks)

        if doc.status == DocumentStatus.ACTIVE.value:
            superseded_docs = session.execute(
                select(Document).where(
                    Document.title == doc.title,
                    Document.region == doc.region,
                    Document.category == doc.category,
                    Document.id != doc.id,
                    Document.status == DocumentStatus.ACTIVE.value,
                )
            ).scalars().all()

            for old_doc in superseded_docs:
                old_doc.status = DocumentStatus.INACTIVE.value
                vector_db.set_document_status(str(old_doc.id), DocumentStatus.INACTIVE.value)

        doc.processing_status = ProcessingStatus.READY.value
        doc.updated_at = datetime.now(timezone.utc)
        session.commit()
        return True

    except Exception as e:
        logger.exception("Failed to process document sync %s: %s", document_id, e)
        session.rollback()
        try:
            doc = session.execute(select(Document).where(Document.id == doc_uuid)).scalar_one_or_none()
            if doc:
                doc.processing_status = ProcessingStatus.FAILED.value
                doc.error_message = str(e)
                session.commit()
        except Exception:
            pass
        return False
    finally:
        if should_close:
            session.close()
