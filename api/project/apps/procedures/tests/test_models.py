import pytest
from django.core.exceptions import ValidationError

from organizations.models import Area, Organismo
from procedures.models import Categoria, Plataforma, Servicio, Tramite


@pytest.fixture
def dominio_demo(db):
    organismo = Organismo.objects.create(nombre='Organismo DEMO')
    area = Area.objects.create(organismo=organismo, nombre='Área DEMO')
    categoria = Categoria.objects.create(nombre='Categoría DEMO', slug='categoria-demo')
    plataforma = Plataforma.objects.create(nombre='Plataforma DEMO')
    return organismo, area, categoria, plataforma


@pytest.mark.django_db
def test_crear_tramite_con_relaciones_normalizadas(dominio_demo):
    organismo, area, categoria, plataforma = dominio_demo
    tramite = Tramite.objects.create(
        nombre='Trámite DEMO',
        slug='tramite-demo',
        descripcion='Contenido exclusivamente ficticio.',
        organismo=organismo,
        area=area,
        categoria=categoria,
        plataforma=plataforma,
        modalidad=Tramite.Modalidad.ONLINE,
    )

    assert tramite.organismo == organismo
    assert tramite.area == area
    assert tramite.categoria == categoria
    assert tramite.plataforma == plataforma
    assert str(tramite) == 'Trámite DEMO'


@pytest.mark.django_db
def test_crear_servicio_de_pago_demo(dominio_demo):
    organismo, area, categoria, plataforma = dominio_demo
    servicio = Servicio.objects.create(
        nombre='Pago DEMO',
        slug='pago-demo',
        descripcion='Servicio ficticio sin medios de pago reales.',
        organismo=organismo,
        area=area,
        categoria=categoria,
        plataforma=plataforma,
        tipo=Servicio.Tipo.PAGO,
        impuesto='Impuesto DEMO',
    )

    assert servicio.tipo == Servicio.Tipo.PAGO
    assert servicio.medios_pago == ''


@pytest.mark.django_db
def test_rechazar_area_de_otro_organismo(dominio_demo):
    organismo, _, _, _ = dominio_demo
    otro_organismo = Organismo.objects.create(nombre='Otro organismo DEMO')
    otra_area = Area.objects.create(organismo=otro_organismo, nombre='Otra área DEMO')
    tramite = Tramite(
        nombre='Trámite inválido DEMO',
        slug='tramite-invalido-demo',
        descripcion='Prueba de validación.',
        organismo=organismo,
        area=otra_area,
    )

    with pytest.raises(ValidationError, match='El área debe pertenecer'):
        tramite.full_clean()


@pytest.mark.django_db
def test_metodo_de_autenticacion_exige_marca_correspondiente(dominio_demo):
    organismo, _, _, _ = dominio_demo
    tramite = Tramite(
        nombre='Autenticación DEMO',
        slug='autenticacion-demo',
        descripcion='Prueba de validación.',
        organismo=organismo,
        metodo_autenticacion='Método DEMO',
        autenticacion_requerida=False,
    )

    with pytest.raises(ValidationError, match='requiere autenticación'):
        tramite.full_clean()
