import pytest
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.urls import reverse

from organizations.admin import AreaAdmin, OrganismoAdmin
from organizations.models import Area, Organismo
from procedures.admin import (
    CategoriaAdmin,
    PlataformaAdmin,
    ServicioAdmin,
    TramiteAdmin,
)
from procedures.models import Categoria, Plataforma, Servicio, Tramite
from sources.admin import DocumentChunkAdmin, DocumentoAdmin, FuenteAdmin
from sources.models import DocumentChunk, Documento, Fuente


@pytest.mark.parametrize(
    ('model', 'admin_class'),
    (
        (Organismo, OrganismoAdmin),
        (Area, AreaAdmin),
        (Categoria, CategoriaAdmin),
        (Plataforma, PlataformaAdmin),
        (Tramite, TramiteAdmin),
        (Servicio, ServicioAdmin),
        (Fuente, FuenteAdmin),
        (Documento, DocumentoAdmin),
        (DocumentChunk, DocumentChunkAdmin),
    ),
)
def test_modelos_del_dominio_estan_registrados(model, admin_class):
    assert isinstance(admin.site._registry[model], admin_class)


@pytest.fixture
def admin_client(client, db):
    usuario = get_user_model().objects.create_superuser(
        username='admin-demo',
        email='admin@demo.invalid',
        password='clave-demo',
    )
    client.force_login(usuario)
    return client


@pytest.mark.parametrize(
    'model',
    (Organismo, Area, Categoria, Plataforma, Tramite, Servicio, Fuente, Documento),
)
def test_listados_del_dominio_son_accesibles(admin_client, model):
    url = reverse(
        f'admin:{model._meta.app_label}_{model._meta.model_name}_changelist'
    )

    response = admin_client.get(url)

    assert response.status_code == 200


@pytest.mark.parametrize('model', (Tramite, Servicio, Documento))
def test_formularios_principales_son_accesibles(admin_client, model):
    url = reverse(f'admin:{model._meta.app_label}_{model._meta.model_name}_add')

    response = admin_client.get(url)

    assert response.status_code == 200
