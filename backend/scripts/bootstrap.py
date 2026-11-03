"""
LeaveHRAlone AI — Clean Production Bootstrap Script
Creates initial SUPER_ADMIN / HR_ADMIN user from environment variables.
Does NOT create any demo documents, policies, or mock data.
Usage:
    python scripts/bootstrap.py
    # or with custom env vars:
    ADMIN_EMAIL="admin@company.com" ADMIN_PASSWORD="SecurePassword123!" python scripts/bootstrap.py
"""
import asyncio
import os
import sys
import uuid
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
from app.db.models import User, UserRole
from app.db.session import AsyncSessionLocal


async def bootstrap():
    admin_email = os.getenv("ADMIN_EMAIL", "admin@leavehralone.ai").strip()
    admin_password = os.getenv("ADMIN_PASSWORD", "AdminPass123!").strip()
    admin_name = os.getenv("ADMIN_NAME", "System Administrator").strip()
    admin_region = os.getenv("ADMIN_REGION", "Global").strip()
    admin_country = os.getenv("ADMIN_COUNTRY", "Global").strip()
    admin_department = os.getenv("ADMIN_DEPARTMENT", "HR & Operations").strip()

    print("🚀 Initializing LeaveHRAlone AI Production Bootstrap...")
    print(f"Target Admin: {admin_email} [{admin_region}]")

    async with AsyncSessionLocal() as session:
        res = await session.execute(select(User).where(User.email == admin_email))
        user = res.scalar_one_or_none()

        if user:
            print(f"ℹ️  Admin user '{admin_email}' already exists. Updating credentials & role...")
            user.role = UserRole.SUPER_ADMIN.value
            user.password_hash = get_password_hash(admin_password)
            user.region = admin_region
            user.country = admin_country
            user.department = admin_department
            await session.commit()
            print(f"✓ Admin account updated successfully.")
        else:
            new_admin = User(
                id=uuid.uuid4(),
                name=admin_name,
                email=admin_email,
                password_hash=get_password_hash(admin_password),
                role=UserRole.SUPER_ADMIN.value,
                region=admin_region,
                country=admin_country,
                department=admin_department,
                employment_type="Full-Time",
            )
            session.add(new_admin)
            await session.commit()
            print(f"✓ Super Admin created: {admin_email} (Role: SUPER_ADMIN)")

    print("\n✅ Bootstrap completed successfully!")
    print(f"   Email: {admin_email}")
    print("   Ready for live document uploads and employee onboarding.")


if __name__ == "__main__":
    asyncio.run(bootstrap())
