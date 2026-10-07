import pytest
from django.test import override_settings

from core.ai.llm import LLMRequestError, LLMResponse
from core.ai.service import LLMService, LLMUsageLimitError
from core.models import LLMDailyQuota, LLMRequestLog


class FakeLLMProvider:
    primary_model = 'principal:free'
    fallback_models = ('alternativo:free',)

    def __init__(self, failures=()):
        self.failures = set(failures)
        self.calls = []

    def ensure_ready(self, model):
        return None

    def generate(self, messages, *, model=None):
        self.calls.append(model)
        if model in self.failures:
            raise LLMRequestError('Falla recuperable DEMO', recoverable=True)
        return LLMResponse(
            text='Respuesta DEMO',
            model=model,
            input_tokens=12,
            output_tokens=4,
        )


@pytest.mark.django_db
def test_fallback_gratuito_registra_cada_intento():
    provider = FakeLLMProvider(failures={'principal:free'})

    response = LLMService(provider=provider).generate([
        {'role': 'user', 'content': 'Pregunta DEMO'},
    ])

    assert response.model == 'alternativo:free'
    assert provider.calls == ['principal:free', 'alternativo:free']
    assert LLMDailyQuota.objects.get().solicitudes == 2
    assert list(LLMRequestLog.objects.order_by('posicion_fallback').values_list(
        'estado', 'posicion_fallback'
    )) == [
        (LLMRequestLog.Estado.ERROR, 0),
        (LLMRequestLog.Estado.EXITOSA, 1),
    ]


@pytest.mark.django_db
def test_error_no_recuperable_no_activa_fallback():
    provider = FakeLLMProvider()

    def reject(messages, *, model=None):
        provider.calls.append(model)
        raise LLMRequestError('Solicitud inválida DEMO', recoverable=False)

    provider.generate = reject
    with pytest.raises(LLMRequestError, match='inválida'):
        LLMService(provider=provider).generate([
            {'role': 'user', 'content': 'Pregunta DEMO'},
        ])

    assert provider.calls == ['principal:free']
    assert LLMDailyQuota.objects.get().solicitudes == 1


@pytest.mark.django_db
@override_settings(MAX_DAILY_LLM_REQUESTS=1)
def test_limite_diario_bloquea_antes_de_segunda_llamada():
    provider = FakeLLMProvider()
    service = LLMService(provider=provider)
    service.generate([{'role': 'user', 'content': 'Primera'}])

    with pytest.raises(LLMUsageLimitError, match='límite diario'):
        service.generate([{'role': 'user', 'content': 'Segunda'}])

    assert provider.calls == ['principal:free']
    assert LLMDailyQuota.objects.get().solicitudes == 1
    assert LLMRequestLog.objects.filter(
        estado=LLMRequestLog.Estado.BLOQUEADA,
        codigo_error='daily_limit_exceeded',
    ).exists()


@pytest.mark.django_db
@override_settings(MAX_INPUT_TOKENS=10)
def test_limite_de_entrada_bloquea_sin_consumir_cupo():
    provider = FakeLLMProvider()

    with pytest.raises(LLMUsageLimitError, match='entrada'):
        LLMService(provider=provider).generate([
            {'role': 'user', 'content': 'Una entrada demasiado larga'},
        ])

    assert provider.calls == []
    assert LLMDailyQuota.objects.count() == 0
    assert LLMRequestLog.objects.get().codigo_error == 'input_token_limit_exceeded'
