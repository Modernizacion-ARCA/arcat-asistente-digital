import environ
import pytest
from django.test import override_settings

from core.ai.embeddings import LocalEmbeddingProvider, get_embedding_provider
from core.ai.llm import (
    MissingLLMCredentialsError,
    OpenRouterProvider,
    PaidModelNotAllowedError,
)
from project.settings.ai import load_ai_settings


def test_carga_y_parsea_configuracion_ai(monkeypatch):
    values = {
        'OPENROUTER_PRIMARY_MODEL': 'proveedor/modelo:free',
        'OPENROUTER_FALLBACK_MODELS': 'uno:free,dos:free',
        'ALLOW_PAID_MODELS': 'true',
        'MAX_DAILY_LLM_REQUESTS': '25',
        'MAX_INPUT_TOKENS': '4000',
        'MAX_OUTPUT_TOKENS': '700',
        'EMBEDDING_PROVIDER': 'local',
        'EMBEDDING_MODEL': 'modelo-local-demo',
        'EMBEDDING_DIMENSION': '3',
        'RAG_CHUNK_SIZE': '120',
        'RAG_CHUNK_OVERLAP': '20',
        'RAG_TOP_K': '4',
    }
    for name, value in values.items():
        monkeypatch.setenv(name, value)

    config = load_ai_settings(environ.Env())

    assert config.allow_paid_models is True
    assert config.max_daily_llm_requests == 25
    assert config.max_input_tokens == 4000
    assert config.max_output_tokens == 700
    assert config.openrouter_primary_model == 'proveedor/modelo:free'
    assert config.openrouter_fallback_models == ('uno:free', 'dos:free')
    assert config.embedding_model == 'modelo-local-demo'
    assert config.embedding_dimension == 3
    assert config.rag_chunk_size == 120
    assert config.rag_chunk_overlap == 20
    assert config.rag_top_k == 4


def test_rechaza_overlap_invalido(monkeypatch):
    monkeypatch.setenv('RAG_CHUNK_SIZE', '100')
    monkeypatch.setenv('RAG_CHUNK_OVERLAP', '100')

    with pytest.raises(ValueError, match='RAG_CHUNK_OVERLAP'):
        load_ai_settings(environ.Env())


def test_local_embedding_provider_usa_modelo_configurado():
    class FakeModel:
        def encode(self, texts, **kwargs):
            assert texts == ['uno', 'dos']
            assert kwargs['normalize_embeddings'] is True
            return [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]

    factory_calls = []

    def factory(model_name):
        factory_calls.append(model_name)
        return FakeModel()

    provider = LocalEmbeddingProvider(
        model_name='modelo-local-demo',
        dimension=3,
        model_factory=factory,
    )

    assert provider.embed(['uno', 'dos']) == [
        [0.1, 0.2, 0.3],
        [0.4, 0.5, 0.6],
    ]
    assert factory_calls == ['modelo-local-demo']


@override_settings(EMBEDDING_PROVIDER='local')
def test_factory_de_embeddings_no_utiliza_openrouter():
    assert isinstance(get_embedding_provider(), LocalEmbeddingProvider)


def test_rechaza_modelo_pago_cuando_no_esta_permitido():
    with pytest.raises(PaidModelNotAllowedError, match='ALLOW_PAID_MODELS=false'):
        OpenRouterProvider(
            api_key='',
            primary_model='proveedor/modelo-pago',
            allow_paid_models=False,
        )


def test_falta_de_api_key_solo_falla_al_generar():
    provider = OpenRouterProvider(
        api_key='',
        primary_model='openrouter/free',
        allow_paid_models=False,
    )

    with pytest.raises(MissingLLMCredentialsError, match='OPENROUTER_API_KEY'):
        provider.generate([{'role': 'user', 'content': 'Consulta DEMO'}])


def test_fallback_pago_tambien_es_rechazado():
    with pytest.raises(PaidModelNotAllowedError, match='modelo-pago'):
        OpenRouterProvider(
            api_key='',
            primary_model='openrouter/free',
            fallback_models=('proveedor/modelo-pago',),
            allow_paid_models=False,
        )
