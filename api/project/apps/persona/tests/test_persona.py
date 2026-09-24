import pytest

from core.tests.fixtures import get_default_test_user
from core.tests.utils import post


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
