from .base import *


SECRET_KEY = 'CHANGEME!!!'
DEBUG = False

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

MEDIA_ROOT = str(PROJECT_DIR.path('test_media'))

# OAUTH2_PROVIDER_ACCESS_TOKEN_MODEL = 'oauth2_provider.AccessToken'
# OAUTH2_PROVIDER_APPLICATION_MODEL = 'oauth2_provider.Application'
# OAUTH2_PROVIDER_GRANT_MODEL = 'oauth2_provider.Grant'
# OAUTH2_PROVIDER_REFRESH_TOKEN_MODEL = 'oauth2_provider.RefreshToken'

OAUTH2_PROVIDER = {
    # this is the list of available scopes
    'SCOPES': ['read', 'write', 'groups']
}


