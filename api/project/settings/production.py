from .base import *  # noqa: F403
from .base import env
from django.core.exceptions import ImproperlyConfigured


DEBUG = False
SECURE_SSL_REDIRECT = env.bool('DJANGO_SECURE_SSL_REDIRECT', default=True)  # noqa: F405
SESSION_COOKIE_SECURE = env.bool('DJANGO_SESSION_COOKIE_SECURE', default=True)  # noqa: F405
CSRF_COOKIE_SECURE = env.bool('DJANGO_CSRF_COOKIE_SECURE', default=True)  # noqa: F405
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

if not CACHE_URL:  # noqa: F405
    raise ImproperlyConfigured(
        'DJANGO_CACHE_URL es obligatorio en producción para rate limiting distribuido.'
    )
