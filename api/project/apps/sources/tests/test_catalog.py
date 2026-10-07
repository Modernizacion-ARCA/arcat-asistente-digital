import json
from io import StringIO
from pathlib import Path

import pytest
from django.conf import settings
from django.core.management import call_command
from django.core.management.base import CommandError

from sources.catalog import CatalogValidationError, load_catalog
from sources.models import Documento, Fuente
from procedures.models import Tramite


CATALOG_DIR = Path(str(settings.ROOT_DIR)) / 'data/catalogs'
CANDIDATE_PATH = CATALOG_DIR / 'arcat-tramites-candidatos-v1.json'
CATALOG_PATH = CATALOG_DIR / 'arcat-tramites-revisados-v2.json'


def test_catalogo_candidato_original_se_conserva_pendiente():
    catalog = load_catalog(CANDIDATE_PATH)

    assert catalog.verification_status == 'PENDING_SOURCE_VERIFICATION'
    assert catalog.reviewed_at is None
    assert len(catalog.records) == 10


def test_catalogo_revisado_es_valido_y_espera_aprobacion_institucional():
    catalog = load_catalog(CATALOG_PATH)

    assert catalog.name == 'Catálogo revisado de trámites ARCAT'
    assert catalog.verification_status == 'PENDING_INSTITUTIONAL_APPROVAL'
    assert catalog.reviewed_at == '2026-10-07'
    assert len(catalog.records) == 10
    assert len({record['id'] for record in catalog.records}) == 10
    assert all(record['organismo'] == 'ARCAT' for record in catalog.records)
    assert all(record['source_review']['evidence_urls'] for record in catalog.records)


def test_catalogo_rechaza_fuente_fuera_de_allowlist(tmp_path):
    path = tmp_path / 'catalog.json'
    path.write_text(json.dumps({
        'name': 'Catálogo DEMO',
        'schema_version': 1,
        'verification_status': 'PENDING_SOURCE_VERIFICATION',
        'source_urls': ['https://sitio-no-oficial.invalid/'],
        'records': [{}],
    }), encoding='utf-8')

    with pytest.raises(CatalogValidationError, match='URL no permitida'):
        load_catalog(path)


def test_comando_informa_estado_y_cantidad():
    output = StringIO()

    call_command('validar_catalogo_arcat', archivo=CATALOG_PATH, stdout=output)

    summary = json.loads(output.getvalue())
    assert summary['records'] == 10
    assert summary['verification_status'] == 'PENDING_INSTITUTIONAL_APPROVAL'
    assert summary['reviewed_at'] == '2026-10-07'


def test_comando_impide_tratar_borrador_como_verificado():
    with pytest.raises(CommandError, match='verificación manual'):
        call_command(
            'validar_catalogo_arcat',
            archivo=CATALOG_PATH,
            require_verified=True,
        )


def test_carga_demo_exige_confirmacion():
    with pytest.raises(CommandError, match='--confirm-demo'):
        call_command('cargar_catalogo_demo', archivo=CATALOG_PATH)


@pytest.mark.django_db
def test_carga_demo_es_aislada_e_idempotente():
    first_output = StringIO()
    second_output = StringIO()

    call_command(
        'cargar_catalogo_demo',
        archivo=CATALOG_PATH,
        confirm_demo=True,
        stdout=first_output,
    )
    call_command(
        'cargar_catalogo_demo',
        archivo=CATALOG_PATH,
        confirm_demo=True,
        stdout=second_output,
    )

    assert json.loads(first_output.getvalue())['created_procedures'] == 10
    assert json.loads(second_output.getvalue())['updated_procedures'] == 10
    assert Tramite.objects.filter(slug__startswith='demo-tad-arcat-').count() == 10
    assert not Tramite.objects.filter(
        slug__startswith='demo-tad-arcat-', activo=True
    ).exists()
    assert Documento.objects.filter(fuente__origen_informacion='DEMO').count() == 10
    source = Fuente.objects.get(url__startswith='https://demo.invalid/catalog/')
    assert source.origen_informacion == Fuente.OrigenInformacion.DEMO
    assert source.metadata['source_verification_status'] == (
        'PENDING_INSTITUTIONAL_APPROVAL'
    )


def test_catalogo_revisado_exige_evidencia_por_registro(tmp_path):
    payload = json.loads(CATALOG_PATH.read_text(encoding='utf-8'))
    del payload['records'][0]['source_review']['evidence_urls']
    path = tmp_path / 'sin-evidencia.json'
    path.write_text(json.dumps(payload), encoding='utf-8')

    with pytest.raises(CatalogValidationError, match='evidence_urls'):
        load_catalog(path)


def test_catalogo_no_se_promueve_solo_cambiando_el_estado(tmp_path):
    payload = json.loads(CATALOG_PATH.read_text(encoding='utf-8'))
    payload['verification_status'] = 'VERIFIED'
    path = tmp_path / 'sin-aprobacion.json'
    path.write_text(json.dumps(payload), encoding='utf-8')

    with pytest.raises(CatalogValidationError, match='institutional_approval'):
        load_catalog(path)
