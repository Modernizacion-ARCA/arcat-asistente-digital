from dataclasses import dataclass

from django.conf import settings
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from pgvector.django import CosineDistance

from core.ai.embeddings import get_embedding_provider

from .models import DocumentChunk, Fuente


@dataclass(frozen=True)
class RetrievalFilters:
    organismo_id: int | None = None
    categoria_id: int | None = None
    origen_informacion: str | None = Fuente.OrigenInformacion.OFICIAL
    metadata: dict | None = None


@dataclass(frozen=True)
class RetrievalResult:
    chunk: DocumentChunk
    score: float
    vector_rank: int | None
    text_rank: int | None


class HybridRetriever:
    """Combine vector and PostgreSQL full-text ranks using reciprocal rank fusion."""

    rank_constant = 60
    candidate_multiplier = 4

    def __init__(self, embedding_provider=None, top_k=None):
        self.embedding_provider = embedding_provider or get_embedding_provider()
        self.top_k = top_k or settings.RAG_TOP_K

    def _base_queryset(self, filters):
        queryset = DocumentChunk.objects.select_related(
            'documento',
            'documento__fuente',
        ).filter(
            documento__activo=True,
            documento__fuente__activo=True,
            documento__fuente__estado_verificacion=(
                Fuente.EstadoVerificacion.VERIFICADA
            ),
            embedding_model=self.embedding_provider.model_name,
        )
        if filters.organismo_id is not None:
            queryset = queryset.filter(
                documento__fuente__organismo_id=filters.organismo_id
            )
        if filters.categoria_id is not None:
            queryset = queryset.filter(
                documento__fuente__categoria_id=filters.categoria_id
            )
        if filters.origen_informacion is not None:
            queryset = queryset.filter(
                documento__fuente__origen_informacion=filters.origen_informacion
            )
        if filters.metadata:
            queryset = queryset.filter(metadata__contains=filters.metadata)
        return queryset

    def _vector_candidates(self, queryset, query_embedding, limit):
        return list(
            queryset.annotate(
                vector_distance=CosineDistance('embedding', query_embedding)
            ).order_by('vector_distance')[:limit]
        )

    def _text_candidates(self, queryset, query, limit):
        search_query = SearchQuery(query, config='spanish', search_type='websearch')
        search_vector = SearchVector('contenido', config='spanish')
        return list(
            queryset.annotate(
                text_rank_score=SearchRank(search_vector, search_query)
            ).filter(text_rank_score__gt=0).order_by('-text_rank_score')[:limit]
        )

    def _fuse(self, vector_candidates, text_candidates):
        combined = {}
        for rank, chunk in enumerate(vector_candidates, start=1):
            combined[chunk.pk] = {
                'chunk': chunk,
                'score': 1 / (self.rank_constant + rank),
                'vector_rank': rank,
                'text_rank': None,
            }
        for rank, chunk in enumerate(text_candidates, start=1):
            item = combined.setdefault(chunk.pk, {
                'chunk': chunk,
                'score': 0,
                'vector_rank': None,
                'text_rank': None,
            })
            item['score'] += 1 / (self.rank_constant + rank)
            item['text_rank'] = rank
        ordered = sorted(combined.values(), key=lambda item: item['score'], reverse=True)
        return [RetrievalResult(**item) for item in ordered[:self.top_k]]

    def retrieve(self, query, filters=None):
        query = query.strip()
        if not query:
            return []
        filters = filters or RetrievalFilters()
        queryset = self._base_queryset(filters)
        query_embedding = self.embedding_provider.embed([query])[0]
        limit = self.top_k * self.candidate_multiplier
        vector_candidates = self._vector_candidates(queryset, query_embedding, limit)
        text_candidates = self._text_candidates(queryset, query, limit)
        return self._fuse(vector_candidates, text_candidates)
