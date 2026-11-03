"""
LeaveHRAlone AI — User Management Route
Provides HR administrators full control over employee rosters:
- List & search users
- Create & edit individual employees
- Bulk CSV import with role, region, department, and country assignment
- Employee invite tokens
"""
import csv
import io
import uuid
from typing import Any, List, Optional
from datetime import datetime, timezone

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_role
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
)
from app.db.models import AuditLog, User, UserRole
from app.db.session import get_db
from app.schemas.user import UserCreate, UserResponse, UserUpdate

router = APIRouter(prefix="/admin/users", tags=["User Management"])


@router.get("", response_model=List[UserResponse])
async def list_users(
    query: Optional[str] = None,
    role: Optional[str] = None,
    region: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_admin: User = Depends(require_role(UserRole.HR_ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """List users with optional search and filters."""
    sql = select(User).order_by(desc(User.created_at)).offset(offset).limit(limit)

    if role:
        sql = sql.where(User.role == role)
    if region:
        sql = sql.where(User.region == region)
    if query:
        search_pattern = f"%{query}%"
        sql = sql.where((User.name.ilike(search_pattern)) | (User.email.ilike(search_pattern)))

    res = await db.execute(sql)
    return [UserResponse.model_validate(u) for u in res.scalars().all()]


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_in: UserCreate,
    current_admin: User = Depends(require_role(UserRole.HR_ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """HR admin creates a new employee or administrator account."""
    existing = await db.execute(select(User).where(User.email == user_in.email))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists.",
        )

    new_user = User(
        id=uuid.uuid4(),
        name=user_in.name,
        email=user_in.email,
        password_hash=get_password_hash(user_in.password),
        role=user_in.role.value if hasattr(user_in.role, "value") else str(user_in.role),
        region=user_in.region,
        country=user_in.country,
        department=user_in.department,
        employment_type=user_in.employment_type,
    )
    db.add(new_user)

    audit = AuditLog(
        id=uuid.uuid4(),
        user_id=current_admin.id,
        action="USER_CREATE",
        resource_type="user",
        resource_id=str(new_user.id),
        details={"email": new_user.email, "role": new_user.role, "region": new_user.region},
        created_at=datetime.now(timezone.utc),
    )
    db.add(audit)

    await db.commit()
    await db.refresh(new_user)
    return UserResponse.model_validate(new_user)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: uuid.UUID,
    user_update: UserUpdate,
    current_admin: User = Depends(require_role(UserRole.HR_ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Update user profile, jurisdiction, role, or department."""
    res = await db.execute(select(User).where(User.id == user_id))
    user = res.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    update_dict = user_update.model_dump(exclude_unset=True)
    if "role" in update_dict and update_dict["role"]:
        val = update_dict["role"]
        update_dict["role"] = val.value if hasattr(val, "value") else str(val)

    for field, val in update_dict.items():
        setattr(user, field, val)

    await db.commit()
    await db.refresh(user)
    return UserResponse.model_validate(user)


@router.delete("/{user_id}")
async def delete_user(
    user_id: uuid.UUID,
    current_admin: User = Depends(require_role(UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Super Admin deletes a user account."""
    res = await db.execute(select(User).where(User.id == user_id))
    user = res.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.id == current_admin.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own admin account.")

    await db.delete(user)
    await db.commit()
    return {"message": f"User {user.email} successfully deleted."}


@router.post("/bulk-import")
async def bulk_import_users(
    file: UploadFile = File(...),
    current_admin: User = Depends(require_role(UserRole.HR_ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Import employees from CSV.
    Expected headers: name, email, role, region, country, department, employment_type, password
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported.")

    content = await file.read()
    text = content.decode("utf-8", errors="replace")
    reader = csv.DictReader(io.StringIO(text))

    created = 0
    skipped = 0
    errors = []

    for row_num, row in enumerate(reader, start=2):
        email = row.get("email", "").strip().lower()
        if not email or "@" not in email:
            errors.append(f"Row {row_num}: Missing or invalid email.")
            continue

        existing = await db.execute(select(User).where(User.email == email))
        if existing.scalar_one_or_none():
            skipped += 1
            continue

        raw_role = row.get("role", "employee").strip().lower()
        role_val = (
            UserRole.SUPER_ADMIN.value
            if "super" in raw_role
            else UserRole.HR_ADMIN.value
            if "hr" in raw_role or "admin" in raw_role
            else UserRole.EMPLOYEE.value
        )

        raw_pwd = row.get("password", "").strip() or "WelcomeLeaveHRAlone2026!"

        user = User(
            id=uuid.uuid4(),
            name=row.get("name", email.split("@")[0].title()).strip(),
            email=email,
            password_hash=get_password_hash(raw_pwd),
            role=role_val,
            region=row.get("region", "Global").strip(),
            country=row.get("country", "Global").strip(),
            department=row.get("department", "General").strip(),
            employment_type=row.get("employment_type", "Full-Time").strip(),
        )
        db.add(user)
        created += 1

    await db.commit()
    return {
        "created_count": created,
        "skipped_count": skipped,
        "errors": errors,
        "message": f"Successfully processed CSV. Created {created} users, skipped {skipped} existing.",
    }


@router.post("/invite")
async def create_user_invite(
    payload: dict[str, Any],
    current_admin: User = Depends(require_role(UserRole.HR_ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Generate an employee onboarding invite token and registration link."""
    email = payload.get("email", "").strip().lower()
    name = payload.get("name", "").strip()
    region = payload.get("region", "Global").strip()
    role = payload.get("role", UserRole.EMPLOYEE.value).strip()

    if not email:
        raise HTTPException(status_code=400, detail="Email is required.")

    token_data = {
        "sub": email,
        "name": name,
        "region": region,
        "role": role,
        "type": "invite",
    }
    invite_token = create_access_token(token_data, expires_delta=None)
    invite_url = f"/register?invite={invite_token}"

    return {
        "invite_token": invite_token,
        "invite_url": invite_url,
        "message": f"Invite generated for {email}.",
    }
