import hashlib
import hmac

from django.conf import settings
from redis.exceptions import RedisError
from rest_framework.exceptions import APIException
from rest_framework.throttling import SimpleRateThrottle


class ThrottleInfrastructureUnavailable(APIException):
    status_code = 503
    default_detail = 'El asistente no está disponible temporalmente.'
    default_code = 'throttle_unavailable'


class HashedRAGThrottle(SimpleRateThrottle):
    """Rate-limit public questions without storing a raw session or IP address."""

    scope = 'rag_anon'

    def get_rate(self):
        # Read the current Django setting rather than DRF's import-time snapshot. This
        # also makes override_settings effective in tests and runtime configuration.
        return settings.REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'][self.scope]

    def allow_request(self, request, view):
        try:
            return super().allow_request(request, view)
        except RedisError as exc:
            # Fail closed: never bypass public throttling when the shared cache is down.
            raise ThrottleInfrastructureUnavailable() from exc

    def get_cache_key(self, request, view):
        session_key = getattr(request.session, 'session_key', None)
        identity = session_key or self.get_ident(request)
        if not identity:
            return None
        digest = hmac.new(
            settings.SECRET_KEY.encode('utf-8'),
            identity.encode('utf-8'),
            hashlib.sha256,
        ).hexdigest()
        return self.cache_format % {'scope': self.scope, 'ident': digest}
