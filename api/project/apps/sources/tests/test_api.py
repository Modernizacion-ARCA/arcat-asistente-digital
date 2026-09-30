from types import SimpleNamespace

import pytest
from django.core.cache import cache
from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from core.ai.llm import MissingLLMCredentialsError
from sources.rag import RAGAnswer


@pytest.fixture(autouse=True)
def clear_throttle_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def api_client():
    return APIClient()


def test_consulta_publica_valida_y_serializa_evidencias(api_client, mocker):
    answer = RAGAnswer(
        answer='Respuesta oficial [1]',
        evidence=(SimpleNamespace(
            chunk_id=4,
            document_title='Guía oficial',
            source_name='ARCAT',
            url='https://example.gov/guia',
        ),),
        model='modelo:free',
    )
    service = mocker.patch('sources.api.RAGService').return_value
    service.answer.return_value = answer

    response = api_client.post(
        reverse('rag_consultar'),
        {'pregunta': '¿Cómo realizo el trámite?', 'organismo_id': 2},
        format='json',
    )

    assert response.status_code == 200
    assert response.data == {
        'respuesta': 'Respuesta oficial [1]',
        'evidencias': [{
            'fragmento_id': 4,
            'documento': 'Guía oficial',
            'fuente': 'ARCAT',
            'url': 'https://example.gov/guia',
        }],
        'modelo': 'modelo:free',
    }
    filters = service.answer.call_args.kwargs['filters']
    assert filters.organismo_id == 2
    assert filters.origen_informacion == 'OFICIAL'


@pytest.mark.parametrize('payload', ({}, {'pregunta': ''}, {'pregunta': '   '}))
def test_consulta_rechaza_pregunta_vacia(api_client, payload):
    response = api_client.post(reverse('rag_consultar'), payload, format='json')

    assert response.status_code == 400


def test_error_del_proveedor_se_sanitiza(api_client, mocker):
    service = mocker.patch('sources.api.RAGService').return_value
    service.answer.side_effect = MissingLLMCredentialsError('detalle interno sensible')

    response = api_client.post(
        reverse('rag_consultar'),
        {'pregunta': 'Pregunta válida'},
        format='json',
    )

    assert response.status_code == 503
    assert response.data['code'] == 'assistant_unavailable'
    assert 'sensible' not in response.data['detail']


def test_throttle_publico_limita_por_identidad_anonima(api_client, mocker, settings):
    service = mocker.patch('sources.api.RAGService').return_value
    service.answer.return_value = RAGAnswer(
        answer='Respuesta', evidence=(), model=None
    )
    url = reverse('rag_consultar')

    rest_framework_settings = {
        **settings.REST_FRAMEWORK,
        'DEFAULT_THROTTLE_RATES': {'rag_anon': '1/hour'},
    }
    with override_settings(REST_FRAMEWORK=rest_framework_settings):
        first = api_client.post(url, {'pregunta': 'Primera'}, format='json')
        second = api_client.post(url, {'pregunta': 'Segunda'}, format='json')

    assert first.status_code == 200
    assert second.status_code == 429
    assert service.answer.call_count == 1
