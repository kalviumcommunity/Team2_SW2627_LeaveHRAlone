from app.core.config import settings
from app.rag.embeddings.base import BaseEmbeddingProvider
from app.rag.embeddings.gemini_provider import GeminiEmbeddingProvider, OllamaEmbeddingProvider
from app.rag.embeddings.mock_provider import MockEmbeddingProvider
from app.rag.embeddings.openai_provider import OpenAIEmbeddingProvider


def get_embedding_provider() -> BaseEmbeddingProvider:
    """Return the configured embedding provider based on environment variables."""
    provider_type = settings.embedding_provider.lower()
    if provider_type == "openai":
        return OpenAIEmbeddingProvider()
    elif provider_type == "gemini":
        return GeminiEmbeddingProvider()
    elif provider_type == "ollama":
        return OllamaEmbeddingProvider()
    else:
        return MockEmbeddingProvider(dimension=settings.embedding_dimension)


__all__ = [
    "BaseEmbeddingProvider",
    "MockEmbeddingProvider",
    "OpenAIEmbeddingProvider",
    "GeminiEmbeddingProvider",
    "OllamaEmbeddingProvider",
    "get_embedding_provider",
]
