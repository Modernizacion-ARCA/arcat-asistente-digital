import pytest

from rest_framework.test import APIClient

from core.tests.utils import post, get
from core.tests.fixtures import get_default_test_user


@pytest.mark.django_db
def test_obtener_perfil_usuario(get_default_test_user):
    response = get("/api/v1/usuario/me/", user_logged=get_default_test_user)
    assert response.status_code == 200
    data = response.json()['data']

    assert data['type'] == 'Usuario'
    assert data['attributes']['first_name'] == 'Test'
    assert data['attributes']['last_name'] == 'User'


