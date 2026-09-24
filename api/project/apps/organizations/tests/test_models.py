import pytest
from django.db import IntegrityError

from organizations.models import Area, Organismo


@pytest.mark.django_db
def test_crear_organismo_y_area_demo():
    organismo = Organismo.objects.create(
        nombre='Organismo DEMO',
        descripcion='Entidad ficticia para pruebas.',
        url='https://demo.invalid/',
    )
    area = Area.objects.create(
        organismo=organismo,
        nombre='Área DEMO',
        descripcion='Área ficticia para pruebas.',
    )

    assert str(organismo) == 'Organismo DEMO'
    assert str(area) == 'Organismo DEMO: Área DEMO'
    assert organismo.areas.get() == area


@pytest.mark.django_db(transaction=True)
def test_nombre_de_area_es_unico_dentro_del_organismo():
    organismo = Organismo.objects.create(nombre='Organismo DEMO')
    Area.objects.create(organismo=organismo, nombre='Área DEMO')

    with pytest.raises(IntegrityError):
        Area.objects.create(organismo=organismo, nombre='Área DEMO')
