import pytest
from django.core.management import call_command

from organizations.models import Organismo
from sources.ingestion import (
    FetchResult,
    IngestionError,
    IngestionService,
    validate_public_url,
)
from sources.models import Documento, Fuente


class FakeFetcher:
    def __init__(self, result=None, error=None):
        self.result = result
        self.error = error
        self.calls = []

    def fetch(self, url):
        self.calls.append(url)
        if self.error:
            raise self.error
        return self.result


@pytest.fixture
def fuente(db):
    organismo = Organismo.objects.create(nombre='Organismo DEMO')
    return Fuente.objects.create(
        nombre='Fuente DEMO',
        url='https://demo.invalid/fuente/',
        organismo=organismo,
        tipo=Fuente.Tipo.SITIO_WEB,
        origen_informacion=Fuente.OrigenInformacion.DEMO,
    )


def html_result(body=b'<h1>Titulo DEMO</h1><script>secreto</script><p>Texto util</p>'):
    return FetchResult(
        body=body,
        final_url='https://demo.invalid/fuente/',
        content_type='text/html',
        etag='"demo-v1"',
        last_modified='Wed, 01 Jan 2025 12:00:00 GMT',
    )


def test_rechaza_destinos_de_red_privada(monkeypatch):
    monkeypatch.setattr(
        'sources.ingestion.socket.getaddrinfo',
        lambda *args: [(2, 1, 6, '', ('127.0.0.1', 80))],
    )

    with pytest.raises(IngestionError, match='privada o reservada'):
        validate_public_url('http://interno.invalid/recurso')


def test_rechaza_urls_con_credenciales():
    with pytest.raises(IngestionError, match='URL pública'):
        validate_public_url('https://usuario:clave@example.com/recurso')


@pytest.mark.django_db
def test_ingesta_html_crea_documento_trazable(fuente):
    fetcher = FakeFetcher(result=html_result())

    result = IngestionService(fetcher=fetcher).ingest(fuente)

    assert result.changed is True
    assert result.documento.fuente == fuente
    assert result.documento.tipo == Documento.Tipo.HTML
    assert result.documento.checksum
    assert 'Titulo DEMO' in result.documento.texto_extraido
    assert 'Texto util' in result.documento.texto_extraido
    assert 'secreto' not in result.documento.texto_extraido
    assert result.documento.metadata['ingesta']['etag'] == '"demo-v1"'
    fuente.refresh_from_db()
    assert fuente.estado_disponibilidad == Fuente.EstadoDisponibilidad.DISPONIBLE
    assert fuente.fecha_ultima_consulta is not None


@pytest.mark.django_db
def test_checksum_evita_reprocesar_contenido_sin_cambios(fuente):
    fetcher = FakeFetcher(result=html_result())
    service = IngestionService(fetcher=fetcher)
    first_result = service.ingest(fuente)
    original_update = first_result.documento.fecha_actualizacion

    second_result = service.ingest(fuente)

    assert second_result.changed is False
    assert Documento.objects.filter(fuente=fuente).count() == 1
    assert second_result.documento.fecha_actualizacion == original_update


@pytest.mark.django_db
def test_error_de_descarga_marca_fuente_no_disponible(fuente):
    service = IngestionService(
        fetcher=FakeFetcher(error=IngestionError('Falla DEMO'))
    )

    with pytest.raises(IngestionError, match='Falla DEMO'):
        service.ingest(fuente)

    fuente.refresh_from_db()
    assert fuente.estado_disponibilidad == Fuente.EstadoDisponibilidad.NO_DISPONIBLE
    assert fuente.fecha_ultima_consulta is not None
    assert Documento.objects.count() == 0


@pytest.mark.django_db
def test_tipo_de_contenido_desconocido_no_se_persiste(fuente):
    result = FetchResult(
        body=b'contenido',
        final_url=fuente.url,
        content_type='application/octet-stream',
    )

    with pytest.raises(IngestionError, match='no admitido'):
        IngestionService(fetcher=FakeFetcher(result=result)).ingest(fuente)

    assert Documento.objects.count() == 0


@pytest.mark.django_db
def test_comando_procesa_solo_fuentes_activas_y_verificadas(fuente, mocker):
    fuente.estado_verificacion = Fuente.EstadoVerificacion.VERIFICADA
    fuente.save(update_fields=('estado_verificacion',))
    Fuente.objects.create(
        nombre='Fuente pendiente DEMO',
        url='https://demo.invalid/pendiente/',
        organismo=fuente.organismo,
        tipo=Fuente.Tipo.SITIO_WEB,
        origen_informacion=Fuente.OrigenInformacion.DEMO,
    )
    service = mocker.patch(
        'sources.management.commands.ingestar_fuentes.IngestionService'
    ).return_value
    service.ingest.return_value.changed = False

    call_command('ingestar_fuentes')

    service.ingest.assert_called_once_with(fuente)
