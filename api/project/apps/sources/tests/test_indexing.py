from types import SimpleNamespace

import pytest
from django.conf import settings
from django.core.management import call_command

from organizations.models import Organismo
from sources.chunking import TextChunker
from sources.indexing import DocumentIndexer, IndexingError
from sources.models import DocumentChunk, Documento, Fuente
from sources.retrieval import HybridRetriever


class FakeEmbeddingProvider:
    model_name = 'modelo-local-demo'

    def __init__(self):
        self.calls = []

    def embed(self, texts):
        texts = list(texts)
        self.calls.append(texts)
        return [[float(index)] * settings.EMBEDDING_DIMENSION
                for index, _ in enumerate(texts)]


@pytest.fixture
def documento(db):
    organismo = Organismo.objects.create(nombre='Organismo indexación DEMO')
    fuente = Fuente.objects.create(
        nombre='Fuente indexación DEMO',
        url='https://demo.invalid/indexacion/',
        organismo=organismo,
        tipo=Fuente.Tipo.SITIO_WEB,
        origen_informacion=Fuente.OrigenInformacion.DEMO,
        estado_verificacion=Fuente.EstadoVerificacion.VERIFICADA,
    )
    return Documento.objects.create(
        titulo='Documento indexación DEMO',
        tipo=Documento.Tipo.HTML,
        fuente=fuente,
        url='https://demo.invalid/indexacion/documento/',
        texto_extraido='uno dos tres cuatro cinco seis siete ocho nueve diez',
        checksum='b' * 64,
        metadata={'jurisdiccion': 'demo'},
    )


@pytest.mark.django_db
def test_indexador_crea_fragmentos_con_embeddings_y_metadata(documento):
    provider = FakeEmbeddingProvider()
    indexer = DocumentIndexer(
        embedding_provider=provider,
        chunker=TextChunker(chunk_size=5, overlap=1),
    )

    result = indexer.index(documento)

    chunks = list(documento.fragmentos.order_by('indice'))
    assert result.changed is True
    assert result.chunks == 3
    assert [chunk.indice for chunk in chunks] == [0, 1, 2]
    assert all(chunk.embedding_model == provider.model_name for chunk in chunks)
    assert all(chunk.metadata['document_checksum'] == documento.checksum
               for chunk in chunks)
    assert all(chunk.metadata['jurisdiccion'] == 'demo' for chunk in chunks)
    assert len(chunks[0].embedding) == settings.EMBEDDING_DIMENSION


@pytest.mark.django_db
def test_indexador_no_regenera_si_configuracion_y_texto_no_cambian(documento):
    provider = FakeEmbeddingProvider()
    indexer = DocumentIndexer(
        embedding_provider=provider,
        chunker=TextChunker(chunk_size=5, overlap=1),
    )
    indexer.index(documento)

    result = indexer.index(documento)

    assert result.changed is False
    assert len(provider.calls) == 1


@pytest.mark.django_db
def test_error_de_embeddings_no_elimina_indice_anterior(documento):
    valid_provider = FakeEmbeddingProvider()
    DocumentIndexer(
        embedding_provider=valid_provider,
        chunker=TextChunker(chunk_size=5, overlap=1),
    ).index(documento)
    original_ids = list(documento.fragmentos.values_list('pk', flat=True))
    documento.texto_extraido += ' contenido modificado'

    invalid_provider = FakeEmbeddingProvider()
    invalid_provider.embed = lambda texts: []
    with pytest.raises(IndexingError, match='un vector por fragmento'):
        DocumentIndexer(
            embedding_provider=invalid_provider,
            chunker=TextChunker(chunk_size=5, overlap=1),
        ).index(documento)

    assert list(documento.fragmentos.values_list('pk', flat=True)) == original_ids


def test_retrieval_hibrido_fusiona_resultados_vectoriales_y_textuales():
    shared = SimpleNamespace(pk=1)
    vector_only = SimpleNamespace(pk=2)
    text_only = SimpleNamespace(pk=3)
    retriever = HybridRetriever(
        embedding_provider=FakeEmbeddingProvider(),
        top_k=3,
    )

    results = retriever._fuse(
        [shared, vector_only],
        [shared, text_only],
    )

    assert [result.chunk.pk for result in results] == [1, 2, 3]
    assert results[0].vector_rank == 1
    assert results[0].text_rank == 1
    assert results[1].text_rank is None
    assert results[2].vector_rank is None


@pytest.mark.django_db
def test_comando_indexa_solo_documentos_de_fuentes_verificadas(documento, mocker):
    pending_source = Fuente.objects.create(
        nombre='Fuente pendiente para indexación DEMO',
        url='https://demo.invalid/indexacion/pendiente/',
        organismo=documento.fuente.organismo,
        tipo=Fuente.Tipo.SITIO_WEB,
        origen_informacion=Fuente.OrigenInformacion.DEMO,
    )
    Documento.objects.create(
        titulo='Documento pendiente DEMO',
        tipo=Documento.Tipo.HTML,
        fuente=pending_source,
        url='https://demo.invalid/indexacion/pendiente/documento/',
        texto_extraido='No debe indexarse.',
    )
    indexer = mocker.patch(
        'sources.management.commands.indexar_documentos.DocumentIndexer'
    ).return_value
    indexer.index.return_value = SimpleNamespace(changed=True, chunks=1)

    call_command('indexar_documentos')

    indexer.index.assert_called_once_with(documento)
