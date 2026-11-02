from typing import Any, Dict, List

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin_user
from app.db.models import (
    ConfidenceLevel,
    Conversation,
    Document,
    DocumentStatus,
    Feedback,
    HRTicket,
    Message,
    MessageRole,
    User,
)
from app.db.session import get_db
from app.schemas.analytics import (
    AnalyticsOverview,
    FeedbackStat,
    QuestionStat,
    TopicStat,
    UnansweredQuestionStat,
)

router = APIRouter(prefix="/admin/analytics", tags=["Analytics"])


@router.get("/overview", response_model=AnalyticsOverview)
async def get_analytics_overview(
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """HR Admin overview KPIs as specified in PRD Section 24 & 25."""
    # Total user messages (questions)
    total_q_res = await db.execute(
        select(func.count(Message.id)).where(Message.role == MessageRole.USER.value)
    )
    total_questions = total_q_res.scalar_one() or 0

    # Total tickets (escalated)
    total_tickets_res = await db.execute(select(func.count(HRTicket.id)))
    escalated_questions = total_tickets_res.scalar_one() or 0

    # Low confidence assistant messages
    low_conf_res = await db.execute(
        select(func.count(Message.id)).where(
            Message.role == MessageRole.ASSISTANT.value,
            Message.confidence.in_([ConfidenceLevel.LOW.value, ConfidenceLevel.NONE.value]),
        )
    )
    low_confidence_questions = low_conf_res.scalar_one() or 0

    # Active documents
    docs_res = await db.execute(
        select(func.count(Document.id)).where(Document.status == DocumentStatus.ACTIVE.value)
    )
    active_policies = docs_res.scalar_one() or 0

    # Total users
    users_res = await db.execute(select(func.count(User.id)))
    total_users = users_res.scalar_one() or 0

    # Calculate resolution
    resolved_by_ai = max(total_questions - escalated_questions, 0)
    resolved_pct = round((resolved_by_ai / max(total_questions, 1)) * 100, 1)
    escalated_pct = round((escalated_questions / max(total_questions, 1)) * 100, 1)

    return AnalyticsOverview(
        total_questions=total_questions,
        resolved_by_ai=resolved_by_ai,
        resolved_percentage=resolved_pct,
        escalated_questions=escalated_questions,
        escalated_percentage=escalated_pct,
        low_confidence_questions=low_confidence_questions,
        active_policies=active_policies,
        total_users=total_users,
    )


@router.get("/topics", response_model=List[TopicStat])
async def get_topics_analytics(
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Most asked topics and their distribution."""
    # Fetch user questions
    result = await db.execute(
        select(Message.content).where(Message.role == MessageRole.USER.value)
    )
    questions = result.scalars().all()

    counts = {
        "Leave & Time Off": 0,
        "Benefits & Insurance": 0,
        "Remote Work": 0,
        "Workplace Policies": 0,
        "Payroll & Compensation": 0,
        "General HR": 0,
    }

    for q in questions:
        q_lower = q.lower()
        if any(w in q_lower for w in ["leave", "holiday", "vacation", "pto", "sick", "casual", "maternity", "paternity"]):
            counts["Leave & Time Off"] += 1
        elif any(w in q_lower for w in ["insurance", "benefit", "medical", "health", "dental", "gmc", "stipend"]):
            counts["Benefits & Insurance"] += 1
        elif any(w in q_lower for w in ["remote", "wfh", "work from home", "office"]):
            counts["Remote Work"] += 1
        elif any(w in q_lower for w in ["conduct", "harassment", "whistleblower", "ethics", "dress", "handbook"]):
            counts["Workplace Policies"] += 1
        elif any(w in q_lower for w in ["payroll", "salary", "bonus", "tax", "reimbursement", "pay"]):
            counts["Payroll & Compensation"] += 1
        else:
            counts["General HR"] += 1

    total = max(len(questions), 1)
    topics = []
    for topic, count in sorted(counts.items(), key=lambda x: x[1], reverse=True):
        topics.append(
            TopicStat(
                topic=topic,
                count=count,
                percentage=round((count / total) * 100, 1),
            )
        )
    return topics


@router.get("/questions", response_model=List[QuestionStat])
async def get_questions_analytics(
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Recent employee queries with resolution and escalation status, using real region from DB."""
    result = await db.execute(
        select(Message, User.region)
        .outerjoin(Conversation, Message.conversation_id == Conversation.id)
        .outerjoin(User, Conversation.user_id == User.id)
        .where(Message.role == MessageRole.USER.value)
        .order_by(Message.created_at.desc())
        .limit(20)
    )
    rows = result.all()

    # Get escalated ticket questions to cross-reference
    tickets_res = await db.execute(select(HRTicket.question))
    escalated_questions = set(tickets_res.scalars().all())

    items = []
    for msg, user_region in rows:
        req_hr = msg.content in escalated_questions
        items.append(
            QuestionStat(
                question=msg.content,
                count=1,
                resolved=not req_hr,
                requires_hr=req_hr,
                region=user_region or "Global",
            )
        )
    return items


@router.get("/unanswered", response_model=List[UnansweredQuestionStat])
async def get_unanswered_questions(
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Return low-confidence queries or escalated questions that indicate policy gaps."""
    # 1. Fetch assistant messages with LOW or NONE confidence
    low_conf_query = (
        select(Message, Conversation, User.region)
        .join(Conversation, Message.conversation_id == Conversation.id)
        .join(User, Conversation.user_id == User.id)
        .where(
            Message.role == MessageRole.ASSISTANT.value,
            Message.confidence.in_([ConfidenceLevel.LOW.value, ConfidenceLevel.NONE.value]),
        )
        .order_by(Message.created_at.desc())
        .limit(30)
    )
    res = await db.execute(low_conf_query)
    low_conf_msgs = res.all()

    # Fetch open escalated ticket questions
    tickets_res = await db.execute(
        select(HRTicket).where(HRTicket.status == "open").order_by(HRTicket.created_at.desc())
    )
    open_tickets = tickets_res.scalars().all()
    ticket_map = {t.question: t for t in open_tickets}

    items: List[UnansweredQuestionStat] = []
    seen_questions = set()

    # Add open tickets first
    for t in open_tickets:
        if t.question not in seen_questions:
            seen_questions.add(t.question)
            items.append(
                UnansweredQuestionStat(
                    id=str(t.id),
                    question=t.question,
                    region=getattr(t.creator, "region", "Global") if hasattr(t, "creator") and t.creator else "Global",
                    confidence=t.confidence or "low",
                    created_at=t.created_at.isoformat(),
                    escalated=True,
                )
            )

    # Add low-confidence assistant questions (found via conversation title or user prompt)
    for msg, conv, region in low_conf_msgs:
        question_text = conv.title
        if question_text and question_text not in seen_questions:
            seen_questions.add(question_text)
            items.append(
                UnansweredQuestionStat(
                    id=str(msg.id),
                    question=question_text,
                    region=region or "Global",
                    confidence=msg.confidence or "low",
                    created_at=msg.created_at.isoformat(),
                    escalated=question_text in ticket_map,
                )
            )

    return items


@router.get("/feedback", response_model=FeedbackStat)
async def get_feedback_analytics(
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Feedback counts, satisfaction score, and breakdown by negative reasons."""
    fb_res = await db.execute(select(Feedback))
    feedback_list = fb_res.scalars().all()

    total = len(feedback_list)
    positive = sum(1 for f in feedback_list if f.rating is True)
    negative = sum(1 for f in feedback_list if f.rating is False)

    reasons_breakdown: Dict[str, int] = {
        "Incorrect information": 0,
        "Outdated policy": 0,
        "Not relevant": 0,
        "Missing information": 0,
        "Other": 0,
    }

    for f in feedback_list:
        if not f.rating and f.reason:
            if f.reason in reasons_breakdown:
                reasons_breakdown[f.reason] += 1
            else:
                reasons_breakdown["Other"] += 1

    pos_pct = round((positive / max(total, 1)) * 100, 1)

    return FeedbackStat(
        total_feedback=total,
        positive_count=positive,
        negative_count=negative,
        positive_percentage=pos_pct,
        reasons_breakdown=reasons_breakdown,
    )
