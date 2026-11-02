import uuid
from datetime import date
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    AuditLog,
    Citation,
    ConfidenceLevel,
    Conversation,
    Document,
    DocumentChunk,
    DocumentStatus,
    Feedback,
    HRTicket,
    Message,
    MessageRole,
    ProcessingStatus,
    TicketPriority,
    TicketStatus,
    User,
    UserRole,
)


@pytest.mark.asyncio
async def test_complete_database_schema_and_relationships(db_session: AsyncSession):
    # 1. Create User
    user = User(
        id=uuid.uuid4(),
        name="HR Specialist",
        email="specialist@company.com",
        password_hash="hashed_pw",
        role=UserRole.HR_ADMIN.value,
        region="India",
        country="India",
        department="Human Resources",
        employment_type="Full-Time",
    )
    db_session.add(user)
    await db_session.flush()

    # 2. Create Document
    doc = Document(
        id=uuid.uuid4(),
        title="India Leave Policy 2026",
        category="Leave",
        region="India",
        employee_type="All",
        version="2026.1",
        effective_date=date(2026, 1, 1),
        status=DocumentStatus.ACTIVE.value,
        file_path="/storage/policies/india_leave_2026.pdf",
        file_type="pdf",
        file_size_bytes=102400,
        processing_status=ProcessingStatus.READY.value,
        uploaded_by=user.id,
    )
    db_session.add(doc)
    await db_session.flush()

    # 3. Create DocumentChunk
    chunk = DocumentChunk(
        id=uuid.uuid4(),
        document_id=doc.id,
        chunk_index=0,
        chunk_text="Employees in India are entitled to 24 annual paid leaves.",
        page_number=4,
        section="4.2 Annual Leave",
        token_count=18,
        embedding_id="qdrant-vec-001",
        chunk_metadata={"region": "India", "category": "Leave"},
    )
    db_session.add(chunk)
    await db_session.flush()

    # 4. Create Conversation
    conv = Conversation(
        id=uuid.uuid4(),
        user_id=user.id,
        title="Leave policy inquiry",
        region_snapshot="India",
    )
    db_session.add(conv)
    await db_session.flush()

    # 5. Create Message
    msg = Message(
        id=uuid.uuid4(),
        conversation_id=conv.id,
        role=MessageRole.ASSISTANT.value,
        content="You are entitled to 24 annual paid leaves.",
        confidence=ConfidenceLevel.HIGH.value,
    )
    db_session.add(msg)
    await db_session.flush()

    # 6. Create Citation
    citation = Citation(
        id=uuid.uuid4(),
        message_id=msg.id,
        document_id=doc.id,
        chunk_id=chunk.id,
        document_title=doc.title,
        version=doc.version,
        page_number=4,
        section="4.2 Annual Leave",
        similarity_score=0.92,
    )
    db_session.add(citation)

    # 7. Create Feedback
    fb = Feedback(
        id=uuid.uuid4(),
        message_id=msg.id,
        user_id=user.id,
        rating=True,
        comment="Very clear and accurate citation.",
    )
    db_session.add(fb)

    # 8. Create HRTicket
    ticket = HRTicket(
        id=uuid.uuid4(),
        user_id=user.id,
        conversation_id=conv.id,
        question="Can I take all 24 leaves consecutively?",
        status=TicketStatus.OPEN.value,
        priority=TicketPriority.MEDIUM.value,
        confidence="medium",
    )
    db_session.add(ticket)

    # 9. Create AuditLog
    log = AuditLog(
        id=uuid.uuid4(),
        user_id=user.id,
        action="DOCUMENT_UPLOAD",
        resource_type="document",
        resource_id=str(doc.id),
        details={"title": doc.title, "region": "India"},
        ip_address="127.0.0.1",
    )
    db_session.add(log)

    await db_session.commit()

    # Verify query and relationships
    q_doc = await db_session.execute(select(Document).where(Document.id == doc.id))
    retrieved_doc = q_doc.scalar_one()
    assert retrieved_doc.title == "India Leave Policy 2026"
    assert len(retrieved_doc.chunks) == 1
    assert retrieved_doc.chunks[0].chunk_text.startswith("Employees in India")

    q_user = await db_session.execute(select(User).where(User.id == user.id))
    retrieved_user = q_user.scalar_one()
    assert retrieved_user.email == "specialist@company.com"
    assert len(retrieved_user.conversations) == 1
    assert retrieved_user.conversations[0].messages[0].content.startswith("You are entitled")
