from app.core.config import settings
from app.rag.generation.anthropic_provider import AnthropicLLMProvider, OllamaLLMProvider
from app.rag.generation.base import BaseLLMProvider
from app.rag.generation.mock_provider import MockLLMProvider
from app.rag.generation.openai_provider import GeminiLLMProvider, OpenAILLMProvider


def get_llm_provider() -> BaseLLMProvider:
    """Instantiate and return the configured LLM provider based on settings."""
    provider_type = settings.llm_provider.lower()
    if provider_type == "openai":
        return OpenAILLMProvider()
    elif provider_type == "gemini":
        return GeminiLLMProvider()
    elif provider_type == "anthropic":
        return AnthropicLLMProvider()
    elif provider_type == "ollama":
        return OllamaLLMProvider()
    else:
        return MockLLMProvider()


__all__ = [
    "BaseLLMProvider",
    "MockLLMProvider",
    "OpenAILLMProvider",
    "GeminiLLMProvider",
    "AnthropicLLMProvider",
    "OllamaLLMProvider",
    "get_llm_provider",
]
