import hashlib
import json
from dataclasses import dataclass

from django.conf import settings
from django.db import transaction

from core.ai.embeddings import get_embedding_provider

from .chunking import TextChunker
from .models import DocumentChunk


class IndexingError(Exception):
    """Controlled error raised when a document cannot be indexed."""


@dataclass(frozen=True)
class IndexingResult:
    document_id: int
    chunks: int
    changed: bool


class DocumentIndexer:
    def __init__(self, embedding_provider=None, chunker=None):
        self.embedding_provider = embedding_provider or get_embedding_provider()
        self.chunker = chunker or TextChunker()

    def _signature(self, document, text):
        payload = (
            f'{self.embedding_provider.model_name}\0'
            f'{self.chunker.chunk_size}\0{self.chunker.overlap}\0'
            f'{json.dumps(document.metadata, sort_keys=True, ensure_ascii=False)}\0'
            f'{text}'
        )
        return hashlib.sha256(payload.encode('utf-8')).hexdigest()

    def index(self, document):
        text = (document.texto_extraido or document.contenido).strip()
        if not text:
            raise IndexingError('El documento no contiene texto para indexar.')

        signature = self._signature(document, text)
        chunks = self.chunker.split(text)
        existing = list(document.fragmentos.order_by('indice'))
        if existing and len(existing) == len(chunks) and all(
            chunk.metadata.get('index_signature') == signature
            for chunk in existing
        ):
            return IndexingResult(
                document_id=document.pk,
                chunks=len(existing),
                changed=False,
            )

        try:
            embeddings = self.embedding_provider.embed(
                chunk.content for chunk in chunks
            )
        except Exception as exc:
            raise IndexingError('No se pudieron generar los embeddings locales.') from exc
        if len(embeddings) != len(chunks):
            raise IndexingError(
                'El proveedor de embeddings no devolvió un vector por fragmento.'
            )

        records = [
            DocumentChunk(
                documento=document,
                contenido=chunk.content,
                indice=chunk.index,
                embedding=embedding,
                embedding_model=self.embedding_provider.model_name,
                metadata={
                    **document.metadata,
                    **chunk.metadata,
                    'index_signature': signature,
                    'document_checksum': document.checksum,
                },
            )
            for chunk, embedding in zip(chunks, embeddings)
        ]
        with transaction.atomic():
            document.fragmentos.all().delete()
            DocumentChunk.objects.bulk_create(records)
        return IndexingResult(
            document_id=document.pk,
            chunks=len(records),
            changed=True,
        )
