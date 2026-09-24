import pytest
from django.contrib.auth import get_user_model
from core.tests.fixtures import create_user, CONTENT_TYPE_JSON
from core.tests.utils import post, patch


@pytest.mark.django_db
def test_creacion_usuario_satisfactoria():
    endpoint = '/api/v1/usuario/registro/'
    data = {
        "data": {
            "type": "Usuario",
            "attributes": {
                "first_name": "David",
                "last_name": "Sanchez Motran",
                "password": "contraseña",
                "password_2": "contraseña",
                "email": "debianitram@gmail.com",
                "username": "debianitram"
            },
            "relationships": {
                "persona": {
                    "data": {
                        "nombre": "David",
                        "apellido": "Sanchez Motran",
                        "documento_identidad": "39935311",
                        "fecha_nacimiento": "1983-04-14",
                        "domicilio": "Domicilio",
                        "correo_electronico": "correo@electronico.com.ar",
                        "telefonos": []
                    }
                }
            }
        }
    }

    response = post(endpoint, data=data)
    assert response.status_code == 201
    data = response.json()['data']
    assert data['type'] == 'Usuario'
    assert data['id'] == '1'
    assert data['attributes']['username'] == 'debianitram'
    assert data['attributes']['email'] == 'debianitram@gmail.com'
    assert data['attributes']['first_name'] == 'David'
    assert data['attributes']['last_name'] == 'Sanchez Motran'

    usuario = get_user_model().objects.get(id=data['id'])
    assert usuario.is_active is False
'''

@pytest.mark.django_db
def test_creacion_usuario_falla_passwords_diferentes():
    endpoint = '/api/v1/usuario/registro/'
    data = {
        'data': {
            'type': 'Usuario',
            'attributes': {
                'first_name': 'Martín',
                'last_name': 'Miranda',
                'email': 'debianitram@gmail.com',
                'username': 'debianitram',
                'password': 'password_/123',
                'password_2': 'ContraseñaCompleja123',
            }
        }
    }

    response = post(endpoint, data=data)
    assert response.status_code == 400
    errors = response.json()['errors']
    assert errors[0]['detail'] == 'Las contraseñas ingresadas no coinciden.'
    assert errors[0]['source']['pointer'] == '/data/attributes/password'


@pytest.mark.django_db
def test_usuario_cambio_password_satisfactoriamente():
    usuario_autenticado = create_user(username='debianitram')
    usuario_autenticado.set_password('ultima_contraseña')

    data = {
        "clave": "ultima_contraseña",
        "clave_nueva": "nueva_contraseña",
        "clave_nueva_2": "nueva_contraseña"
    }

    endpoint = "/api/v1/usuario/cambiar-clave-secreta/"
    response = patch(endpoint, data=data, content_type=CONTENT_TYPE_JSON, user_logged=usuario_autenticado)

    assert response.status_code == 200

    debianitram = get_user_model().objects.get(username='debianitram')
    assert debianitram.check_password('nueva_contraseña')


@pytest.mark.django_db
def test_usuario_cambio_password_falla_con_clave():
    usuario_autenticado = create_user(username='debianitram')
    usuario_autenticado.set_password('ultima_contraseña')

    data = {
        "clave": "ultima.-.",
        "clave_nueva": "nueva_contraseña",
        "clave_nueva_2": "nueva_contraseña"
    }

    endpoint = "/api/v1/usuario/cambiar-clave-secreta/"
    response = patch(endpoint, data=data, content_type=CONTENT_TYPE_JSON, user_logged=usuario_autenticado)

    assert response.status_code == 400
    errors = response.json()['errors']
    assert errors[0]['detail'] == 'La contraseña anterior no es válida. ¡Intentalo nuevamente!'


@pytest.mark.django_db
def test_usuario_cambio_password_falla_no_coinciden_nuevas_password():
    usuario_autenticado = create_user(username='debianitram')
    usuario_autenticado.set_password('ultima_contraseña')

    data = {
        "clave": "ultima_contraseña",
        "clave_nueva": "NuevaContraseña",
        "clave_nueva_2": "nueva_contraseña"
    }

    endpoint = "/api/v1/usuario/cambiar-clave-secreta/"
    response = patch(endpoint, data=data, content_type=CONTENT_TYPE_JSON, user_logged=usuario_autenticado)

    assert response.status_code == 400
    errors = response.json()['errors']
    assert errors[0]['detail'] == 'Los nuevos campos de contraseñas no coinciden'


@pytest.mark.django_db
def test_usuario_cambio_password_falla_password_demasiado_corta_y_comun():
    usuario_autenticado = create_user(username='debianitram')
    usuario_autenticado.set_password('ultima_contraseña')

    data = {
        "clave": "ultima_contraseña",
        "clave_nueva": "admin",
        "clave_nueva_2": "admin"
    }

    endpoint = "/api/v1/usuario/cambiar-clave-secreta/"
    response = patch(endpoint, data=data, content_type=CONTENT_TYPE_JSON, user_logged=usuario_autenticado)

    assert response.status_code == 400
    errors = response.json()['errors']
    assert len(errors) == 3
    codigos_errors = [error['code'] for error in errors]
    assert 'password_too_similar' in codigos_errors
    assert 'password_too_short' in codigos_errors
    assert 'password_too_common' in codigos_errors
'''