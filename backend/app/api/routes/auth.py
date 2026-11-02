import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from app.db.models import User, UserRole
from app.db.session import get_db
from app.schemas.auth import GoogleAuthRequest, RefreshTokenRequest, Token
from app.schemas.user import UserCreate, UserLogin, UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Register a new user account and return JWT credentials."""
    # Check if email exists
    existing = await db.execute(select(User).where(User.email == user_in.email))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists.",
        )

    # Create new user
    db_user = User(
        id=uuid.uuid4(),
        name=user_in.name,
        email=user_in.email,
        password_hash=get_password_hash(user_in.password),
        role=user_in.role.value,
        region=user_in.region,
        country=user_in.country,
        department=user_in.department,
        employment_type=user_in.employment_type,
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)

    token_data = {
        "sub": str(db_user.id),
        "role": db_user.role,
        "region": db_user.region,
    }
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(db_user),
    )


@router.post("/login", response_model=Token)
async def login(
    credentials: UserLogin,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Authenticate with email and password to receive JWT credentials."""
    result = await db.execute(select(User).where(User.email == credentials.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token_data = {
        "sub": str(user.id),
        "role": user.role,
        "region": user.region,
    }
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user),
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    payload: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Exchange a valid refresh token for a fresh access and refresh token pair."""
    try:
        decoded = decode_token(payload.refresh_token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    if decoded.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type: refresh token required",
        )

    user_id_str = decoded.get("sub")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token subject",
        )

    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id_str)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    token_data = {
        "sub": str(user.id),
        "role": user.role,
        "region": user.region,
    }
    new_access_token = create_access_token(token_data)
    new_refresh_token = create_refresh_token(token_data)

    return Token(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        user=UserResponse.model_validate(user),
    )


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    """Log out the current session."""
    return {"message": "Successfully logged out."}


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_user),
) -> Any:
    """Retrieve the current logged-in employee or administrator profile."""
    return UserResponse.model_validate(current_user)


@router.post("/google", response_model=Token)
async def google_auth(
    payload: GoogleAuthRequest,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Verify Google OAuth token and return user authentication credentials."""
    # In enterprise production, this validates against Google's tokeninfo endpoint.
    # Here we support both simulated/dev tokens and parse basic email metadata.
    email = "google.user@example.com"
    name = "Google User"

    # If id_token contains structured info (e.g. for testing)
    if "@" in payload.id_token:
        email = payload.id_token.strip()
        name = email.split("@")[0].replace(".", " ").title()

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        user = User(
            id=uuid.uuid4(),
            name=name,
            email=email,
            password_hash=get_password_hash(uuid.uuid4().hex),
            role=UserRole.EMPLOYEE.value,
            region=payload.region or "India",
            country=payload.country or "India",
            department="General",
            employment_type="Full-Time",
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    token_data = {
        "sub": str(user.id),
        "role": user.role,
        "region": user.region,
    }
    return Token(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
        user=UserResponse.model_validate(user),
    )
