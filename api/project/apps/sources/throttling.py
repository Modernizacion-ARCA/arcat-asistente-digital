import hashlib
import hmac

from django.conf import settings
from rest_framework.throttling import SimpleRateThrottle


class HashedRAGThrottle(SimpleRateThrottle):
    """Rate-limit public questions without storing a raw session or IP address."""

    scope = 'rag_anon'

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
