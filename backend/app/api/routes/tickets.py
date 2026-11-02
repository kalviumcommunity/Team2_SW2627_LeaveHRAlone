import uuid
from datetime import datetime, timezone
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin_user, get_current_user
from app.db.models import AuditLog, Conversation, HRTicket, TicketStatus, User
from app.db.session import get_db
from app.schemas.ticket import TicketCreate, TicketResponse, TicketUpdate

router = APIRouter(tags=["HR Tickets"])


@router.post("/tickets", response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
async def create_ticket(
    payload: TicketCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Employee escalates an unresolvable or low-confidence policy question to HR."""
    # Verify conversation if provided
    if payload.conversation_id:
        conv_query = await db.execute(
            select(Conversation).where(
                Conversation.id == payload.conversation_id,
                Conversation.user_id == current_user.id,
            )
        )
        if not conv_query.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found or access denied.",
            )

    ticket = HRTicket(
        id=uuid.uuid4(),
        user_id=current_user.id,
        conversation_id=payload.conversation_id,
        question=payload.question,
        status=TicketStatus.OPEN.value,
        priority=payload.priority or "medium",
        confidence=payload.confidence or "low",
        retrieved_sources=payload.retrieved_sources,
        created_at=datetime.now(timezone.utc),
    )
    db.add(ticket)

    audit = AuditLog(
        id=uuid.uuid4(),
        user_id=current_user.id,
        action="create_ticket",
        resource_type="ticket",
        resource_id=str(ticket.id),
        details={"question": payload.question[:100], "priority": payload.priority},
        created_at=datetime.now(timezone.utc),
    )
    db.add(audit)

    await db.commit()
    await db.refresh(ticket)
    return ticket


@router.get("/admin/tickets", response_model=List[TicketResponse])
async def list_tickets(
    status_filter: Optional[str] = Query(None, alias="status"),
    priority: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """HR admin lists and filters escalated employee policy tickets."""
    query = select(HRTicket)
    if status_filter:
        query = query.where(HRTicket.status == status_filter)
    if priority:
        query = query.where(HRTicket.priority == priority)

    query = query.order_by(desc(HRTicket.created_at)).offset(offset).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.put("/admin/tickets/{ticket_id}", response_model=TicketResponse)
async def update_ticket(
    ticket_id: uuid.UUID,
    payload: TicketUpdate,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """HR admin updates ticket status, notes, or assigns the ticket."""
    query = await db.execute(select(HRTicket).where(HRTicket.id == ticket_id))
    ticket = query.scalar_one_or_none()
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket {ticket_id} not found.",
        )

    if payload.status:
        ticket.status = payload.status
        if payload.status in [TicketStatus.RESOLVED.value, TicketStatus.CLOSED.value]:
            ticket.resolved_at = datetime.now(timezone.utc)
    if payload.priority:
        ticket.priority = payload.priority
    if payload.assigned_to:
        ticket.assigned_to = payload.assigned_to
    if payload.resolution_notes is not None:
        ticket.resolution_notes = payload.resolution_notes

    audit = AuditLog(
        id=uuid.uuid4(),
        user_id=current_admin.id,
        action="update_ticket",
        resource_type="ticket",
        resource_id=str(ticket.id),
        details={"status": ticket.status, "notes": payload.resolution_notes},
        created_at=datetime.now(timezone.utc),
    )
    db.add(audit)

    await db.commit()
    await db.refresh(ticket)
    return ticket


@router.get("/tickets/my-tickets", response_model=List[TicketResponse])
async def get_my_tickets(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Retrieve all escalated tickets filed by the currently logged-in employee."""
    query = (
        select(HRTicket)
        .where(HRTicket.user_id == current_user.id)
        .order_by(desc(HRTicket.created_at))
    )
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/admin/tickets/{ticket_id}/reply", response_model=TicketResponse)
async def reply_ticket(
    ticket_id: uuid.UUID,
    payload: dict[str, Any],
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """HR admin sends direct answer/resolution to an employee ticket."""
    query = await db.execute(select(HRTicket).where(HRTicket.id == ticket_id))
    ticket = query.scalar_one_or_none()
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket {ticket_id} not found.",
        )

    reply_text = payload.get("reply", "").strip()
    if not reply_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reply text cannot be empty.",
        )

    new_status = payload.get("status", TicketStatus.RESOLVED.value)
    ticket.resolution_notes = reply_text
    ticket.status = new_status
    ticket.assigned_to = current_admin.id
    if new_status in [TicketStatus.RESOLVED.value, TicketStatus.CLOSED.value]:
        ticket.resolved_at = datetime.now(timezone.utc)

    audit = AuditLog(
        id=uuid.uuid4(),
        user_id=current_admin.id,
        action="reply_ticket",
        resource_type="ticket",
        resource_id=str(ticket.id),
        details={"reply": reply_text[:200], "status": new_status},
        created_at=datetime.now(timezone.utc),
    )
    db.add(audit)

    await db.commit()
    await db.refresh(ticket)
    return ticket


@router.post("/admin/tickets/{ticket_id}/faq-draft")
async def convert_ticket_to_faq(
    ticket_id: uuid.UUID,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Convert a resolved ticket into a suggested draft FAQ item for HR policy handbooks."""
    query = await db.execute(select(HRTicket).where(HRTicket.id == ticket_id))
    ticket = query.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    return {
        "question": ticket.question,
        "suggested_answer": ticket.resolution_notes or "Under review by HR.",
        "category": "General",
        "region": "Global",
        "created_from_ticket": str(ticket.id),
    }

