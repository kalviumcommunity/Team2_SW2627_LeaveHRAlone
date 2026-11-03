from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import api_router
from app.core.config import settings
from app.rag.vector_db import vector_db

logger = logging.getLogger("leavehralone")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Startup validation of AI providers
    logger.info("Starting %s in %s mode...", settings.app_name, settings.app_env)
    try:
        settings.validate_providers()
        logger.info("AI Provider configuration validated: LLM=%s, Embedding=%s", settings.llm_provider, settings.embedding_provider)
    except Exception as e:
        logger.error("Startup validation error: %s", e)
        # In non-test environments this will abort or warn appropriately
        if settings.app_env.lower() != "test" and not settings.allow_mock_providers:
            raise

    # 2. Ensure Qdrant collection and payload indexes
    try:
        vector_db.ensure_collection()
        logger.info("Vector database verified at %s", settings.qdrant_url)
    except Exception as e:
        logger.error("Failed to connect/initialize vector database: %s", e)
        if settings.app_env.lower() != "test":
            raise

    # 3. Auto-initialize default accounts if fresh database
    try:
        import uuid
        from sqlalchemy import func, select
        from app.core.security import get_password_hash
        from app.db.models import User, UserRole
        from app.db.session import AsyncSessionLocal

        async with AsyncSessionLocal() as session:
            count_res = await session.execute(select(func.count(User.id)))
            user_count = count_res.scalar() or 0
            if user_count == 0:
                admin_user = User(
                    id=uuid.uuid4(),
                    name="Priya Nair",
                    email="hr.admin@example.com",
                    password_hash=get_password_hash("password123"),
                    role=UserRole.HR_ADMIN.value,
                    region="India",
                    country="India",
                    department="Human Resources",
                    employment_type="Full-Time",
                )
                emp_user = User(
                    id=uuid.uuid4(),
                    name="Aarav Sharma",
                    email="employee.india@example.com",
                    password_hash=get_password_hash("password123"),
                    role=UserRole.EMPLOYEE.value,
                    region="India",
                    country="India",
                    department="Engineering",
                    employment_type="Full-Time",
                )
                super_user = User(
                    id=uuid.uuid4(),
                    name="David Kim",
                    email="admin@example.com",
                    password_hash=get_password_hash("password123"),
                    role=UserRole.SUPER_ADMIN.value,
                    region="Global",
                    country="Global",
                    department="Executive",
                    employment_type="Full-Time",
                )
                session.add_all([admin_user, emp_user, super_user])
                await session.commit()
                logger.info("Auto-initialized default accounts (hr.admin@example.com, employee.india@example.com) for fresh database.")
    except Exception as e:
        logger.debug("Startup default accounts check: %s", e)

    yield


app = FastAPI(
    title=settings.app_name,
    description="LeaveHRAlone AI — Production-grade, region-aware HR policy assistant API.",
    version="1.0.0",
    lifespan=lifespan,
)

configured_origins = [o.strip() for o in settings.frontend_origin.split(",") if o.strip()]
default_origins = ["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:3000", "http://127.0.0.1:5173"]
allowed_origins = list(set(configured_origins + default_origins))

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")


@app.get("/")
def root() -> dict[str, str]:
    return {
        "message": f"{settings.app_name} API is running.",
        "docs": "/docs",
        "health": "/api/health",
    }
