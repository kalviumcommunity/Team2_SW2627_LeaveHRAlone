"""
LeaveHRAlone AI — Database & Vector DB Seed Script
Seeds:
- Demo Users (Employee India, Employee US, HR Admin, Super Admin)
- Sample Policy Documents (India, US, Global with active/expired and v1/v2 pairs)
- Processes all documents into Qdrant vector database
"""
import asyncio
import os
import sys
import uuid
from datetime import date, datetime, timezone
from pathlib import Path

# Safe utf-8 output on Windows terminal
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Ensure backend root is in sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import select
from app.core.security import get_password_hash
from app.db.models import Document, DocumentStatus, ProcessingStatus, User, UserRole
from app.db.session import AsyncSessionLocal
from app.rag.ingestion.pipeline import async_process_document


SAMPLE_USERS = [
    {
        "name": "Aarav Sharma",
        "email": "employee.india@example.com",
        "password": "password123",
        "role": UserRole.EMPLOYEE.value,
        "region": "India",
        "country": "India",
        "department": "Engineering",
        "employment_type": "Full-Time",
    },
    {
        "name": "Sarah Jenkins",
        "email": "employee.us@example.com",
        "password": "password123",
        "role": UserRole.EMPLOYEE.value,
        "region": "US",
        "country": "United States",
        "department": "Product",
        "employment_type": "Full-Time",
    },
    {
        "name": "Priya Nair",
        "email": "hr.admin@example.com",
        "password": "password123",
        "role": UserRole.HR_ADMIN.value,
        "region": "India",
        "country": "India",
        "department": "Human Resources",
        "employment_type": "Full-Time",
    },
    {
        "name": "Alex Vance",
        "email": "super.admin@example.com",
        "password": "password123",
        "role": UserRole.SUPER_ADMIN.value,
        "region": "Global",
        "country": "United States",
        "department": "Executive",
        "employment_type": "Full-Time",
    },
]

POLICIES = [
    {
        "filename": "India_Leave_Policy_2026_v2.0.txt",
        "title": "India Leave Policy",
        "category": "Leave",
        "region": "India",
        "version": "2026.1",
        "status": DocumentStatus.ACTIVE.value,
        "effective_date": date(2026, 1, 1),
        "expiration_date": None,
    },
    {
        "filename": "India_Leave_Policy_2025_v1.0.txt",
        "title": "India Leave Policy (Superseded)",
        "category": "Leave",
        "region": "India",
        "version": "2025.1",
        "status": DocumentStatus.INACTIVE.value,
        "effective_date": date(2025, 1, 1),
        "expiration_date": date(2025, 12, 31),
    },
    {
        "filename": "India_Benefits_and_Insurance_2026.txt",
        "title": "India Benefits & Group Medical Insurance",
        "category": "Benefits & Insurance",
        "region": "India",
        "version": "2026.1",
        "status": DocumentStatus.ACTIVE.value,
        "effective_date": date(2026, 1, 1),
        "expiration_date": None,
    },
    {
        "filename": "US_Employee_Handbook_2026_v1.0.txt",
        "title": "US Employee Handbook & PTO Policy",
        "category": "Employee Handbook",
        "region": "US",
        "version": "2026.1",
        "status": DocumentStatus.ACTIVE.value,
        "effective_date": date(2026, 1, 1),
        "expiration_date": None,
    },
    {
        "filename": "US_Remote_Work_Policy_Expired_2024.txt",
        "title": "US Remote Work Guidelines (Expired)",
        "category": "Remote Work",
        "region": "US",
        "version": "2024.1",
        "status": DocumentStatus.INACTIVE.value,
        "effective_date": date(2024, 1, 1),
        "expiration_date": date(2024, 12, 31),
    },
    {
        "filename": "Global_Code_of_Conduct_2026.txt",
        "title": "Global Workplace Code of Conduct",
        "category": "Workplace Policies",
        "region": "Global",
        "version": "2026.1",
        "status": DocumentStatus.ACTIVE.value,
        "effective_date": date(2026, 1, 1),
        "expiration_date": None,
    },
]


async def seed() -> None:
    print("🌱 Starting LeaveHRAlone AI database and vector seeding...")
    policies_dir = backend_dir / "data" / "sample_policies"

    async with AsyncSessionLocal() as session:
        # 1. Seed Users
        admin_user_id = None
        for u_data in SAMPLE_USERS:
            res = await session.execute(select(User).where(User.email == u_data["email"]))
            existing = res.scalar_one_or_none()
            if not existing:
                user = User(
                    id=uuid.uuid4(),
                    name=u_data["name"],
                    email=u_data["email"],
                    password_hash=get_password_hash(u_data["password"]),
                    role=u_data["role"],
                    region=u_data["region"],
                    country=u_data["country"],
                    department=u_data.get("department"),
                    employment_type=u_data.get("employment_type", "Full-Time"),
                )
                session.add(user)
                await session.flush()
                print(f"  ✓ Created user: {u_data['email']} ({u_data['role']})")
                if u_data["role"] == UserRole.HR_ADMIN.value:
                    admin_user_id = user.id
            else:
                if u_data["role"] == UserRole.HR_ADMIN.value:
                    admin_user_id = existing.id
                print(f"  - User exists: {u_data['email']}")

        await session.commit()

        # 2. Seed Policy Documents
        for p in POLICIES:
            file_path = policies_dir / p["filename"]
            if not file_path.exists():
                print(f"  ⚠️ Policy file not found: {file_path}")
                continue

            file_size = os.path.getsize(file_path)

            res = await session.execute(select(Document).where(Document.title == p["title"]))
            doc = res.scalar_one_or_none()
            if not doc:
                doc = Document(
                    id=uuid.uuid4(),
                    title=p["title"],
                    category=p["category"],
                    region=p["region"],
                    version=p["version"],
                    effective_date=p["effective_date"],
                    expiration_date=p["expiration_date"],
                    status=p["status"],
                    file_path=str(file_path),
                    file_type="txt",
                    file_size_bytes=file_size,
                    processing_status=ProcessingStatus.QUEUED.value,
                    uploaded_by=admin_user_id,
                )
                session.add(doc)
                await session.commit()
                print(f"  ✓ Registered policy document: {p['title']} [{p['region']}]")
            else:
                print(f"  - Document exists: {p['title']}")

            # Ingest into vector DB
            print(f"    Indexing {p['title']}...")
            success = await async_process_document(doc.id, db_session=session)
            if success:
                print(f"    ✓ Successfully indexed {p['title']}")
            else:
                print(f"    ✗ Failed to index {p['title']}")

    print("\n✅ Seeding complete!")


if __name__ == "__main__":
    if "--demo" not in sys.argv:
        print("⚠️  Notice: seed.py is for loading demonstration data only.")
        print("To seed demo data, explicitly pass the --demo flag:")
        print("   python scripts/seed.py --demo")
        print("\nFor production bootstrap (creating admin without fake data), use:")
        print("   python scripts/bootstrap.py")
        sys.exit(1)

    asyncio.run(seed())
