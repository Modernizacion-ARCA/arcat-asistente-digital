import json
from io import StringIO
from types import SimpleNamespace

import pytest
from django.core.cache import cache
from django.core.management import call_command
from django.core.management.base import CommandError

from organizations.models import Organismo
from sources.models import Fuente, KnowledgeUpdateRun


@pytest.fixture
def official_source(db):
    organismo = Organismo.objects.create(nombre='ARCAT actualización')
    source = Fuente.objects.create(
        nombre='Fuente oficial verificada',
        url='https://example.gob.ar/fuente/',
        organismo=organismo,
        tipo=Fuente.Tipo.SITIO_WEB,
        origen_informacion=Fuente.OrigenInformacion.OFICIAL,
        estado_verificacion=Fuente.EstadoVerificacion.VERIFICADA,
    )
    Fuente.objects.create(
        nombre='Fuente DEMO excluida',
        url='https://demo.invalid/fuente/',
        organismo=organismo,
        tipo=Fuente.Tipo.SITIO_WEB,
        origen_informacion=Fuente.OrigenInformacion.DEMO,
        estado_verificacion=Fuente.EstadoVerificacion.VERIFICADA,
    )
    Fuente.objects.create(
        nombre='Fuente oficial pendiente excluida',
        url='https://example.gob.ar/pendiente/',
        organismo=organismo,
        tipo=Fuente.Tipo.SITIO_WEB,
        origen_informacion=Fuente.OrigenInformacion.OFICIAL,
    )
    return source


@pytest.fixture(autouse=True)
def clear_update_lock():
    cache.delete('sources:actualizar_conocimiento:lock')
    yield
    cache.delete('sources:actualizar_conocimiento:lock')


@pytest.mark.django_db
def test_actualizacion_procesa_solo_fuentes_oficiales_verificadas(
    official_source,
    mocker,
):
    document = object()
    ingestion = mocker.patch(
        'sources.management.commands.actualizar_conocimiento.IngestionService'
    ).return_value
    ingestion.ingest.return_value = SimpleNamespace(
        changed=False,
        documento=document,
    )
    indexer = mocker.patch(
        'sources.management.commands.actualizar_conocimiento.DocumentIndexer'
    ).return_value
    indexer.index.return_value = SimpleNamespace(changed=False)
    stdout = StringIO()

    call_command('actualizar_conocimiento', stdout=stdout)

    ingestion.ingest.assert_called_once_with(official_source)
    indexer.index.assert_called_once_with(document, force=False)
    summary = json.loads(stdout.getvalue())
    run_id = summary.pop('run_id')
    assert summary == {
        'sources': 1,
        'ingested': 0,
        'unchanged': 1,
        'indexed': 0,
        'errors': [],
    }
    run = KnowledgeUpdateRun.objects.get(pk=run_id)
    assert run.estado == KnowledgeUpdateRun.Estado.EXITOSA
    assert run.fuentes_total == 1
    assert run.documentos_sin_cambios == 1
    assert run.fecha_fin is not None


@pytest.mark.django_db
def test_actualizacion_forzada_reindexa_documento(official_source, mocker):
    document = object()
    ingestion = mocker.patch(
        'sources.management.commands.actualizar_conocimiento.IngestionService'
    ).return_value
    ingestion.ingest.return_value = SimpleNamespace(
        changed=False,
        documento=document,
    )
    indexer = mocker.patch(
        'sources.management.commands.actualizar_conocimiento.DocumentIndexer'
    ).return_value
    indexer.index.return_value = SimpleNamespace(changed=True)

    call_command('actualizar_conocimiento', '--force-index')

    indexer.index.assert_called_once_with(document, force=True)


@pytest.mark.django_db
def test_actualizacion_rechaza_ejecuciones_concurrentes(official_source, mocker):
    cache.set('sources:actualizar_conocimiento:lock', 'otra-ejecucion', 60)
    ingestion_class = mocker.patch(
        'sources.management.commands.actualizar_conocimiento.IngestionService'
    )

    with pytest.raises(CommandError, match='otra actualización'):
        call_command('actualizar_conocimiento')

    ingestion_class.assert_not_called()


@pytest.mark.django_db
def test_actualizacion_falla_cerrada_si_el_cache_no_responde(
    official_source,
    mocker,
):
    mocker.patch(
        'sources.management.commands.actualizar_conocimiento.cache.add',
        side_effect=ConnectionError,
    )
    ingestion_class = mocker.patch(
        'sources.management.commands.actualizar_conocimiento.IngestionService'
    )

    with pytest.raises(CommandError, match='bloqueo de actualización'):
        call_command('actualizar_conocimiento')

    ingestion_class.assert_not_called()


@pytest.mark.django_db
def test_actualizacion_libera_el_bloqueo_al_finalizar(official_source, mocker):
    ingestion = mocker.patch(
        'sources.management.commands.actualizar_conocimiento.IngestionService'
    ).return_value
    ingestion.ingest.return_value = SimpleNamespace(
        changed=False,
        documento=object(),
    )
    indexer = mocker.patch(
        'sources.management.commands.actualizar_conocimiento.DocumentIndexer'
    ).return_value
    indexer.index.return_value = SimpleNamespace(changed=False)

    call_command('actualizar_conocimiento')

    assert cache.get('sources:actualizar_conocimiento:lock') is None


@pytest.mark.django_db
def test_actualizacion_registra_errores_controlados(official_source, mocker):
    ingestion = mocker.patch(
        'sources.management.commands.actualizar_conocimiento.IngestionService'
    ).return_value
    ingestion.ingest.side_effect = ValueError('detalle interno')
    mocker.patch(
        'sources.management.commands.actualizar_conocimiento.DocumentIndexer'
    )

    with pytest.raises(CommandError, match='Fallaron 1'):
        call_command('actualizar_conocimiento')

    run = KnowledgeUpdateRun.objects.get()
    assert run.estado == KnowledgeUpdateRun.Estado.ERROR
    assert run.errores == 1
    assert run.detalle_errores == [
        {'source_id': official_source.pk, 'error': 'ValueError'},
    ]
    assert 'detalle interno' not in str(run.detalle_errores)
    assert run.fecha_fin is not None
