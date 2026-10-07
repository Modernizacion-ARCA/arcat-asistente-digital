import time

from django.conf import settings
from django.db.models import F
from django.utils import timezone

from core.models import LLMDailyQuota, LLMRequestLog

from .llm import LLMRequestError, get_llm_provider


class LLMUsageLimitError(Exception):
    """Raised before a request that would exceed an application limit."""


def conservative_token_estimate(messages):
    """Use UTF-8 bytes as a safe upper bound for common BPE tokenizers."""
    return sum(
        len(str(message.get('role', '')).encode('utf-8'))
        + len(str(message.get('content', '')).encode('utf-8'))
        + 16  # Conservative allowance for chat framing added by the provider.
        for message in messages
    )


class LLMService:
    def __init__(self, provider=None):
        self.provider = provider or get_llm_provider()

    def _reserve_request(self, model, fallback_position):
        today = timezone.localdate()
        quota, _ = LLMDailyQuota.objects.get_or_create(fecha=today)
        reserved = LLMDailyQuota.objects.filter(
            pk=quota.pk,
            solicitudes__lt=settings.MAX_DAILY_LLM_REQUESTS,
        ).update(solicitudes=F('solicitudes') + 1)
        if not reserved:
            LLMRequestLog.objects.create(
                proveedor='openrouter',
                modelo=model,
                estado=LLMRequestLog.Estado.BLOQUEADA,
                posicion_fallback=fallback_position,
                codigo_error='daily_limit_exceeded',
            )
            raise LLMUsageLimitError(
                'Se alcanzó el límite diario de solicitudes al LLM.'
            )

    def generate(self, messages):
        messages = list(messages)
        estimated_tokens = conservative_token_estimate(messages)
        if estimated_tokens > settings.MAX_INPUT_TOKENS:
            LLMRequestLog.objects.create(
                proveedor='openrouter',
                modelo=self.provider.primary_model,
                estado=LLMRequestLog.Estado.BLOQUEADA,
                codigo_error='input_token_limit_exceeded',
                tokens_entrada=estimated_tokens,
            )
            raise LLMUsageLimitError(
                'La entrada supera el límite de tokens configurado.'
            )

        models = (self.provider.primary_model, *self.provider.fallback_models)
        last_error = None
        for position, model in enumerate(models):
            self.provider.ensure_ready(model)
            self._reserve_request(model, position)
            started = time.monotonic()
            try:
                response = self.provider.generate(messages, model=model)
            except LLMRequestError as exc:
                last_error = exc
                LLMRequestLog.objects.create(
                    proveedor='openrouter',
                    modelo=model,
                    estado=LLMRequestLog.Estado.ERROR,
                    posicion_fallback=position,
                    duracion_ms=int((time.monotonic() - started) * 1000),
                    codigo_error=type(exc).__name__,
                    tokens_entrada=estimated_tokens,
                )
                if not exc.recoverable:
                    raise
                continue

            LLMRequestLog.objects.create(
                proveedor='openrouter',
                modelo=response.model,
                estado=LLMRequestLog.Estado.EXITOSA,
                posicion_fallback=position,
                duracion_ms=int((time.monotonic() - started) * 1000),
                tokens_entrada=response.input_tokens or estimated_tokens,
                tokens_salida=response.output_tokens,
            )
            return response
        raise last_error or LLMRequestError('No hay modelos LLM configurados.')
