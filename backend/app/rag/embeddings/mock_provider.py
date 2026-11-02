import hashlib
import math
import re
from typing import List

from app.rag.embeddings.base import BaseEmbeddingProvider


class MockEmbeddingProvider(BaseEmbeddingProvider):
    """Deterministic, offline embedding provider for tests, CI, and local dev."""

    def __init__(self, dimension: int = 1536):
        self._dimension = dimension

    @property
    def dimension(self) -> int:
        return self._dimension

    def _hash_word_to_index(self, word: str) -> int:
        digest = hashlib.md5(word.lower().encode("utf-8")).hexdigest()
        return int(digest, 16) % self._dimension

    def embed_text(self, text: str) -> List[float]:
        vector = [0.0] * self._dimension
        words = re.findall(r"\w+", text.lower())

        if not words:
            # Non-empty fallback vector
            vector[0] = 1.0
            return vector

        for word in words:
            idx = self._hash_word_to_index(word)
            vector[idx] += 1.0

        # L2 normalize vector for cosine similarity
        norm = math.sqrt(sum(v * v for v in vector))
        if norm > 0:
            vector = [v / norm for v in vector]
        else:
            vector[0] = 1.0

        return vector

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        return [self.embed_text(t) for t in texts]
