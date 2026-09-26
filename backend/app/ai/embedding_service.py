# app/ai/embedding_service.py

from abc import ABC, abstractmethod
from functools import lru_cache

from app.core.config import settings


class EmbeddingProvider(ABC):
    @abstractmethod
    def embed_text(self, text: str) -> list[float]:
        """Embed a single piece of text (e.g., a user query)."""
        ...

    @abstractmethod
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed multiple texts at once (e.g., a batch of document chunks)."""
        ...


class SentenceTransformerEmbeddingProvider(EmbeddingProvider):
    """
    Local embedding model — no API key, no network call, runs on your machine.
    Uses all-MiniLM-L6-v2, which outputs 384-dimensional vectors — this MUST
    stay in sync with EMBEDDING_DIMENSIONS in app/schemes/document_models.py.
    """

    MODEL_NAME = "all-MiniLM-L6-v2"

    def __init__(self):
        # imported lazily so importing this module doesn't force-load
        # sentence-transformers (and torch) for code paths that never embed anything
        # pyrefly: ignore [missing-import]
        from sentence_transformers import SentenceTransformer

        self._model = SentenceTransformer(self.MODEL_NAME)

    def embed_text(self, text: str) -> list[float]:
        return self._model.encode(text, normalize_embeddings=True).tolist()

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        embeddings = self._model.encode(texts, normalize_embeddings=True)
        return embeddings.tolist()


@lru_cache(maxsize=1)
def get_embedding_provider() -> EmbeddingProvider:
    """
    Factory — the single place that decides which embedding provider
    is active. Callers depend on this function and the EmbeddingProvider
    interface, never on a concrete class directly.
    """
    provider_name = settings.embedding_provider or "sentence_transformers"

    if provider_name == "sentence_transformers":
        return SentenceTransformerEmbeddingProvider()

    raise NotImplementedError(f"Unknown embedding provider: '{provider_name}'")