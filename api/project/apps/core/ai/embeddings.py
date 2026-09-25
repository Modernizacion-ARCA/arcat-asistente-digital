from abc import ABC, abstractmethod

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


class EmbeddingProvider(ABC):
    @abstractmethod
    def embed(self, texts):
        """Return one embedding for each supplied text."""


class LocalEmbeddingProvider(EmbeddingProvider):
    def __init__(self, model_name=None, dimension=None, model_factory=None):
        self.model_name = model_name or settings.EMBEDDING_MODEL
        self.dimension = dimension or settings.EMBEDDING_DIMENSION
        self._model_factory = model_factory
        self._model = None

    def _load_model(self):
        if self._model is None:
            if self._model_factory is None:
                from sentence_transformers import SentenceTransformer

                self._model_factory = SentenceTransformer
            self._model = self._model_factory(self.model_name)
        return self._model

    def embed(self, texts):
        texts = list(texts)
        if not texts:
            return []
        vectors = self._load_model().encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        result = [vector.tolist() if hasattr(vector, 'tolist') else list(vector)
                  for vector in vectors]
        if any(len(vector) != self.dimension for vector in result):
            raise ValueError(
                f'El modelo {self.model_name} no generó vectores de '
                f'{self.dimension} dimensiones.'
            )
        return result


def get_embedding_provider():
    if settings.EMBEDDING_PROVIDER == 'local':
        return LocalEmbeddingProvider()
    raise ImproperlyConfigured(
        f'Proveedor de embeddings no soportado: {settings.EMBEDDING_PROVIDER}.'
    )
