import json
from datetime import timedelta
from io import StringIO

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.utils import timezone

from sources.models import KnowledgeUpdateRun


def create_run(*, status, age_hours=0):
    occurred_at = timezone.now() - timedelta(hours=age_hours)
    run = KnowledgeUpdateRun.objects.create(
        estado=status,
        fuentes_total=2,
        documentos_actualizados=1,
        documentos_sin_cambios=1,
        documentos_indexados=1,
        errores=int(status == KnowledgeUpdateRun.Estado.ERROR),
        fecha_fin=(
            None if status == KnowledgeUpdateRun.Estado.EN_CURSO else occurred_at
        ),
    )
    KnowledgeUpdateRun.objects.filter(pk=run.pk).update(
        fecha_inicio=occurred_at,
    )
    run.refresh_from_db()
    return run


@pytest.mark.django_db
def test_estado_saludable_devuelve_metricas_y_run_id():
    run = create_run(status=KnowledgeUpdateRun.Estado.EXITOSA)
    stdout = StringIO()

    call_command('verificar_conocimiento', '--max-hours', '24', stdout=stdout)

    report = json.loads(stdout.getvalue())
    assert report['healthy'] is True
    assert report['reasons'] == []
    assert report['latest_run']['id'] == run.pk
    assert report['last_success_at'] == run.fecha_fin.isoformat()
    assert report['official_verified_sources'] == 0
    assert report['indexed_documents'] == 0
    assert report['chunks'] == 0


@pytest.mark.django_db
def test_estado_falla_si_la_ultima_ejecucion_exitosa_esta_vencida():
    create_run(status=KnowledgeUpdateRun.Estado.EXITOSA, age_hours=25)
    stdout = StringIO()

    with pytest.raises(CommandError, match='last_success_is_stale'):
        call_command('verificar_conocimiento', '--max-hours', '24', stdout=stdout)

    report = json.loads(stdout.getvalue())
    assert report['healthy'] is False
    assert report['reasons'] == ['last_success_is_stale']


@pytest.mark.django_db
def test_estado_falla_si_la_ejecucion_mas_reciente_tuvo_error():
    create_run(status=KnowledgeUpdateRun.Estado.EXITOSA)
    failed = create_run(status=KnowledgeUpdateRun.Estado.ERROR)
    stdout = StringIO()

    with pytest.raises(CommandError, match='latest_run_failed'):
        call_command('verificar_conocimiento', stdout=stdout)

    report = json.loads(stdout.getvalue())
    assert report['latest_run']['id'] == failed.pk
    assert report['reasons'] == ['latest_run_failed']


@pytest.mark.django_db
def test_estado_detecta_una_ejecucion_estancada():
    create_run(status=KnowledgeUpdateRun.Estado.EN_CURSO, age_hours=25)
    stdout = StringIO()

    with pytest.raises(CommandError, match='latest_run_is_stalled'):
        call_command('verificar_conocimiento', '--max-hours', '24', stdout=stdout)

    report = json.loads(stdout.getvalue())
    assert report['reasons'] == [
        'no_successful_run',
        'latest_run_is_stalled',
    ]


def test_estado_rechaza_umbral_invalido():
    with pytest.raises(CommandError, match='mayor que cero'):
        call_command('verificar_conocimiento', '--max-hours', '0')
