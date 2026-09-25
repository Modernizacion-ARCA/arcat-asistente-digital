import pytest
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models.deletion import ProtectedError

from organizations.models import Organismo
from procedures.models import Tramite
from sources.models import DocumentChunk, Documento, Fuente


@pytest.fixture
def fuente_demo(db):
    organismo = Organismo.objects.create(nombre='Organismo DEMO')
    fuente = Fuente.objects.create(
        nombre='Fuente DEMO',
        url='https://demo.invalid/fuente/',
        organismo=organismo,
        tipo=Fuente.Tipo.SITIO_WEB,
        origen_informacion=Fuente.OrigenInformacion.DEMO,
        estado_verificacion=Fuente.EstadoVerificacion.VERIFICADA,
        metadata={'entorno': 'pruebas'},
    )
    return organismo, fuente


@pytest.mark.django_db
def test_documento_es_trazable_hasta_fuente_y_tramite(fuente_demo):
    organismo, fuente = fuente_demo
    tramite = Tramite.objects.create(
        nombre='Trámite DEMO',
        slug='documento-tramite-demo',
        descripcion='Contenido ficticio.',
        organismo=organismo,
    )
    documento = Documento.objects.create(
        titulo='Documento DEMO',
        tipo=Documento.Tipo.GUIA,
        fuente=fuente,
        url='https://demo.invalid/documento/',
        contenido='Contenido DEMO sin valor institucional.',
        texto_extraido='Contenido DEMO sin valor institucional.',
        checksum='a' * 64,
    )
    documento.tramites.add(tramite)

    assert documento.fuente == fuente
    assert documento.tramites.get() == tramite
    assert tramite.documentos.get() == documento
    assert fuente.documentos.get() == documento


@pytest.mark.django_db
def test_checksum_debe_ser_sha256_hexadecimal(fuente_demo):
    _, fuente = fuente_demo
    documento = Documento(
        titulo='Documento inválido DEMO',
        tipo=Documento.Tipo.PDF,
        fuente=fuente,
        url='https://demo.invalid/invalido.pdf',
        checksum='no-es-un-sha256',
    )

    with pytest.raises(ValidationError, match='SHA-256'):
        documento.full_clean()


@pytest.mark.django_db
def test_fuente_no_se_elimina_si_tiene_documentos(fuente_demo):
    _, fuente = fuente_demo
    Documento.objects.create(
        titulo='Documento protegido DEMO',
        tipo=Documento.Tipo.HTML,
        fuente=fuente,
        url='https://demo.invalid/protegido/',
    )

    with pytest.raises(ProtectedError):
        fuente.delete()


@pytest.mark.django_db
def test_fragmento_persiste_embedding_y_trazabilidad(fuente_demo):
    _, fuente = fuente_demo
    documento = Documento.objects.create(
        titulo='Documento vectorial DEMO',
        tipo=Documento.Tipo.HTML,
        fuente=fuente,
        url='https://demo.invalid/vectorial/',
    )

    fragmento = DocumentChunk.objects.create(
        documento=documento,
        contenido='Contenido fragmentado DEMO.',
        indice=0,
        embedding=[0.0] * settings.EMBEDDING_DIMENSION,
        embedding_model=settings.EMBEDDING_MODEL,
        metadata={'seccion': 'demo'},
    )

    fragmento.refresh_from_db()
    assert fragmento.documento.fuente == fuente
    assert fragmento.documento == documento
    assert len(fragmento.embedding) == settings.EMBEDDING_DIMENSION
    assert fragmento.embedding_model == settings.EMBEDDING_MODEL
