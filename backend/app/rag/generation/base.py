from abc import ABC, abstractmethod
from typing import AsyncGenerator, List, Optional


class BaseLLMProvider(ABC):
    """Abstract interface for LLM text and structured response generation."""

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 1000,
    ) -> str:
        """Generate response text synchronously."""
        pass

    @abstractmethod
    async def generate_async(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 1000,
    ) -> str:
        """Generate response text asynchronously."""
        pass
