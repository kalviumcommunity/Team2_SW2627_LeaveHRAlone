from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "PolicyPilot AI"
    app_env: str = "development"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    frontend_origin: str = "http://localhost:3000"

    # PostgreSQL Database
    postgres_db: str = "policypilot"
    postgres_user: str = "postgres"
    postgres_password: str = "postgres"
    postgres_port: int = 5432
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/policypilot"
    sync_database_url: str = "postgresql://postgres:postgres@localhost:5432/policypilot"

    # Qdrant Vector Database
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "hr_policy_chunks"

    # Redis & Celery
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"

    # Security & Auth
    jwt_secret_key: str = "super-secret-dev-jwt-key-minimum-32-characters-for-hs256"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7

    # LLM & Embedding Providers
    llm_provider: Literal["mock", "gemini", "openai", "anthropic", "ollama"] = "mock"
    embedding_provider: Literal["mock", "openai", "gemini", "ollama"] = "mock"
    embedding_dimension: int = 1536
    allow_mock_providers: bool = False

    # Specific Model Names
    gemini_model: str = "gemini-1.5-flash"
    gemini_embedding_model: str = "text-embedding-004"
    openai_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-small"
    anthropic_model: str = "claude-3-5-sonnet-20241022"
    ollama_model: str = "llama3"
    ollama_embedding_model: str = "nomic-embed-text"

    # API Keys & URLs
    gemini_api_key: str = ""
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    ollama_base_url: str = "http://localhost:11434"

    # RAG Tuning
    rag_similarity_threshold: float = 0.45
    rag_enable_hybrid_search: bool = True

    # Rate Limiting
    rate_limit_per_minute: int = 60

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    def validate_providers(self) -> None:
        """Enforce strict provider credential check in non-test environments."""
        if self.app_env.lower() == "test":
            return

        if self.llm_provider == "mock" and not self.allow_mock_providers:
            raise RuntimeError(
                "Mock LLM provider is disabled in non-test environment. "
                "Please configure a real LLM provider (LLM_PROVIDER=gemini, openai, anthropic, or ollama) "
                "or set ALLOW_MOCK_PROVIDERS=true for offline demonstration."
            )

        if self.embedding_provider == "mock" and not self.allow_mock_providers:
            raise RuntimeError(
                "Mock Embedding provider is disabled in non-test environment. "
                "Please configure a real Embedding provider (EMBEDDING_PROVIDER=gemini, openai, or ollama) "
                "or set ALLOW_MOCK_PROVIDERS=true for offline demonstration."
            )

        if self.llm_provider == "gemini" and not self.gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY is required when LLM_PROVIDER=gemini.")
        if self.llm_provider == "openai" and not self.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is required when LLM_PROVIDER=openai.")
        if self.llm_provider == "anthropic" and not self.anthropic_api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is required when LLM_PROVIDER=anthropic.")

        if self.embedding_provider == "gemini" and not self.gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY is required when EMBEDDING_PROVIDER=gemini.")
        if self.embedding_provider == "openai" and not self.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is required when EMBEDDING_PROVIDER=openai.")


settings = Settings()

