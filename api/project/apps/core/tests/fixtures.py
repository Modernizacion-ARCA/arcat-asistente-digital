import json

import pytest

from django.contrib.auth import get_user_model
from oauth2_provider.models import get_application_model
from rest_framework.test import APIClient

User = get_user_model()

CONTENT_TYPE_JSON = 'application/json'


def create_user(username, first_name='Admin', last_name='Root', email=None, *, is_active=True):
    user, created = User.objects.get_or_create(
        username=username,
        email='{}@root.com'.format(username) if email is None else email,
        defaults=dict(
            first_name=first_name,
            last_name=last_name,
            password='password',
            is_active=is_active
        )
    )

    return user


@pytest.fixture
def get_default_test_user():
    test_user = create_user(username='test_user', first_name='Test', last_name='User', email='tests@user')
    return test_user


def get_client_application():
    Application = get_application_model()
    application, _ = Application.objects.get_or_create(
        name='TestApp',
        client_type=Application.CLIENT_CONFIDENTIAL,
        authorization_grant_type=Application.GRANT_CLIENT_CREDENTIALS,
        skip_authorization=True
    )

    return application


def client_authorized():
    app = get_client_application()
    client = APIClient()
    r = client.post('/oauth2/token/', {
        'grant_type': 'client_credentials',
        'client_id': app.client_id,
        'client_secret': app.client_secret
    })
    response = json.loads(r.content)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION='Bearer ' + response['access_token'])
    return client
