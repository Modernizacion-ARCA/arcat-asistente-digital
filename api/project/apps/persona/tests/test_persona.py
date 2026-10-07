import pytest

from core.tests.fixtures import get_default_test_user
from core.tests.utils import post
from persona.models import Persona
from util.models import Mail, Telefono


@pytest.mark.django_db
def test_creacion_persona_satisfactorio(get_default_test_user):
    endpoint = '/api/v1/persona/'

    data = {
        "data": {
            "type": "Persona",
            "attributes": {
                "nombre": "Zurita",
                "apellido": "Franco",
                "documento_identidad": "1020305",
                "fecha_nacimiento": "2017-03-11",
                "domicilio": "La Chacarita",
                "correo_electronico": "fz@fzurita.com",
                'telefonos': [{'tipo': 'telefono', 'numero': '3834904560'}]
            }
        }
    }

    response = post(endpoint, data=data, user_logged=get_default_test_user)
    assert response.status_code == 201
    persona = Persona.objects.get(documento_identidad='1020305')
    assert Mail.objects.get(object_id=persona.pk).contact_point == 'fz@fzurita.com'
    telefono = Telefono.objects.get(object_id=persona.pk)
    assert telefono.type == Telefono.TELEFONO_FIJO
    assert telefono.contact_point == '3834904560'
