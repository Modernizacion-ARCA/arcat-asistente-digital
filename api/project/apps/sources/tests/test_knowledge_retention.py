import json
from datetime import timedelta
from io import StringIO

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.utils import timezone

from sources.models import KnowledgeUpdateRun


def create_run(*, status, days_old):
    run = KnowledgeUpdateRun.objects.create(
        estado=status,
        fecha_fin=timezone.now(),
    )
    KnowledgeUpdateRun.objects.filter(pk=run.pk).update(
        fecha_inicio=timezone.now() - timedelta(days=days_old),
    )
    run.refresh_from_db()
    return run


@pytest.fixture
def run_history(db):
    old_error = create_run(
        status=KnowledgeUpdateRun.Estado.ERROR,
        days_old=120,
    )
    latest_success = create_run(
        status=KnowledgeUpdateRun.Estado.EXITOSA,
        days_old=1,
    )
    old_running = create_run(
        status=KnowledgeUpdateRun.Estado.EN_CURSO,
        days_old=120,
    )
    return old_error, latest_success, old_running


@pytest.mark.django_db
def test_depurar_es_simulacion_por_defecto(run_history):
    old_error, latest_success, _ = run_history
    stdout = StringIO()

    call_command('depurar_actualizaciones_conocimiento', '--days', '90', stdout=stdout)

    report = json.loads(stdout.getvalue())
    assert report['executed'] is False
    assert report['candidates'] == 1
    assert report['deleted_runs'] == 0
    assert report['protected_run_ids'] == [latest_success.pk]
    assert KnowledgeUpdateRun.objects.filter(pk=old_error.pk).exists()


@pytest.mark.django_db
def test_depurar_elimina_solo_finalizadas_antiguas_con_confirmacion(run_history):
    old_error, latest_success, old_running = run_history
    stdout = StringIO()

    call_command(
        'depurar_actualizaciones_conocimiento',
        '--days',
        '90',
        '--execute',
        stdout=stdout,
    )

    report = json.loads(stdout.getvalue())
    assert report['executed'] is True
    assert report['deleted_runs'] == 1
    assert not KnowledgeUpdateRun.objects.filter(pk=old_error.pk).exists()
    assert KnowledgeUpdateRun.objects.filter(pk=latest_success.pk).exists()
    assert KnowledgeUpdateRun.objects.filter(pk=old_running.pk).exists()


@pytest.mark.django_db
def test_depurar_conserva_la_ultima_exitosa_aunque_sea_antigua(db):
    older_error = create_run(
        status=KnowledgeUpdateRun.Estado.ERROR,
        days_old=150,
    )
    old_success = create_run(
        status=KnowledgeUpdateRun.Estado.EXITOSA,
        days_old=120,
    )
    latest_error = create_run(
        status=KnowledgeUpdateRun.Estado.ERROR,
        days_old=1,
    )
    stdout = StringIO()

    call_command(
        'depurar_actualizaciones_conocimiento',
        '--days',
        '90',
        '--execute',
        stdout=stdout,
    )

    report = json.loads(stdout.getvalue())
    assert report['protected_run_ids'] == sorted([
        old_success.pk,
        latest_error.pk,
    ])
    assert not KnowledgeUpdateRun.objects.filter(pk=older_error.pk).exists()
    assert KnowledgeUpdateRun.objects.filter(pk=old_success.pk).exists()


def test_depurar_rechaza_retencion_invalida():
    with pytest.raises(CommandError, match='mayor que cero'):
        call_command('depurar_actualizaciones_conocimiento', '--days', '0')
