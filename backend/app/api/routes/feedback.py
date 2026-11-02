import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.models import AuditLog, Feedback, Message, User
from app.db.session import get_db
from app.schemas.feedback import FeedbackCreate, FeedbackResponse

router = APIRouter(prefix="/feedback", tags=["Feedback"])


@router.post("", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
async def submit_feedback(
    payload: FeedbackCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Submit user feedback (helpful / not helpful) on an AI response message."""
    # Verify message exists
    msg_query = await db.execute(select(Message).where(Message.id == payload.message_id))
    message = msg_query.scalar_one_or_none()
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Message with id {payload.message_id} not found.",
        )

    # Check if feedback already exists for this message
    existing_query = await db.execute(
        select(Feedback).where(Feedback.message_id == payload.message_id)
    )
    existing = existing_query.scalar_one_or_none()
    if existing:
        # Update existing feedback
        existing.rating = payload.rating
        existing.reason = payload.reason
        existing.comment = payload.comment
        await db.commit()
        await db.refresh(existing)
        return existing

    feedback = Feedback(
        id=uuid.uuid4(),
        message_id=payload.message_id,
        user_id=current_user.id,
        rating=payload.rating,
        reason=payload.reason,
        comment=payload.comment,
        created_at=datetime.now(timezone.utc),
    )
    db.add(feedback)

    audit = AuditLog(
        id=uuid.uuid4(),
        user_id=current_user.id,
        action="submit_feedback",
        resource_type="feedback",
        resource_id=str(feedback.id),
        details={"rating": payload.rating, "reason": payload.reason},
        created_at=datetime.now(timezone.utc),
    )
    db.add(audit)

    await db.commit()
    await db.refresh(feedback)
    return feedback
