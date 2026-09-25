import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.conf import settings


class LLMProviderError(Exception):
    """Base error exposed by an LLM provider."""


class MissingLLMCredentialsError(LLMProviderError):
    """Raised only when an operation requires an absent API key."""


class PaidModelNotAllowedError(LLMProviderError):
    """Raised before a paid or unclassified model can be requested."""


class LLMRequestError(LLMProviderError):
    """Raised when the remote provider cannot complete a request."""


@dataclass(frozen=True)
class LLMResponse:
    text: str
    model: str
    input_tokens: int | None = None
    output_tokens: int | None = None


class LLMProvider(ABC):
    @abstractmethod
    def generate(self, messages, *, model=None):
        """Generate a response from a bounded sequence of chat messages."""


def is_explicitly_free_model(model):
    return model == 'openrouter/free' or model.endswith(':free')


class OpenRouterProvider(LLMProvider):
    def __init__(
        self,
        *,
        api_key=None,
        base_url=None,
        primary_model=None,
        fallback_models=None,
        allow_paid_models=None,
        transport=None,
    ):
        self.api_key = settings.OPENROUTER_API_KEY if api_key is None else api_key
        self.base_url = (base_url or settings.OPENROUTER_BASE_URL).rstrip('/')
        self.primary_model = primary_model or settings.OPENROUTER_PRIMARY_MODEL
        self.fallback_models = tuple(
            settings.OPENROUTER_FALLBACK_MODELS
            if fallback_models is None else fallback_models
        )
        self.allow_paid_models = (
            settings.ALLOW_PAID_MODELS
            if allow_paid_models is None else allow_paid_models
        )
        self.transport = transport or self._urlopen_transport
        self._validate_models((self.primary_model, *self.fallback_models))

    def _validate_models(self, models):
        if self.allow_paid_models:
            return
        rejected = [model for model in models if not is_explicitly_free_model(model)]
        if rejected:
            raise PaidModelNotAllowedError(
                'ALLOW_PAID_MODELS=false: sólo se permiten openrouter/free o '
                'identificadores terminados en :free. Modelos rechazados: '
                + ', '.join(rejected)
            )

    @staticmethod
    def _urlopen_transport(request, timeout):
        try:
            with urlopen(request, timeout=timeout) as response:
                return json.loads(response.read().decode('utf-8'))
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise LLMRequestError('OpenRouter no pudo completar la solicitud.') from exc

    def generate(self, messages, *, model=None):
        if not self.api_key:
            raise MissingLLMCredentialsError(
                'OPENROUTER_API_KEY no está configurada para esta operación.'
            )
        selected_model = model or self.primary_model
        self._validate_models((selected_model,))
        body = json.dumps({
            'model': selected_model,
            'messages': list(messages),
            'max_tokens': settings.MAX_OUTPUT_TOKENS,
        }).encode('utf-8')
        request = Request(
            f'{self.base_url}/chat/completions',
            data=body,
            headers={
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json',
            },
            method='POST',
        )
        payload = self.transport(request, 30)
        try:
            choice = payload['choices'][0]
            usage = payload.get('usage', {})
            return LLMResponse(
                text=choice['message']['content'],
                model=payload.get('model', selected_model),
                input_tokens=usage.get('prompt_tokens'),
                output_tokens=usage.get('completion_tokens'),
            )
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMRequestError('OpenRouter devolvió una respuesta inválida.') from exc


def get_llm_provider():
    return OpenRouterProvider()
