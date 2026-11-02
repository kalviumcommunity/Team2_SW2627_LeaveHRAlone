import uuid
import pytest
from httpx import AsyncClient

from app.core.security import create_access_token, get_password_hash
from app.db.models import Conversation, Message, User, UserRole


@pytest.mark.asyncio
async def test_feedback_and_tickets_and_analytics_flow(client: AsyncClient, db_session):
    # 1. Create Employee and Admin users
    emp_user = User(
        id=uuid.uuid4(),
        email="emp.test@example.com",
        name="Employee Test",
        password_hash=get_password_hash("password123"),
        role=UserRole.EMPLOYEE.value,
        region="India",
        country="India",
        employment_type="Full-Time",
    )
    admin_user = User(
        id=uuid.uuid4(),
        email="admin.test@example.com",
        name="Admin Test",
        password_hash=get_password_hash("password123"),
        role=UserRole.HR_ADMIN.value,
        region="India",
        country="India",
        employment_type="Full-Time",
    )
    db_session.add(emp_user)
    db_session.add(admin_user)
    await db_session.commit()

    emp_token = create_access_token(data={"sub": str(emp_user.id), "role": emp_user.role, "email": emp_user.email})
    admin_token = create_access_token(data={"sub": str(admin_user.id), "role": admin_user.role, "email": admin_user.email})
    emp_headers = {"Authorization": f"Bearer {emp_token}"}
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 2. Create conversation and message
    conv = Conversation(
        id=uuid.uuid4(),
        user_id=emp_user.id,
        title="Leave Question",
        region_snapshot="India",
    )
    db_session.add(conv)
    await db_session.flush()

    user_msg = Message(
        id=uuid.uuid4(),
        conversation_id=conv.id,
        role="user",
        content="How many days of annual leave do I get?",
        confidence="none",
    )
    asst_msg = Message(
        id=uuid.uuid4(),
        conversation_id=conv.id,
        role="assistant",
        content="Employees in India receive 24 days of annual leave.",
        confidence="high",
    )
    db_session.add(user_msg)
    db_session.add(asst_msg)
    await db_session.commit()

    # 3. Test Feedback API
    fb_resp = await client.post(
        "/api/feedback",
        json={
            "message_id": str(asst_msg.id),
            "rating": True,
            "comment": "Very accurate and quick!",
        },
        headers=emp_headers,
    )
    assert fb_resp.status_code == 201
    fb_data = fb_resp.json()
    assert fb_data["rating"] is True

    # 4. Test Ticket Creation (Escalation)
    ticket_resp = await client.post(
        "/api/tickets",
        json={
            "question": "Can I get an exception for sabbatical leave?",
            "conversation_id": str(conv.id),
            "confidence": "low",
            "priority": "high",
        },
        headers=emp_headers,
    )
    assert ticket_resp.status_code == 201
    ticket_data = ticket_resp.json()
    ticket_id = ticket_data["id"]
    assert ticket_data["status"] == "open"
    assert ticket_data["priority"] == "high"

    # 5. Test HR Admin List Tickets
    list_resp = await client.get("/api/admin/tickets", headers=admin_headers)
    assert list_resp.status_code == 200
    tickets = list_resp.json()
    assert len(tickets) >= 1
    assert any(t["id"] == ticket_id for t in tickets)

    # 6. Test HR Admin Update Ticket
    up_resp = await client.put(
        f"/api/admin/tickets/{ticket_id}",
        json={
            "status": "resolved",
            "resolution_notes": "Sabbatical policy exception granted as per VP approval.",
        },
        headers=admin_headers,
    )
    assert up_resp.status_code == 200
    assert up_resp.json()["status"] == "resolved"

    # 7. Test Admin Analytics Endpoints
    overview_resp = await client.get("/api/admin/analytics/overview", headers=admin_headers)
    assert overview_resp.status_code == 200
    overview = overview_resp.json()
    assert overview["total_questions"] >= 1
    assert overview["escalated_questions"] >= 1

    topics_resp = await client.get("/api/admin/analytics/topics", headers=admin_headers)
    assert topics_resp.status_code == 200
    topics = topics_resp.json()
    assert isinstance(topics, list)
    assert any(t["topic"] == "Leave & Time Off" for t in topics)

    fb_stat_resp = await client.get("/api/admin/analytics/feedback", headers=admin_headers)
    assert fb_stat_resp.status_code == 200
    fb_stats = fb_stat_resp.json()
    assert fb_stats["total_feedback"] >= 1
    assert fb_stats["positive_count"] >= 1
