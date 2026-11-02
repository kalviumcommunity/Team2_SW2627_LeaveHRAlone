import io
import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Document, DocumentChunk, DocumentStatus, ProcessingStatus
from app.rag.ingestion.pipeline import async_process_document


@pytest.mark.asyncio
async def test_document_lifecycle_and_admin_api(client: AsyncClient, db_session: AsyncSession):
    # 1. Register HR_ADMIN
    admin_res = await client.post(
        "/api/auth/register",
        json={
            "name": "HR Director",
            "email": "hr.director@example.com",
            "password": "Password123!",
            "role": "HR_ADMIN",
            "region": "India",
            "country": "India",
        },
    )
    admin_token = admin_res.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 2. Register EMPLOYEE
    emp_res = await client.post(
        "/api/auth/register",
        json={
            "name": "Employee Joe",
            "email": "joe@example.com",
            "password": "Password123!",
            "role": "EMPLOYEE",
            "region": "India",
            "country": "India",
        },
    )
    emp_token = emp_res.json()["access_token"]
    emp_headers = {"Authorization": f"Bearer {emp_token}"}

    # 3. Employee trying to upload should get 403 Forbidden
    fake_file = io.BytesIO(b"Company policy text")
    forbidden_res = await client.post(
        "/api/admin/documents",
        files={"file": ("test.txt", fake_file, "text/plain")},
        data={
            "title": "Employee Handbook",
            "category": "Handbook",
            "region": "India",
            "effective_date": "2026-01-01",
        },
        headers=emp_headers,
    )
    assert forbidden_res.status_code == 403

    # 4. HR Admin uploads a valid policy document (v1.0)
    policy_content = (
        "# India Annual Leave Policy\n"
        "All regular full-time employees are eligible for 24 paid leaves per year.\n"
        "Unused leave up to 10 days can be carried forward.\n"
    ).encode("utf-8")

    upload_res = await client.post(
        "/api/admin/documents",
        files={"file": ("india_leave_policy.txt", io.BytesIO(policy_content), "text/plain")},
        data={
            "title": "India Annual Leave Policy",
            "category": "Leave",
            "region": "India",
            "version": "1.0",
            "effective_date": "2026-01-01",
        },
        headers=admin_headers,
    )
    assert upload_res.status_code == 201
    doc_data = upload_res.json()
    doc_id = doc_data["id"]
    assert doc_data["title"] == "India Annual Leave Policy"
    assert doc_data["processing_status"] in ["queued", "processing", "ready"]

    # 5. Process document asynchronously and verify chunks in DB
    success = await async_process_document(doc_id, db_session=db_session)
    assert success is True

    # 6. Inspect chunks via admin endpoint
    chunks_res = await client.get(
        f"/api/admin/documents/{doc_id}/chunks",
        headers=admin_headers,
    )
    assert chunks_res.status_code == 200
    chunks = chunks_res.json()
    assert len(chunks) >= 1
    assert "24 paid leaves" in chunks[0]["chunk_text"]
    assert chunks[0]["token_count"] > 0

    # 7. Upload a new version (v2.0) of the SAME document
    v2_content = (
        "# India Annual Leave Policy\n"
        "Updated version: Full-time employees are eligible for 26 paid leaves per year.\n"
    ).encode("utf-8")

    upload_v2_res = await client.post(
        "/api/admin/documents",
        files={"file": ("india_leave_policy_v2.txt", io.BytesIO(v2_content), "text/plain")},
        data={
            "title": "India Annual Leave Policy",
            "category": "Leave",
            "region": "India",
            "version": "2.0",
            "effective_date": "2026-06-01",
        },
        headers=admin_headers,
    )
    assert upload_v2_res.status_code == 201
    v2_doc_id = upload_v2_res.json()["id"]

    # Process v2
    await async_process_document(v2_doc_id, db_session=db_session)

    # 8. Verify older version (v1.0) was automatically deactivated!
    v1_check = await client.get(f"/api/admin/documents/{doc_id}", headers=admin_headers)
    assert v1_check.json()["status"] == DocumentStatus.INACTIVE.value

    v2_check = await client.get(f"/api/admin/documents/{v2_doc_id}", headers=admin_headers)
    assert v2_check.json()["status"] == DocumentStatus.ACTIVE.value

    # 9. Verify Employee Knowledge Library only returns active documents for India
    lib_res = await client.get("/api/documents/library", headers=emp_headers)
    assert lib_res.status_code == 200
    library_docs = lib_res.json()
    # Should include v2.0 but NOT inactive v1.0
    active_ids = [d["id"] for d in library_docs]
    assert v2_doc_id in active_ids
    assert doc_id not in active_ids

    # 10. Delete v1 document
    del_res = await client.delete(f"/api/admin/documents/{doc_id}", headers=admin_headers)
    assert del_res.status_code == 200

    not_found = await client.get(f"/api/admin/documents/{doc_id}", headers=admin_headers)
    assert not_found.status_code == 404
